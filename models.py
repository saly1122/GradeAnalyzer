from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Question(db.Model):
    """Model for storing generated questions"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    prerequisite_name = db.Column(db.String(200), nullable=False)
    difficulty_level = db.Column(db.String(50), nullable=False)  # 'easy', 'medium', 'hard'
    question_text = db.Column(db.Text, nullable=False, unique=True)
    correct_answer = db.Column(db.String(500), nullable=False)
    times_used = db.Column(db.Integer, default=0)
    
    # Analytics columns
    avg_difficulty_percent = db.Column(db.Float)
    avg_discrimination_index = db.Column(db.Float)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.prerequisite_name}>'

class Student(db.Model):
    """Model for storing student session information"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_grade = db.Column(db.String(50), nullable=False)
    session_start_time = db.Column(db.String(50), nullable=False)
    
    # Relationship to student answers
    answers = db.relationship('StudentAnswer', backref='student', lazy=True)
    
    def __repr__(self):
        return f'<Student {self.id}: {self.student_name}>'

class StudentAnswer(db.Model):
    """Model for storing individual student answers"""
    __tablename__ = 'student_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    prerequisite_name = db.Column(db.String(200), nullable=False)
    student_answer = db.Column(db.String(500))
    correct_answer = db.Column(db.String(500))
    is_correct = db.Column(db.Integer, nullable=False)  # 1 for correct, 0 for incorrect, -1 for "don't know"
    
    def __repr__(self):
        return f'<StudentAnswer {self.id}: Student {self.student_id}, {self.prerequisite_name}>'

class PrerequisiteVideo(db.Model):
    """Model for storing educational video links"""
    __tablename__ = 'prerequisite_videos'
    
    id = db.Column(db.Integer, primary_key=True)
    prerequisite_name = db.Column(db.String(200), nullable=False, unique=True)
    video_url = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<PrerequisiteVideo {self.id}: {self.prerequisite_name}>'
