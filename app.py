from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///driver_testing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_subscriber = db.Column(db.Boolean, default=False)
    subscription_date = db.Column(db.DateTime)
    tests_taken = db.relationship('TestResult', backref='user', lazy=True)
    downloads_count = db.Column(db.Integer, default=0)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    time_taken = db.Column(db.Integer)  # in seconds

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    category = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load sample questions
def load_questions():
    if not Question.query.first():
        sample_questions = [
            {
                "question_text": "What should you do when approaching a red traffic light?",
                "option_a": "Speed up to get through quickly",
                "option_b": "Stop and wait for green light",
                "option_c": "Ignore the light if no cars are coming",
                "correct_answer": "B",
                "category": "Traffic Signs"
            },
            {
                "question_text": "What is the speed limit in a residential area?",
                "option_a": "60 km/h",
                "option_b": "80 km/h", 
                "option_c": "40 km/h",
                "correct_answer": "C",
                "category": "Speed Limits"
            },

            {
                "question_text": "When should you use your hazard lights?",
                "option_a": "When driving in rain",
                "option_b": "When your car breaks down",
                "option_c": "When you're in a hurry",
                "correct_answer": "B",
                "category": "Safety"

            },  
        ]
        
        for q_data in sample_questions:
            question = Question(**q_data)
            db.session.add(question)
        
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_tests = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.test_date.desc()).limit(5)
    return render_template('dashboard.html', user=current_user, tests=user_tests)

@app.route('/take_test')
@login_required
def take_test():
    # Check if user can take test (free tier limit)
    if not current_user.is_subscriber:
        today_tests = TestResult.query.filter(
            TestResult.user_id == current_user.id,
            TestResult.test_date >= datetime.utcnow().date()
        ).count()
        
        if today_tests >= 2:  # Free tier: 2 tests per day
            flash('Free tier limit reached. Subscribe for unlimited tests.')
            return redirect(url_for('dashboard'))
    
    questions = Question.query.limit(5).all()  # 5 questions for demo
    random.shuffle(questions)
    return render_template('test.html', questions=questions)

@app.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    data = request.get_json()
    answers = data.get('answers', {})
    
    score = 0
    total_questions = len(answers)
    
    for question_id, answer in answers.items():
        question = Question.query.get(question_id)
        if question and answer == question.correct_answer:
            score += 1
    
    # Save test result
    test_result = TestResult(
        user_id=current_user.id,
        score=score,
        total_questions=total_questions,
        time_taken=data.get('time_taken', 0)
    )
    db.session.add(test_result)
    db.session.commit()
    
    return jsonify({
        'score': score,
        'total': total_questions,
        'percentage': round((score / total_questions) * 100, 1)
    })

@app.route('/subscribe')
@login_required
def subscribe():
    current_user.is_subscriber = True
    current_user.subscription_date = datetime.utcnow()
    db.session.commit()
    flash('Subscription activated! You now have unlimited access.')
    return redirect(url_for('dashboard'))

@app.route('/download_pdf')
@login_required
def download_pdf():
    if current_user.is_subscriber or current_user.downloads_count < 3:
        if not current_user.is_subscriber:
            current_user.downloads_count += 1
            db.session.commit()
        
        # In a real app, you'd serve actual PDF files
        flash('PDF download started! (Demo mode)')
    else:
        flash('Download limit reached. Subscribe for unlimited downloads.')
    
    return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/admin')
@login_required
def admin():
    # Simple admin check - in production, use proper role-based access
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    questions = Question.query.all()
    users = User.query.all()
    
    # Calculate statistics
    stats = {
        'total_users': User.query.count(),
        'premium_users': User.query.filter_by(is_subscriber=True).count(),
        'total_tests': TestResult.query.count(),
        'total_questions': Question.query.count()
    }
    
    # Mock recent activity
    recent_activity = [
        {'timestamp': '2024-01-15 14:30', 'description': 'New user registered: john_doe'},
        {'timestamp': '2024-01-15 13:45', 'description': 'Test completed by user: jane_smith'},
        {'timestamp': '2024-01-15 12:20', 'description': 'Premium subscription activated: mike_jones'}
    ]
    
    return render_template('admin.html', 
                         questions=questions, 
                         users=users, 
                         stats=stats, 
                         recent_activity=recent_activity)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_questions()
    
    app.run(debug=True)

