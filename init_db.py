"""
Database initialization script
Run this to create the database schema
"""
import os
from app import app, db
from models import Question, Student, StudentAnswer, PrerequisiteVideo

def init_database():
    """Initialize the database with tables"""
    with app.app_context():
        # Drop all tables and recreate (for development)
        db.drop_all()
        db.create_all()
        
        # Add sample prerequisite videos
        sample_videos = [
            ("جمع و تفریق اعداد طبیعی", "https://www.youtube.com/watch?v=example1"),
            ("ضرب و تقسیم اعداد طبیعی", "https://www.youtube.com/watch?v=example2"),
            ("کسرها و اعمال روی کسرها", "https://www.youtube.com/watch?v=example3"),
            ("اعشار و تبدیل کسر به اعشار", "https://www.youtube.com/watch?v=example4"),
            ("درصد و کاربردهای آن", "https://www.youtube.com/watch?v=example5")
        ]
        
        for name, url in sample_videos:
            video = PrerequisiteVideo(prerequisite_name=name, video_url=url)
            db.session.add(video)
        
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
