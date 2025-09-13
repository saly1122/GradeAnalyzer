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
# Set secure secret key - generate random one for development
import secrets
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret:
    # Generate a secure random secret for development
    session_secret = secrets.token_hex(32)
    logging.warning("SESSION_SECRET not set in environment. Using generated secret for development.")
app.secret_key = session_secret
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure PostgreSQL database
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix SSL connection issues for PostgreSQL
    if '?' not in database_url:
        database_url += '?sslmode=prefer'
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=prefer'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'prefer',
            'connect_timeout': 10
        }
    }
else:
    # Fallback to SQLite in /tmp for serverless compatibility
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/mathboost.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Admin credentials from environment
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Grade-specific prerequisites for Iranian curriculum (Grades 7-12)
GRADE_PREREQUISITES = {
    "ششم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی", 
        "کسرها و اعمال روی کسرها",
        "اعشار و تبدیل کسر به اعشار",
        "درصد و کاربردهای آن"
    ],
    "هفتم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی",
        "کسرها و اعمال روی کسرها", 
        "اعشار و تبدیل کسر به اعشار",
        "درصد و کاربردهای آن",
        "اعداد صحیح و عملیات روی آنها",
        "اعداد گویا و مقایسه آنها",
        "توان و ریشه دوم",
        "عبارت‌های جبری ساده",
        "معادلات درجه یک"
    ],
    "هشتم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی",
        "کسرها و اعمال روی کسرها",
        "اعشار و تبدیل کسر به اعشار", 
        "درصد و کاربردهای آن",
        "اعداد صحیح و عملیات روی آنها",
        "اعداد گویا و مقایسه آنها",
        "توان و ریشه دوم",
        "عبارت‌های جبری ساده",
        "معادلات درجه یک",
        "عملیات روی عبارت‌های جبری",
        "معادلات دو مجهوله",
        "نسبت و تناسب",
        "هندسه مثلث",
        "مساحت اشکال هندسی"
    ],
    "نهم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی",
        "کسرها و اعمال روی کسرها",
        "اعشار و تبدیل کسر به اعشار",
        "درصد و کاربردهای آن", 
        "اعداد صحیح و عملیات روی آنها",
        "اعداد گویا و مقایسه آنها",
        "توان و ریشه دوم",
        "عبارت‌های جبری ساده",
        "معادلات درجه یک",
        "عملیات روی عبارت‌های جبری",
        "معادلات دو مجهوله", 
        "نسبت و تناسب",
        "هندسه مثلث",
        "مساحت اشکال هندسی",
        "اعداد حقیقی",
        "رادیکال و عملیات روی آن",
        "عبارت‌های جبری پیچیده",
        "معادلات درجه دو",
        "تابع و نمودار"
    ],
    "دهم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی",
        "کسرها و اعمال روی کسرها",
        "اعشار و تبدیل کسر به اعشار",
        "درصد و کاربردهای آن",
        "اعداد صحیح و عملیات روی آنها", 
        "اعداد گویا و مقایسه آنها",
        "توان و ریشه دوم",
        "عبارت‌های جبری ساده",
        "معادلات درجه یک",
        "عملیات روی عبارت‌های جبری",
        "معادلات دو مجهوله",
        "نسبت و تناسب",
        "هندسه مثلث",
        "مساحت اشکال هندسی",
        "اعداد حقیقی",
        "رادیکال و عملیات روی آن",
        "عبارت‌های جبری پیچیده", 
        "معادلات درجه دو",
        "تابع و نمودار",
        "مثلثات پایه",
        "لگاریتم",
        "دنباله و سری",
        "هندسه تحلیلی",
        "احتمال و آمار پایه"
    ],
    "یازدهم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی", 
        "کسرها و اعمال روی کسرها",
        "اعشار و تبدیل کسر به اعشار",
        "درصد و کاربردهای آن",
        "اعداد صحیح و عملیات روی آنها",
        "اعداد گویا و مقایسه آنها",
        "توان و ریشه دوم",
        "عبارت‌های جبری ساده",
        "معادلات درجه یک",
        "عملیات روی عبارت‌های جبری",
        "معادلات دو مجهوله",
        "نسبت و تناسب",
        "هندسه مثلث",
        "مساحت اشکال هندسی",
        "اعداد حقیقی",
        "رادیکال و عملیات روی آن",
        "عبارت‌های جبری پیچیده",
        "معادلات درجه دو",
        "تابع و نمودار",
        "مثلثات پایه",
        "لگاریتم",
        "دنباله و سری",
        "هندسه تحلیلی",
        "احتمال و آمار پایه",
        "مثلثات پیشرفته",
        "حد و پیوستگی",
        "مشتق",
        "کاربردهای مشتق",
        "انتگرال پایه"
    ],
    "دوازدهم": [
        "جمع و تفریق اعداد طبیعی",
        "ضرب و تقسیم اعداد طبیعی",
        "کسرها و اعمال روی کسرها",
        "اعشار و تبدیل کسر به اعشار",
        "درصد و کاربردهای آن",
        "اعداد صحیح و عملیات روی آنها",
        "اعداد گویا و مقایسه آنها",
        "توان و ریشه دوم",
        "عبارت‌های جبری ساده",
        "معادلات درجه یک",
        "عملیات روی عبارت‌های جبری",
        "معادلات دو مجهوله",
        "نسبت و تناسب",
        "هندسه مثلث",
        "مساحت اشکال هندسی",
        "اعداد حقیقی",
        "رادیکال و عملیات روی آن",
        "عبارت‌های جبری پیچیده",
        "معادلات درجه دو",
        "تابع و نمودار",
        "مثلثات پایه",
        "لگاریتم",
        "دنباله و سری", 
        "هندسه تحلیلی",
        "احتمال و آمار پایه",
        "مثلثات پیشرفته",
        "حد و پیوستگی",
        "مشتق",
        "کاربردهای مشتق",
        "انتگرال پایه",
        "انتگرال تعیین",
        "معادلات دیفرانسیل ساده",
        "آمار و احتمال پیشرفته",
        "ترکیبات و جایگشت",
        "هندسه فضایی"
    ]
}

