import os
import json
import logging
import google.genai as genai
from google.genai import types
from models import db, Question
from pydantic import BaseModel
from typing import List, Dict

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "your-api-key-here"))

class GeneratedQuestion(BaseModel):
    """Pydantic model for structured question generation"""
    difficulty_level: str
    question_text: str
    correct_answer: str

class QuestionSet(BaseModel):
    """Pydantic model for a set of generated questions"""
    questions: List[GeneratedQuestion]

def generate_questions_from_ai(prerequisite_name: str) -> bool:
    """
    Generate questions using Gemini AI for a specific prerequisite
    Returns True if successful, False otherwise
    """
    # Check if API key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        logging.warning(f"No valid Gemini API key found. Skipping AI question generation for {prerequisite_name}")
        return False
    
    try:
        # Create detailed prompt in Persian
        prompt = f"""
        لطفاً برای پیش‌نیاز ریاضی "{prerequisite_name}" سه سوال تشخیصی با سطوح مختلف سختی تولید کنید.
        
        مشخصات مورد نیاز:
        1. سه سوال با سطوح سختی: آسان، متوسط، سخت
        2. هر سوال باید دقیقاً یک پاسخ کوتاه و مشخص داشته باشد (عدد، کلمه، یا عبارت کوتاه)
        3. سوالات باید مناسب دانش‌آموزان دبستان و راهنمایی باشند
        4. از عبارات ریاضی ساده استفاده کنید که با MathJax قابل نمایش باشند
        5. سوالات باید برای تشخیص میزان تسلط دانش‌آموز طراحی شوند
        
        مثال فرمت پاسخ:
        {{
            "questions": [
                {{
                    "difficulty_level": "easy",
                    "question_text": "حاصل $2 + 3$ چقدر است؟",
                    "correct_answer": "5"
                }},
                {{
                    "difficulty_level": "medium", 
                    "question_text": "اگر $\\frac{{3}}{{4}}$ یک عدد برابر با 12 باشد، آن عدد کدام است؟",
                    "correct_answer": "16"
                }},
                {{
                    "difficulty_level": "hard",
                    "question_text": "25 درصد از 80 چقدر است؟",
                    "correct_answer": "20"
                }}
            ]
        }}
        
        حال برای پیش‌نیاز "{prerequisite_name}" سه سوال مناسب تولید کنید:
        """
        
        system_instruction = """
        شما یک متخصص طراحی آزمون‌های تشخیصی ریاضی هستید. 
        وظیفه شما تولید سوالات دقیق و مناسب برای سنجش پیش‌نیازهای ریاضی دانش‌آموزان است.
        لطفاً فقط به صورت JSON پاسخ دهید و هیچ توضیح اضافی ندهید.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=prompt)])
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=QuestionSet,
            ),
        )
        
        if not response.text:
            logging.error("Empty response from Gemini API")
            return False
        
        # Parse JSON response
        try:
            data = json.loads(response.text)
            question_set = QuestionSet(**data)
        except (json.JSONDecodeError, Exception) as e:
            logging.error(f"Error parsing Gemini response: {e}")
            logging.error(f"Raw response: {response.text}")
            return False
        
        # Save questions to database
        questions_added = 0
        for q_data in question_set.questions:
            try:
                # Check if question already exists
                existing = Question.query.filter_by(question_text=q_data.question_text).first()
                if existing:
                    logging.info(f"Question already exists: {q_data.question_text[:50]}...")
                    continue
                
                question = Question(
                    prerequisite_name=prerequisite_name,
                    difficulty_level=q_data.difficulty_level,
                    question_text=q_data.question_text,
                    correct_answer=q_data.correct_answer,
                    times_used=0
                )
                db.session.add(question)
                questions_added += 1
                
            except Exception as e:
                logging.error(f"Error adding question to database: {e}")
                continue
        
        if questions_added > 0:
            db.session.commit()
            logging.info(f"Successfully generated {questions_added} questions for {prerequisite_name}")
            return True
        else:
            logging.warning(f"No new questions were added for {prerequisite_name}")
            return False
        
    except Exception as e:
        logging.error(f"Error generating questions from AI: {e}")
        return False

def test_gemini_connection():
    """Test connection to Gemini API"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="سلام، لطفاً عدد 5 را به من برگردانید."
        )
        return response.text is not None
    except Exception as e:
        logging.error(f"Gemini API test failed: {e}")
        return False
