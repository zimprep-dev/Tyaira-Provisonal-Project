#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
flask db upgrade

# Create admin user (if not exists)
echo "👤 Creating admin user..."
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
        print('✅ Admin user created successfully!')
        print('   Username: admin')
        print('   Password: admin123')
        print('   ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!')
    else:
        print('ℹ️  Admin user already exists.')
"

echo "✅ Build completed successfully!"
