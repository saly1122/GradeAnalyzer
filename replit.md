# MathBoost Analyzer

## Overview

MathBoost Analyzer is a Persian-language educational web application designed to assess students' mathematical knowledge through diagnostic tests. The system evaluates students on mathematical prerequisites and provides analytics to help identify strengths and weaknesses. It generates AI-powered questions using Google's Gemini AI and includes an admin panel for managing questions, videos, and analyzing student performance through statistical metrics like difficulty percentages and discrimination indexes.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask for server-side rendering
- **UI Framework**: Bootstrap with dark theme support for responsive design
- **Mathematics Rendering**: MathJax for displaying mathematical expressions and formulas
- **Internationalization**: Right-to-left (RTL) layout support for Persian language
- **Client-side Logic**: Vanilla JavaScript classes for student assessment flow and admin panel interactions

### Backend Architecture
- **Web Framework**: Flask application with session-based authentication
- **Database ORM**: SQLAlchemy for database operations and model definitions
- **AI Integration**: Google Gemini API for automatic question generation
- **Analytics Engine**: Custom calculation engine for educational metrics (difficulty percentage and discrimination index)
- **Authentication**: Simple username/password authentication for admin access
- **API Design**: RESTful endpoints for AJAX interactions between frontend and backend

### Data Storage Solutions
- **Primary Database**: SQLite for development with SQLAlchemy ORM
- **Database Models**:
  - Questions: Stores generated questions with difficulty levels and analytics
  - Students: Session-based student information and assessment data
  - StudentAnswers: Individual answer records for analytics calculation
  - PrerequisiteVideos: Educational video links for each mathematical topic
- **Session Management**: Flask sessions for maintaining student state during assessments

### Authentication and Authorization
- **Admin Authentication**: Environment-variable based credentials with session management
- **Student Sessions**: Anonymous session tracking without persistent authentication
- **Access Control**: Simple role-based access with admin-only routes for management functions

## External Dependencies

### Third-party Services
- **Google Gemini AI**: Question generation service using structured prompts in Persian
- **MathJax CDN**: Mathematical expression rendering engine
- **Bootstrap CDN**: UI framework with dark theme styling
- **Font Awesome**: Icon library for user interface elements

### APIs and Integrations
- **Gemini API**: Structured question generation with Pydantic models for validation
- **YouTube Integration**: Video link management for educational content
- **Environment Variables**: Configuration management for API keys and admin credentials

### Development Tools
- **Werkzeug**: WSGI utilities and development server with proxy fix support
- **Pydantic**: Data validation for AI-generated content structure
- **Logging**: Python logging module for debugging and error tracking

### Database Technology
- **SQLite**: File-based database for development and testing
- **SQLAlchemy**: ORM with support for database migrations and relationship management
- **Database Architecture**: Designed to be easily portable to PostgreSQL for production deployment