def get_prerequisites_for_grade(grade):
    """Get prerequisites for a specific grade"""
    return GRADE_PREREQUISITES.get(grade, [])

def generate_questions(prerequisite_name, count=1):
    """Generate questions for a specific prerequisite"""
    try:
        # Sample questions data
        sample_questions_data = [
            # Basic arithmetic - grade 6-7 level
            {
                "prerequisite": "جمع و تفریق اعداد طبیعی",
                "text": "حاصل جمع ۲۵ + ۳۷ چقدر است؟",
                "answer": "۶۲"
            },
            {
                "prerequisite": "جمع و تفریق اعداد طبیعی",
                "text": "حاصل تفریق ۵۰ - ۲۳ چقدر است؟",
                "answer": "۲۷"
            },
            {
                "prerequisite": "ضرب و تقسیم اعداد طبیعی",
                "text": "حاصل ضرب ۸ × ۹ چقدر است؟",
                "answer": "۷۲"
            },
            {
                "prerequisite": "ضرب و تقسیم اعداد طبیعی",
                "text": "حاصل تقسیم ۸۱ ÷ ۹ چقدر است؟",
                "answer": "۹"
            },
            {
                "prerequisite": "کسرها و اعمال روی کسرها",
                "text": "حاصل ۱/۲ + ۱/۴ چقدر است؟",
                "answer": "۳/۴"
            },
            {
                "prerequisite": "درصد و کاربردهای آن",
                "text": "۲۵ درصد از ۸۰ چقدر است؟",
                "answer": "۲۰"
            },
            {
                "prerequisite": "اعداد صحیح و عملیات روی آنها",
                "text": "حاصل (-۵) + (۳) چقدر است؟",
                "answer": "-۲"
            },
            {
                "prerequisite": "معادلات درجه یک",
                "text": "مقدار x در معادله ۲x + ۵ = ۱۱ چقدر است؟",
                "answer": "۳"
            },
            {
                "prerequisite": "معادلات درجه دو",
                "text": "ریشه‌های معادله x² - 5x + 6 = 0 کدام هستند؟",
                "answer": "۲ و ۳"
            },
            {
                "prerequisite": "توابع و نمودار",
                "text": "اگر f(x) = 2x + 1 باشد، f(3) چقدر است؟",
                "answer": "۷"
            }
        ]
        
        # Filter questions for the specific prerequisite
        matching_questions = [q for q in sample_questions_data if q["prerequisite"] == prerequisite_name]
        
        if not matching_questions:
            # Fallback: return a generic question
            return [{
                "text": f"سوال نمونه برای {prerequisite_name}. لطفا یک عدد وارد کنید:",
                "answer": "۱"
            }]
        
        # Return the requested number of questions (cycling if needed)
        result = []
        for i in range(count):
            result.append(matching_questions[i % len(matching_questions)])
        
        return result
        
    except Exception as e:
        logging.error(f"Error generating questions for {prerequisite_name}: {e}")
        # Return a fallback question
        return [{
            "text": f"سوال نمونه برای {prerequisite_name}. لطفا عدد ۱ را وارد کنید:",
            "answer": "۱"
        }]

