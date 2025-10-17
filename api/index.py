"""
Vercel serverless entry point
This file is required for Vercel to serve the Flask application
"""
from app import app

# Vercel looks for 'app' or 'application' in this file
# No need to do anything else - just import and expose the Flask app
