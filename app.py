import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Question, Student, StudentAnswer, PrerequisiteVideo
from gemini_service import generate_questions_from_ai
from analytics import calculate_analytics
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Admin credentials from environment
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# List of prerequisites for the assessment
PREREQUISITES = [
    "جمع و تفریق اعداد طبیعی",
    "ضرب و تقسیم اعداد طبیعی",  
    "کسرها و اعمال روی کسرها",
    "اعشار و تبدیل کسر به اعشار",
    "درصد و کاربردهای آن"
]

def create_tables():
    """Initialize database tables and sample data"""
    db.create_all()
    
    # Add sample video links if not exist
    if not PrerequisiteVideo.query.first():
        sample_videos = [
            ("جمع و تفریق اعداد طبیعی", "https://example.com/video1"),
            ("ضرب و تقسیم اعداد طبیعی", "https://example.com/video2"),
            ("کسرها و اعمال روی کسرها", "https://example.com/video3"),
            ("اعشار و تبدیل کسر به اعشار", "https://example.com/video4"),
            ("درصد و کاربردهای آن", "https://example.com/video5")
        ]
        
        for name, url in sample_videos:
            video = PrerequisiteVideo(prerequisite_name=name, video_url=url)
            db.session.add(video)
        
        db.session.commit()

# Initialize database tables and sample data
with app.app_context():
    create_tables()

