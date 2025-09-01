import logging
from models import db, Question, Student, StudentAnswer
from sqlalchemy import func

def calculate_analytics():
    """
    Calculate analytics for all questions including:
    - Average difficulty percentage 
    - Average discrimination index
    """
    try:
        questions = Question.query.all()
        
        for question in questions:
            # Get all answers for this question
            answers = StudentAnswer.query.filter_by(question_id=question.id).all()
            
            if not answers:
                continue
            
            # Calculate difficulty percentage (percentage who got it right)
            total_answers = len(answers)
            correct_answers = sum(1 for answer in answers if answer.is_correct)
            difficulty_percent = (correct_answers / total_answers) * 100
            
            # Calculate discrimination index
            discrimination_index = calculate_discrimination_index(question.id)
            
            # Update question analytics
            question.avg_difficulty_percent = difficulty_percent
            question.avg_discrimination_index = discrimination_index
        
        db.session.commit()
        logging.info("Analytics calculation completed successfully")
        
    except Exception as e:
        logging.error(f"Error calculating analytics: {e}")
        db.session.rollback()

def calculate_discrimination_index(question_id: int) -> float:
    """
    Calculate discrimination index for a specific question
    Uses the 27% rule: compare top 27% performers vs bottom 27% performers
    """
    try:
        # Get all students who answered this question
        student_answers = StudentAnswer.query.filter_by(question_id=question_id).all()
        
        if len(student_answers) < 6:  # Need at least 6 students for meaningful analysis
            return 0.0
        
        # Calculate total score for each student
        student_scores = {}
        for answer in student_answers:
            if answer.student_id not in student_scores:
                # Calculate total correct answers for this student
                total_correct = db.session.query(func.sum(StudentAnswer.is_correct))\
                    .filter_by(student_id=answer.student_id).scalar() or 0
                student_scores[answer.student_id] = total_correct
        
        # Sort students by total score
        sorted_students = sorted(student_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate 27% groups
        total_students = len(sorted_students)
        group_size = max(1, int(total_students * 0.27))
        
        # Get top and bottom groups
        top_group = [student_id for student_id, _ in sorted_students[:group_size]]
        bottom_group = [student_id for student_id, _ in sorted_students[-group_size:]]
        
        # Calculate mean performance on this specific question for each group
        top_answers = StudentAnswer.query.filter(
            StudentAnswer.question_id == question_id,
            StudentAnswer.student_id.in_(top_group)
        ).all()
        
        bottom_answers = StudentAnswer.query.filter(
            StudentAnswer.question_id == question_id,
            StudentAnswer.student_id.in_(bottom_group)
        ).all()
        
        # Calculate means
        mean_upper = sum(answer.is_correct for answer in top_answers) / len(top_answers) if top_answers else 0
        mean_lower = sum(answer.is_correct for answer in bottom_answers) / len(bottom_answers) if bottom_answers else 0
        
        # Discrimination index = Mean_Upper - Mean_Lower
        discrimination_index = mean_upper - mean_lower
        
        return discrimination_index
        
    except Exception as e:
        logging.error(f"Error calculating discrimination index for question {question_id}: {e}")
        return 0.0

def get_question_quality_summary():
    """
    Get summary of question quality based on discrimination index
    Returns counts of questions in each quality category
    """
    try:
        questions = Question.query.filter(Question.avg_discrimination_index.isnot(None)).all()
        
        excellent = sum(1 for q in questions if q.avg_discrimination_index >= 0.4)
        acceptable = sum(1 for q in questions if 0.2 <= q.avg_discrimination_index < 0.4)
        poor = sum(1 for q in questions if q.avg_discrimination_index < 0.2)
        
        return {
            'excellent': excellent,
            'acceptable': acceptable, 
            'poor': poor,
            'total': len(questions)
        }
        
    except Exception as e:
        logging.error(f"Error getting question quality summary: {e}")
        return {'excellent': 0, 'acceptable': 0, 'poor': 0, 'total': 0}

def get_prerequisite_performance():
    """
    Get performance statistics for each prerequisite
    """
    try:
        from app import PREREQUISITES
        
        stats = []
        for prerequisite in PREREQUISITES:
            questions = Question.query.filter_by(prerequisite_name=prerequisite).all()
            if not questions:
                stats.append({
                    'name': prerequisite,
                    'total_questions': 0,
                    'avg_difficulty': 0,
                    'avg_discrimination': 0,
                    'times_used': 0
                })
                continue
                
            total_questions = len(questions)
            avg_difficulty = sum(q.avg_difficulty_percent or 0 for q in questions) / total_questions
            avg_discrimination = sum(q.avg_discrimination_index or 0 for q in questions) / total_questions  
            total_times_used = sum(q.times_used for q in questions)
            
            stats.append({
                'name': prerequisite,
                'total_questions': total_questions,
                'avg_difficulty': round(avg_difficulty, 1),
                'avg_discrimination': round(avg_discrimination, 3),
                'times_used': total_times_used
            })
        
        return stats
        
    except Exception as e:
        logging.error(f"Error getting prerequisite performance: {e}")
        return []
