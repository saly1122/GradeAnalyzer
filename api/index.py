"""
Entry point for Vercel serverless deployment
"""
from app import app

# This is the entry point for Vercel
application = app

# For Vercel serverless functions
def handler(event, context):
    return app(event, context)