# Student Routes
@app.route('/')
def index():
    """Main assessment page for students"""
    return render_template('index.html')

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Start a new student assessment session"""
    try:
        data = request.get_json()
        student_name = data.get('name', '').strip()
        student_grade = data.get('grade', '').strip()
        
        if not student_name or not student_grade:
            return jsonify({'success': False, 'error': 'نام و پایه تحصیلی الزامی است'})
        
        # Create new student record
        student = Student(
            student_name=student_name,
            student_grade=student_grade,
            session_start_time=str(db.func.current_timestamp())
        )
        db.session.add(student)
        db.session.commit()
        
        # Store session data
        session['student_id'] = student.id
        session['current_prerequisite_index'] = 0
        session['score'] = 0
        session['total_questions'] = 0
        
        return jsonify({'success': True, 'student_id': student.id})
        
    except Exception as e:
        logging.error(f"Error starting session: {e}")
        return jsonify({'success': False, 'error': 'خطا در شروع جلسه'})

@app.route('/api/get_question', methods=['GET'])
def get_question():
    """Get next question for student"""
    try:
        if 'student_id' not in session:
            return jsonify({'success': False, 'error': 'جلسه یافت نشد'})
        
        prerequisite_index = session.get('current_prerequisite_index', 0)
        
        # Check if assessment is complete
        if prerequisite_index >= len(PREREQUISITES):
            return jsonify({
                'success': True, 
                'completed': True,
                'score': session.get('score', 0),
                'total': session.get('total_questions', 0)
            })
        
        prerequisite = PREREQUISITES[prerequisite_index]
        
        # Try to get existing question with best discrimination index
        question = Question.query.filter_by(prerequisite_name=prerequisite)\
                                 .order_by(Question.avg_discrimination_index.desc().nullslast(),
                                          Question.times_used.asc())\
                                 .first()
        
        # If no question exists, generate new ones
        if not question:
            logging.info(f"Generating new questions for: {prerequisite}")
            success = generate_questions_from_ai(prerequisite)
            if success:
                question = Question.query.filter_by(prerequisite_name=prerequisite).first()
        
        if not question:
            return jsonify({'success': False, 'error': 'خطا در تولید سوال'})
        
        # Update usage count
        question.times_used += 1
        db.session.commit()
        
        # Store current question in session
        session['current_question_id'] = question.id
        session['total_questions'] = session.get('total_questions', 0) + 1
        
        return jsonify({
            'success': True,
            'question': {
                'id': question.id,
                'text': question.question_text,
                'prerequisite': question.prerequisite_name
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting question: {e}")
        return jsonify({'success': False, 'error': 'خطا در دریافت سوال'})

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """Submit student answer"""
    try:
        if 'student_id' not in session or 'current_question_id' not in session:
            return jsonify({'success': False, 'error': 'جلسه یافت نشد'})
        
        data = request.get_json()
        answer = data.get('answer', '').strip()
        
        student_id = session['student_id']
        question_id = session['current_question_id']
        
        # Get question
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'success': False, 'error': 'سوال یافت نشد'})
        
        # Check if answer is correct
        is_correct = answer.lower() == question.correct_answer.lower()
        
        # Save student answer
        student_answer = StudentAnswer(
            student_id=student_id,
            question_id=question_id,
            is_correct=1 if is_correct else 0
        )
        db.session.add(student_answer)
        db.session.commit()
        
        # Update session score
        if is_correct:
            session['score'] = session.get('score', 0) + 1
        
        # Move to next prerequisite
        session['current_prerequisite_index'] = session.get('current_prerequisite_index', 0) + 1
        
        return jsonify({
            'success': True,
            'correct': is_correct,
            'correct_answer': question.correct_answer
        })
        
    except Exception as e:
        logging.error(f"Error submitting answer: {e}")
        return jsonify({'success': False, 'error': 'خطا در ثبت پاسخ'})

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

def admin_required(f):
    """Decorator to require admin login"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard showing student results"""
    students = Student.query.all()
    
    # Calculate stats for each student
    student_stats = []
    for student in students:
        answers = StudentAnswer.query.filter_by(student_id=student.id).all()
        total_answers = len(answers)
        correct_answers = sum(1 for a in answers if a.is_correct)
        percentage = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        
        student_stats.append({
            'id': student.id,
            'name': student.student_name,
            'grade': student.student_grade,
            'start_time': student.session_start_time,
            'total_questions': total_answers,
            'correct_answers': correct_answers,
            'percentage': round(percentage, 1)
        })
    
    return render_template('admin/dashboard.html', students=student_stats)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page showing question analysis"""
    # Update analytics before showing
    calculate_analytics()
    
    questions = Question.query.all()
    
    # Prepare questions data with analytics
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'prerequisite_name': q.prerequisite_name,
            'difficulty_level': q.difficulty_level,
            'question_text': q.question_text[:100] + '...' if len(q.question_text) > 100 else q.question_text,
            'correct_answer': q.correct_answer,
            'times_used': q.times_used,
            'avg_difficulty_percent': round(q.avg_difficulty_percent or 0, 1),
            'avg_discrimination_index': round(q.avg_discrimination_index or 0, 3)
        })
    
    return render_template('admin/analytics.html', questions=questions_data)

@app.route('/admin/videos', methods=['GET', 'POST'])
@admin_required
def admin_videos():
    """Admin page for managing educational videos"""
    if request.method == 'POST':
        prerequisite_name = request.form.get('prerequisite_name')
        video_url = request.form.get('video_url')
        
        if prerequisite_name and video_url:
            # Check if video already exists
            video = PrerequisiteVideo.query.filter_by(prerequisite_name=prerequisite_name).first()
            if video:
                video.video_url = video_url
            else:
                video = PrerequisiteVideo(prerequisite_name=prerequisite_name, video_url=video_url)
                db.session.add(video)
            
            db.session.commit()
            flash('ویدیو با موفقیت ذخیره شد', 'success')
        else:
            flash('لطفا تمام فیلدها را پر کنید', 'error')
    
    videos = PrerequisiteVideo.query.all()
    return render_template('admin/videos.html', videos=videos, prerequisites=PREREQUISITES)

@app.route('/admin/generate_questions', methods=['POST'])
@admin_required
def admin_generate_questions():
    """Manually generate questions for a prerequisite"""
    try:
        data = request.get_json()
        prerequisite = data.get('prerequisite')
        
        if not prerequisite:
            return jsonify({'success': False, 'error': 'پیش‌نیاز مشخص نشده'})
        
        success = generate_questions_from_ai(prerequisite)
        
        if success:
            return jsonify({'success': True, 'message': 'سوالات با موفقیت تولید شدند'})
        else:
            return jsonify({'success': False, 'error': 'خطا در تولید سوالات'})
            
    except Exception as e:
        logging.error(f"Error generating questions: {e}")
        return jsonify({'success': False, 'error': 'خطای سرور'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
