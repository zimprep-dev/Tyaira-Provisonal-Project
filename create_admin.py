#!/usr/bin/env python
"""Create admin user if it doesn't exist"""

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
        print('WARNING: CHANGE THIS PASSWORD AFTER FIRST LOGIN!')
    else:
        print('Admin user already exists.')