# For backward compatibility
PREREQUISITES = GRADE_PREREQUISITES.get("هفتم", [])

def add_sample_questions():
    """Add sample questions for testing purposes"""
    sample_questions = [
        # Basic arithmetic - grade 6-7 level
        {
            "prerequisite_name": "جمع و تفریق اعداد طبیعی",
            "difficulty_level": "easy",
            "question_text": "حاصل جمع ۲۵ + ۳۷ چقدر است؟",
            "correct_answer": "۶۲"
        },
        {
            "prerequisite_name": "ضرب و تقسیم اعداد طبیعی",
            "difficulty_level": "easy", 
            "question_text": "حاصل ضرب ۸ × ۹ چقدر است؟",
            "correct_answer": "۷۲"
        },
        {
            "prerequisite_name": "کسرها و اعمال روی کسرها",
            "difficulty_level": "medium",
            "question_text": "حاصل $\\frac{1}{2} + \\frac{1}{4}$ چقدر است؟",
            "correct_answer": "۳/۴"
        },
        {
            "prerequisite_name": "درصد و کاربردهای آن",
            "difficulty_level": "medium",
            "question_text": "۲۵ درصد از ۸۰ چقدر است؟",
            "correct_answer": "۲۰"
        },
        # Intermediate level - grade 8-9
        {
            "prerequisite_name": "اعداد صحیح و عملیات روی آنها",
            "difficulty_level": "medium",
            "question_text": "حاصل (-۵) + (۳) چقدر است؟",
            "correct_answer": "-۲"
        },
        {
            "prerequisite_name": "معادلات درجه یک", 
            "difficulty_level": "medium",
            "question_text": "مقدار x در معادله ۲x + ۵ = ۱۱ چقدر است؟",
            "correct_answer": "۳"
        },
        # Advanced level - grade 10-12
        {
            "prerequisite_name": "معادلات درجه دو",
            "difficulty_level": "hard",
            "question_text": "ریشه‌های معادله $x^2 - 5x + 6 = 0$ کدام هستند؟",
            "correct_answer": "۲ و ۳"
        },
        {
            "prerequisite_name": "تابع و نمودار",
            "difficulty_level": "hard", 
            "question_text": "اگر $f(x) = 2x + 1$ باشد، مقدار $f(3)$ چقدر است؟",
            "correct_answer": "۷"
        }
    ]
    
    for q_data in sample_questions:
        question = Question(
            prerequisite_name=q_data["prerequisite_name"],
            difficulty_level=q_data["difficulty_level"],
            question_text=q_data["question_text"],
            correct_answer=q_data["correct_answer"],
            times_used=0
        )
        db.session.add(question)
    
    db.session.commit()
    logging.info(f"Added {len(sample_questions)} sample questions for testing")

def create_tables():
    """Initialize database tables and sample data"""
    db.create_all()
    
    # Add sample video links for all prerequisites if not exist
    if not PrerequisiteVideo.query.first():
        # Get all unique prerequisites from all grades
        all_prerequisites = set()
        for grade_prereqs in GRADE_PREREQUISITES.values():
            all_prerequisites.update(grade_prereqs)
        
        # Create sample video entries for all prerequisites
        for i, prerequisite in enumerate(sorted(all_prerequisites), 1):
            video = PrerequisiteVideo(
                prerequisite_name=prerequisite, 
                video_url=f"https://example.com/video{i}"
            )
            db.session.add(video)
        
        db.session.commit()
        
        # Add sample questions for testing if no questions exist
        if not Question.query.first():
            add_sample_questions()

