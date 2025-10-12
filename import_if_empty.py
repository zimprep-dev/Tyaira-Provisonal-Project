#!/usr/bin/env python
"""Import questions if database is empty"""

from app import app, db
from models import Question
import subprocess

with app.app_context():
    question_count = Question.query.count()
    if question_count == 0:
        print('No questions found. Running import script...')
        subprocess.run(['python', 'import_questions.py'])
    else:
        print(f'Database already has {question_count} questions. Skipping import.')
