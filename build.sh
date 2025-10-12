#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

flask db upgrade

python -c "
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@tyaira.com',
            password_hash=generate_password_hash('admin123'),
            is_subscriber=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
        print('Username: admin')
        print('Password: admin123')
    else:
        print('Admin user already exists.')
"

python -c "
from app import app, db
from models import Question

with app.app_context():
    question_count = Question.query.count()
    if question_count == 0:
        print('No questions found. Running import script...')
        import subprocess
        subprocess.run(['python', 'import_questions.py'])
    else:
        print(f'Database already has {question_count} questions. Skipping import.')
"