# Database initialization function for lazy loading
def init_db_if_needed():
    """Initialize database tables and sample data on first request"""
    try:
        # Try a simple query to see if tables exist
        PrerequisiteVideo.query.first()
    except Exception:
        # Tables don't exist, create them
        db.create_all()
        
        # Add sample video links for all prerequisites if not exist
        if not PrerequisiteVideo.query.first():
            # Get all unique prerequisites from all grades
            all_prerequisites = set()
            for grade_prereqs in GRADE_PREREQUISITES.values():
                all_prerequisites.update(grade_prereqs)
            
            # Create sample video entries for all prerequisites
            for i, prerequisite in enumerate(sorted(all_prerequisites), 1):
                video = PrerequisiteVideo(
                    prerequisite_name=prerequisite, 
                    video_url=f"https://example.com/video{i}"
                )
                db.session.add(video)
            
            db.session.commit()
            
            # Add sample questions for testing if no questions exist
            if not Question.query.first():
                add_sample_questions()

# Student Routes
@app.route('/')
def index():
    """Main assessment page for students"""
    init_db_if_needed()
    return render_template('index.html')

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Start a new student assessment session"""
    try:
        init_db_if_needed()
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
        session['student_grade'] = student_grade
        session['current_prerequisite_index'] = 0
        session['score'] = 0
        session['total_questions'] = 0
        
        # Debug logging for session creation
        logging.info(f"Session created for student {student.id}: {dict(session)}")
        
        return jsonify({'success': True, 'student_id': student.id})
        
    except Exception as e:
        logging.error(f"Error starting session: {e}")
        return jsonify({'success': False, 'error': 'خطا در شروع جلسه'})

@app.route('/api/get_question', methods=['GET'])
def get_question():
    """Get next question for student"""
    try:
        # Debug logging for session
        logging.debug(f"Session contents: {dict(session)}")
        logging.debug(f"Student ID in session: {'student_id' in session}")
        
        if 'student_id' not in session:
            logging.error("Session does not contain student_id")
            return jsonify({'success': False, 'error': 'جلسه یافت نشد'})
        
        prerequisite_index = session.get('current_prerequisite_index', 0)
        student_grade = session.get('student_grade', 'هفتم')
        
        # Get prerequisites for student's grade
        grade_prerequisites = get_prerequisites_for_grade(student_grade)
        
        # Check if assessment is complete
        if prerequisite_index >= len(grade_prerequisites):
            return jsonify({
                'success': True, 
                'completed': True,
                'score': session.get('score', 0),
                'total': session.get('total_questions', 0)
            })
        
        prerequisite = grade_prerequisites[prerequisite_index]
        
        # Generate question for current prerequisite using new system
        logging.info(f"Generating new questions for: {prerequisite}")
        questions = generate_questions(prerequisite, 1)
        
        if not questions:
            return jsonify({'success': False, 'error': 'خطا در تولید سوال'})
        
        question = questions[0]
        
        return jsonify({
            'success': True,
            'question': {
                'text': question['text'],
                'prerequisite': prerequisite
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting question: {e}")
        return jsonify({'success': False, 'error': 'خطا در دریافت سوال'})

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """Submit student answer"""
    try:
        if 'student_id' not in session:
            return jsonify({'success': False, 'error': 'جلسه یافت نشد'})
        
        data = request.get_json()
        answer = data.get('answer', '').strip()
        
        if not answer:
            return jsonify({'success': False, 'error': 'لطفا پاسخ خود را وارد کنید'})
        
        student_id = session['student_id']
        prerequisite_index = session.get('current_prerequisite_index', 0)
        student_grade = session.get('student_grade', 'هفتم')
        
        # Get current question info
        current_prerequisites = get_prerequisites_for_grade(student_grade)
        if prerequisite_index >= len(current_prerequisites):
            return jsonify({'success': False, 'error': 'آزمون تمام شده است'})
        
        current_prerequisite = current_prerequisites[prerequisite_index]
        
        # Generate or get question for current prerequisite
        questions = generate_questions(current_prerequisite, 1)
        if not questions:
            return jsonify({'success': False, 'error': 'خطا در تولید سوال'})
        
        question = questions[0]
        correct_answer = question['answer']
        
        # Check for "don't know" answer
        is_dont_know = answer == 'بلد نیستم'
        
        # Check if answer is correct (simple string comparison for now)
        is_correct = False if is_dont_know else answer.lower().strip() == str(correct_answer).lower().strip()
        
        # Update session score (don't count "don't know" as wrong)
        session['total_questions'] = session.get('total_questions', 0) + 1
        if is_correct:
            session['score'] = session.get('score', 0) + 1
        
        # Move to next prerequisite
        session['current_prerequisite_index'] = prerequisite_index + 1
        
        # Save answer to database
        answer_value = 1 if is_correct else (-1 if is_dont_know else 0)
        student_answer = StudentAnswer(
            student_id=student_id,
            prerequisite_name=current_prerequisite,
            student_answer=answer,
            correct_answer=str(correct_answer),
            is_correct=answer_value
        )
        db.session.add(student_answer)
        db.session.commit()
        
        logging.info(f"Student {student_id} answered '{answer}' for {current_prerequisite}: {'correct' if is_correct else 'incorrect' if not is_dont_know else 'dont_know'}")
        
        return jsonify({
            'success': True,
            'correct': is_correct,
            'correct_answer': str(correct_answer),
            'dont_know': is_dont_know
        })
        
    except Exception as e:
        logging.error(f"Error submitting answer: {e}")
        return jsonify({'success': False, 'error': 'خطا در ثبت پاسخ'})

@app.route('/api/get_results', methods=['GET'])
def get_results():
    """Get detailed student results with strengths/weaknesses analysis"""
    try:
        if 'student_id' not in session:
            return jsonify({'success': False, 'error': 'جلسه یافت نشد'})
        
        student_id = session['student_id']
        score = session.get('score', 0)
        total = session.get('total_questions', 0)
        
        # Get all student answers for analysis
        answers = StudentAnswer.query.filter_by(student_id=student_id).all()
        
        # Analyze strengths and weaknesses
        strengths = []
        weaknesses = []
        
        # Group answers by prerequisite
        prerequisite_performance = {}
        for answer in answers:
            prereq = answer.prerequisite_name
            if prereq not in prerequisite_performance:
                prerequisite_performance[prereq] = {'correct': 0, 'total': 0, 'dont_know': 0}
            
            prerequisite_performance[prereq]['total'] += 1
            if answer.is_correct == 1:
                prerequisite_performance[prereq]['correct'] += 1
            elif answer.is_correct == -1:
                prerequisite_performance[prereq]['dont_know'] += 1
        
        # Determine strengths and weaknesses
        for prereq, performance in prerequisite_performance.items():
            total_answered = performance['total']
            correct_answers = performance['correct']
            dont_know_count = performance['dont_know']
            
            # Calculate success rate excluding "don't know" answers
            # Only count answers where student actually attempted (correct or incorrect)
            attempted_answers = total_answered - dont_know_count
            
            if attempted_answers > 0:
                success_rate = correct_answers / attempted_answers
                
                # Get educational video link
                video = PrerequisiteVideo.query.filter_by(prerequisite_name=prereq).first()
                video_link = video.video_url if video else None
                
                result_item = {
                    'prerequisite': prereq,
                    'correct': correct_answers,
                    'attempted': attempted_answers,
                    'total': total_answered,
                    'dont_know': dont_know_count,
                    'success_rate': round(success_rate * 100, 1),
                    'video_link': video_link
                }
                
                # Consider as strength if success rate >= 70%
                if success_rate >= 0.7:
                    strengths.append(result_item)
                else:
                    weaknesses.append(result_item)
        
        # Calculate total attempted (excluding "don't know" answers)
        total_attempted = len([a for a in answers if a.is_correct != -1])
        
        return jsonify({
            'success': True,
            'score': score,
            'total': total,
            'attempted': total_attempted,
            'percentage': round((score / total_attempted * 100) if total_attempted > 0 else 0, 1),
            'strengths': strengths,
            'weaknesses': weaknesses
        })
        
    except Exception as e:
        logging.error(f"Error getting results: {e}")
        return jsonify({'success': False, 'error': 'خطا در دریافت نتایج'})

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    init_db_if_needed()
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
