from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from sqlalchemy import func, case
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime, timedelta
import random
import uuid
from utils import is_mobile_device, get_device_type

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/tyaira'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}

# Create upload directories if they don't exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'), exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
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
    answers = db.relationship('Answer', backref='test_result', lazy=True, cascade="all, delete-orphan")

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.String(1))  # The answer the user selected (e.g., 'A', 'B')
    is_correct = db.Column(db.Boolean, nullable=False)

    question = db.relationship('Question')

class TestCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    questions = db.relationship('Question', backref='category', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('test_category.id'), nullable=False)
    difficulty = db.Column(db.String(20), default='basic')
    image_path = db.Column(db.String(200))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    options = db.relationship('AnswerOption', backref='question', lazy=True, cascade="all, delete-orphan")
    
    def get_correct_option(self):
        """Get the correct answer option for this question"""
        for option in self.options:
            if option.is_correct:
                return option
        return None
    
    def get_option_by_letter(self, letter):
        """Get option by letter (A, B, C, D)"""
        for option in self.options:
            if option.option_letter.upper() == letter.upper():
                return option
        return None

class AnswerOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    option_text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    option_letter = db.Column(db.String(1), nullable=False) # A, B, C, D

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'image' or 'pdf'
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Track active test sessions (lightweight)
class TestSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    question_ids = db.Column(db.Text)  # JSON list of question IDs
    time_limit_seconds = db.Column(db.Integer, default=30 * 60)

class TestConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    num_questions = db.Column(db.Integer, default=25, nullable=False)
    time_limit = db.Column(db.Integer, default=30, nullable=False) # In minutes
    categories = db.Column(db.Text) # JSON list of categories
    difficulty_distribution = db.Column(db.Text) # JSON object for difficulty percentages

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(80))
    description = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref='activity_logs')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# File upload utility functions
def allowed_file(filename, file_type):
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return extension in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'pdf':
        return extension in ALLOWED_PDF_EXTENSIONS
    return False

def get_file_size_string(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# Create admin user
def create_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            is_subscriber=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username='admin', password='admin123'")

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
            flash('Username already exists.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.')
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
    # This page is now for selecting a test
    categories = TestCategory.query.all()
    return render_template('test_selection.html', categories=categories)

@app.route('/test_interface/<category>')
@login_required
def test_interface(category):
    # Check if user can take test (free tier limit)
    if not current_user.is_subscriber and len(current_user.tests_taken) >= 10:
        flash('You have reached your limit of 10 free tests. Please subscribe for unlimited access.')
        return redirect(url_for('dashboard'))
    
    # Adaptive rendering: detect device and serve appropriate template
    device_type = get_device_type()
    
    # Debug: Print to console
    print(f"🔍 Device detected: {device_type}")
    print(f"📱 User-Agent: {request.headers.get('User-Agent', 'None')}")
    
    if device_type == 'mobile':
        print("✅ Serving MOBILE template")
        return render_template('mobile/test_interface_mobile.html', category=category)
    else:
        print("🖥️ Serving DESKTOP template")
        return render_template('test_interface.html', category=category)

@app.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    data = request.get_json()
    answers = data.get('answers', {})
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'Test session not found.'}), 400

    test_session = TestSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not test_session:
        return jsonify({'error': 'Invalid test session.'}), 400

    question_ids = json.loads(test_session.question_ids or '[]')
    total_questions = len(question_ids)

    # Create test result record first
    test_result = TestResult(
        user_id=current_user.id,
        score=0,  # We'll calculate this now
        total_questions=total_questions,
        time_taken=data.get('time_taken', 0)
    )

    score = 0
    for q_id in question_ids:
        question = Question.query.get(q_id)
        if not question:
            continue

        user_answer = answers.get(str(q_id))
        
        # Find the correct answer from the options
        correct_answer = None
        for option in question.options:
            if option.is_correct:
                correct_answer = option.option_letter
                break
        
        is_correct = user_answer is not None and user_answer == correct_answer
        
        if is_correct:
            score += 1

        # Create an answer record
        answer_record = Answer(
            test_result=test_result,
            question_id=q_id,
            user_answer=user_answer, # Save the user's actual answer
            is_correct=is_correct
        )
        db.session.add(answer_record)

    # Update the final score
    test_result.score = score
    
    db.session.add(test_result)
    # We need to commit here to get the test_result.id
    db.session.commit()
    
    percentage = round((score / total_questions) * 100, 1) if total_questions > 0 else 0

    return jsonify({
        'score': score,
        'total': total_questions,
        'percentage': percentage,
        'test_result_id': test_result.id  # Return the ID for the review link
    })

@app.route('/subscribe')
@login_required
def subscribe():
    current_user.is_subscriber = True
    current_user.subscription_date = datetime.utcnow()
    db.session.commit()
    flash('Subscription activated! You now have unlimited access.')
    return redirect(url_for('dashboard'))

@app.route('/download_pdf/<int:file_id>')
@login_required
def download_pdf(file_id):
    # Check if user has downloads left or is a subscriber
    if not current_user.is_subscriber and current_user.downloads_count >= 3:
        flash('Download limit reached. Subscribe for unlimited downloads.')
        return redirect(url_for('dashboard'))

    file_to_download = UploadedFile.query.get_or_404(file_id)

    if file_to_download.file_type != 'pdf':
        flash('Invalid file type.')
        return redirect(url_for('dashboard'))

    # Increment download count for free users
    if not current_user.is_subscriber:
        current_user.downloads_count += 1
        db.session.commit()
    
    # Send the file for download
    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'),
        file_to_download.filename,
        as_attachment=True,
        download_name=file_to_download.original_filename
    )

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/test_review/<int:test_result_id>')
@login_required
def test_review(test_result_id):
    test_result = TestResult.query.get_or_404(test_result_id)

    # Ensure the user can only review their own tests
    if test_result.user_id != current_user.id:
        flash('You are not authorized to view this page.')
        return redirect(url_for('dashboard'))

    # Calculate percentage
    percentage = round((test_result.score / test_result.total_questions) * 100)
    
    # Adaptive rendering for mobile
    device_type = get_device_type()
    
    if device_type == 'mobile':
        return render_template('mobile/test_review_mobile.html', 
                             test_result=test_result, 
                             percentage=percentage)
    else:
        # Fetch incorrect answers for desktop view
        incorrect_answers = Answer.query.filter_by(test_result_id=test_result.id, is_correct=False).all()
        return render_template('test_review.html', test_result=test_result, incorrect_answers=incorrect_answers)

# CMS Admin Routes
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if current_user.username != 'admin':
        flash('Access denied.')
        return redirect(url_for('dashboard'))

    # Core stats
    total_tests = TestResult.query.count()
    avg_score_raw = db.session.query(func.avg(TestResult.score * 100.0 / TestResult.total_questions)).scalar()
    average_score = round(avg_score_raw, 2) if avg_score_raw else 0

    # Pass/Fail Rate (assuming 80% is a pass)
    PASS_THRESHOLD = 80
    pass_count = TestResult.query.filter((TestResult.score * 100.0 / TestResult.total_questions) >= PASS_THRESHOLD).count()
    fail_count = total_tests - pass_count

    # Performance by category
    category_performance_raw = db.session.query(
        Question.category,
        func.count(Answer.id).label('total'),
        func.sum(case((Answer.is_correct, 1), else_=0)).label('correct')
    ).join(Answer, Answer.question_id == Question.id).group_by(Question.category).all()

    category_performance = {
        cat: round((correct / total) * 100, 2) if total > 0 else 0
        for cat, total, correct in category_performance_raw
    }

    # Performance Trend (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_scores = db.session.query(
        func.cast(TestResult.test_date, db.Date).label('date'),
        func.avg(TestResult.score * 100.0 / TestResult.total_questions).label('avg_score')
    ).filter(TestResult.test_date >= thirty_days_ago).group_by('date').order_by('date').all()

    trend_labels = [d.date.strftime('%b %d') for d in daily_scores]
    trend_data = [round(d.avg_score, 2) for d in daily_scores]

    analytics_data = {
        'total_tests': total_tests,
        'average_score': average_score,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'performance_by_category': category_performance,
        'performance_trend': {
            'labels': trend_labels,
            'data': trend_data
        }
    }
    
    return render_template('admin_analytics.html', data=analytics_data)

@app.route('/admin')
@login_required
def admin():
    # Simple admin check - in production, use proper role-based access
    if current_user.username != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Calculate statistics
    stats = {
        'total_users': User.query.count(),
        'premium_users': User.query.filter_by(is_subscriber=True).count(),
        'total_tests': TestResult.query.count(),
        'total_questions': Question.query.count(),
        'categories': TestCategory.query.count()
    }
    
    # Fetch recent activity
    recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin.html', stats=stats, recent_activity=recent_activity)

@app.route('/admin/questions')
@login_required
def admin_questions():
    if current_user.username != 'admin':
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    selected_category = request.args.get('category', 'all')
    search_query = request.args.get('search', '')

    # Base query
    query = Question.query

    # Apply filters
    if selected_category != 'all':
        # Find category by name
        test_category = TestCategory.query.filter_by(name=selected_category).first()
        if test_category:
            query = query.filter_by(category_id=test_category.id)
    
    if search_query:
        query = query.filter(Question.question_text.ilike(f'%{search_query}%'))

    # Order and paginate
    pagination = query.order_by(Question.created_date.desc()).paginate(page=page, per_page=10, error_out=False)
    questions = pagination.items
    
    # Get all categories for the filter dropdown
    all_categories = [cat.name for cat in TestCategory.query.order_by(TestCategory.name).all()]
    
    return render_template(
        'admin_questions.html', 
        questions=questions, 
        categories=all_categories, 
        pagination=pagination, 
        selected_category=selected_category,
        search_query=search_query
    )

@app.route('/admin/tests')
@login_required
def admin_tests():
    if current_user.username != 'admin':
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    configs = TestConfig.query.order_by(TestConfig.id.desc()).all()
    return render_template('admin_tests.html', test_configs=configs)

@app.route('/admin/files')
@login_required
def admin_files():
    if current_user.username != 'admin':
        flash('Access denied.')
        return redirect(url_for('dashboard'))
        
    page = request.args.get('page', 1, type=int)
    # Paginate files, 12 per page for a 3-column grid
    pagination = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).paginate(page=page, per_page=12, error_out=False)
    uploaded_files_page = pagination.items

    files = []
    for file in uploaded_files_page:
        files.append({
            'id': file.id,
            'name': file.original_filename,
            'type': file.file_type,
            'size': get_file_size_string(file.file_size),
            'uploaded': file.upload_date.strftime('%Y-%m-%d'),
            'path': file.file_path,
            'url': url_for('uploaded_file', filename=(f"images/{file.filename}" if file.file_type == 'image' else f"pdfs/{file.filename}"))
        })
    
    return render_template('admin_files.html', files=files, pagination=pagination)

# File upload routes
@app.route('/upload_files', methods=['POST'])
@login_required
def upload_files():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    uploaded_files = []
    
    # Handle image files
    if 'images' in request.files:
        image_files = request.files.getlist('images')
        for file in image_files:
            if file and file.filename and allowed_file(file.filename, 'image'):
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                
                # Save file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', unique_filename)
                file.save(file_path)
                
                # Save to database
                uploaded_file = UploadedFile(
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_type='image',
                    file_size=os.path.getsize(file_path),
                    uploaded_by=current_user.id
                )
                db.session.add(uploaded_file)
                uploaded_files.append(file.filename)
    
    # Handle PDF files
    if 'pdfs' in request.files:
        pdf_files = request.files.getlist('pdfs')
        for file in pdf_files:
            if file and file.filename and allowed_file(file.filename, 'pdf'):
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                
                # Save file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', unique_filename)
                file.save(file_path)
                
                # Save to database
                uploaded_file = UploadedFile(
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_type='pdf',
                    file_size=os.path.getsize(file_path),
                    uploaded_by=current_user.id
                )
                db.session.add(uploaded_file)
                uploaded_files.append(file.filename)
    
    db.session.commit()

    # Log this activity
    if uploaded_files:
        log_entry = ActivityLog(
            user_id=current_user.id,
            username=current_user.username,
            description=f"Uploaded {len(uploaded_files)} file(s): {', '.join(uploaded_files)}"
        )
        db.session.add(log_entry)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{len(uploaded_files)} files uploaded successfully',
        'files': uploaded_files
    })

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    file = UploadedFile.query.get_or_404(file_id)
    
    # Delete physical file
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500
    
    # Delete from database
    db.session.delete(file)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'File deleted successfully'})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API to start a test and retrieve randomized questions
@app.route('/api/test/start/<category>')
@login_required
def api_test_start(category):
    # Defaults; later can be sourced from TestConfig
    question_count = 25
    time_limit_seconds = 8 * 60

    if category == 'all':
        all_questions = Question.query.all()
    else:
        # Find category by name
        test_category = TestCategory.query.filter_by(name=category).first()
        if test_category:
            all_questions = Question.query.filter_by(category_id=test_category.id).all()
        else:
            all_questions = []

    if not all_questions:
        return jsonify({'questions': [], 'time_limit_seconds': time_limit_seconds, 'session_id': None})

    # Randomly select questions (fall back to available count)
    selected = random.sample(all_questions, k=min(question_count, len(all_questions)))

    # Build payload with image URLs if present
    def image_url_for(q: Question):
        if q.image_path:
            # If image_path is a bare filename, assume images folder; otherwise if it's a full path, try to infer
            filename = q.image_path.replace('\\', '/').split('/')[-1]
            return url_for('uploaded_file', filename=f"images/{filename}")
        return None

    questions_payload = []
    question_ids = []
    for q in selected:
        question_ids.append(q.id)
        
        # Get answer options for this question
        options = {}
        correct_answer = None
        for option in q.options:
            options[option.option_letter] = option.option_text
            if option.is_correct:
                correct_answer = option.option_letter
        
        questions_payload.append({
            'id': q.id,
            'text': q.question_text,
            'category': q.category.name if q.category else 'Unknown',
            'difficulty': q.difficulty,
            'options': options,
            'correct_answer': correct_answer,  # Include for validation
            'image_url': image_url_for(q)
        })

    # Create a TestSession
    session_rec = TestSession(
        user_id=current_user.id,
        started_at=datetime.utcnow(),
        question_ids=json.dumps(question_ids),
        time_limit_seconds=time_limit_seconds
    )
    db.session.add(session_rec)
    db.session.commit()

    return jsonify({
        'session_id': session_rec.id,
        'time_limit_seconds': time_limit_seconds,
        'questions': questions_payload
    })

# Question management routes
@app.route('/add_question', methods=['POST'])
@login_required
def add_question():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Find or create category
    category_name = data['category']
    category = TestCategory.query.filter_by(name=category_name).first()
    if not category:
        category = TestCategory(name=category_name, description=f"Questions about {category_name}")
        db.session.add(category)
        db.session.flush()  # Get the ID
    
    question = Question(
        question_text=data['text'],
        category_id=category.id,
        difficulty=data.get('difficulty', 'basic'),
        image_path=data.get('imagePath')
    )
    
    db.session.add(question)
    db.session.flush()  # Get the question ID
    
    # Add answer options
    options = [
        ('A', data['optionA']),
        ('B', data['optionB']),
        ('C', data['optionC']),
    ]
    if data.get('optionD'):
        options.append(('D', data['optionD']))
    
    correct_answer = data['correctAnswer']
    for letter, text in options:
        option = AnswerOption(
            question_id=question.id,
            option_text=text,
            option_letter=letter,
            is_correct=(letter == correct_answer)
        )
        db.session.add(option)
    
    db.session.commit()

    # Log this activity
    log_entry = ActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        description=f"Added new question (ID: {question.id}) to category: {category.name}"
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # Return the full question object so the UI can update dynamically
    return jsonify({
        'success': True,
        'message': 'Question added successfully',
        'question': {
            'id': question.id,
            'text': question.question_text,
            'optionA': data['optionA'],
            'optionB': data['optionB'],
            'optionC': data['optionC'],
            'optionD': data.get('optionD', ''),
            'correctAnswer': correct_answer,
            'category': category.name,
            'difficulty': question.difficulty,
            'image_path': question.image_path
        }
    })

@app.route('/update_question/<int:question_id>', methods=['PUT'])
@login_required
def update_question(question_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    question = Question.query.get_or_404(question_id)
    data = request.get_json()
    
    # Find or create category
    category_name = data['category']
    category = TestCategory.query.filter_by(name=category_name).first()
    if not category:
        category = TestCategory(name=category_name, description=f"Questions about {category_name}")
        db.session.add(category)
        db.session.flush()
    
    question.question_text = data['text']
    question.category_id = category.id
    question.difficulty = data.get('difficulty', 'basic')
    question.image_path = data.get('imagePath')
    
    # Delete existing options and create new ones
    AnswerOption.query.filter_by(question_id=question.id).delete()
    
    # Add new answer options
    options = [
        ('A', data['optionA']),
        ('B', data['optionB']),
        ('C', data['optionC']),
    ]
    if data.get('optionD'):
        options.append(('D', data['optionD']))
    
    correct_answer = data['correctAnswer']
    for letter, text in options:
        option = AnswerOption(
            question_id=question.id,
            option_text=text,
            option_letter=letter,
            is_correct=(letter == correct_answer)
        )
        db.session.add(option)
    
    db.session.commit()
    
    # Return the full question object so the UI can update dynamically
    return jsonify({
        'success': True,
        'message': 'Question updated successfully',
        'question': {
            'id': question.id,
            'text': question.question_text,
            'optionA': data['optionA'],
            'optionB': data['optionB'],
            'optionC': data['optionC'],
            'optionD': data.get('optionD', ''),
            'correctAnswer': correct_answer,
            'category': category.name,
            'difficulty': question.difficulty,
            'image_path': question.image_path
        }
    })

@app.route('/delete_question/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Question deleted successfully'
    })

@app.route('/admin/test_config', methods=['POST'])
@login_required
def create_test_config():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    new_config = TestConfig(
        name=data['name'],
        is_active=data.get('active', True),
        num_questions=data['questionCount'],
        time_limit=data['timeLimit'],
        categories=json.dumps(data.get('categories', [])),
        difficulty_distribution=json.dumps(data.get('difficulty', {}))
    )
    db.session.add(new_config)
    db.session.commit()

    # Log this activity
    log_entry = ActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        description=f"Created new test configuration: {new_config.name}"
    )
    db.session.add(log_entry)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Test configuration created.', 'test_config': {
        'id': new_config.id,
        'name': new_config.name,
        'active': new_config.is_active,
        'questions': new_config.num_questions,
        'time_limit': new_config.time_limit
    }})

@app.route('/admin/test_config/<int:test_id>', methods=['GET', 'PUT'])
@login_required
def manage_test_config(test_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    config = TestConfig.query.get_or_404(test_id)

    if request.method == 'GET':
        return jsonify({
            'id': config.id,
            'name': config.name,
            'active': config.is_active,
            'questionCount': config.num_questions,
            'timeLimit': config.time_limit,
            'categories': json.loads(config.categories or '[]'),
            'difficulty': json.loads(config.difficulty_distribution or '{}')
        })

    if request.method == 'PUT':
        data = request.get_json()
        config.name = data['name']
        config.is_active = data.get('active', config.is_active)
        config.num_questions = data['questionCount']
        config.time_limit = data['timeLimit']
        config.categories = json.dumps(data.get('categories', []))
        config.difficulty_distribution = json.dumps(data.get('difficulty', {}))
        db.session.commit()

        # Log this activity
        log_entry = ActivityLog(
            user_id=current_user.id,
            username=current_user.username,
            description=f"Updated test configuration: {config.name}"
        )
        db.session.add(log_entry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Test configuration updated.'})

@app.route('/admin/test_config/<int:test_id>/toggle', methods=['POST'])
@login_required
def toggle_test_config_status(test_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    config = TestConfig.query.get_or_404(test_id)
    config.is_active = not config.is_active
    db.session.commit()
    return jsonify({'success': True, 'new_status': config.is_active})

@app.route('/delete_test/<int:test_id>', methods=['DELETE'])
@login_required
def delete_test_config(test_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    config = TestConfig.query.get_or_404(test_id)
    db.session.delete(config)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Test configuration deleted.'})


@app.route('/api/pdfs')
@login_required
def get_pdfs():
    pdfs = UploadedFile.query.filter_by(file_type='pdf').order_by(UploadedFile.original_filename).all()
    
    pdf_list = [
        {
            'id': pdf.id,
            'name': pdf.original_filename,
            'url': url_for('download_pdf', file_id=pdf.id)
        }
        for pdf in pdfs
    ]
    
    return jsonify(pdf_list)

@app.route('/api/images')
@login_required
def get_images():
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    images = UploadedFile.query.filter_by(file_type='image').order_by(UploadedFile.original_filename).all()
    
    image_list = [
        {
            'name': image.original_filename,
            'path': image.file_path,
            'url': url_for('uploaded_file', filename=f"images/{image.filename}")
        }
        for image in images
    ]
    
    return jsonify(image_list)

@app.route('/get_question/<int:question_id>')
@login_required
def get_question(question_id):
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    question = Question.query.get_or_404(question_id)
    
    # Get answer options
    options = {}
    correct_answer = None
    for option in question.options:
        options[option.option_letter] = option.option_text
        if option.is_correct:
            correct_answer = option.option_letter
    
    return jsonify({
        'id': question.id,
        'text': question.question_text,
        'optionA': options.get('A', ''),
        'optionB': options.get('B', ''),
        'optionC': options.get('C', ''),
        'optionD': options.get('D', ''),
        'correctAnswer': correct_answer,
        'category': question.category.name if question.category else '',
        'difficulty': question.difficulty,
        'imagePath': question.image_path
    })

@app.cli.command("init-db")
def init_db_command():
    """Creates the database tables and populates them with initial data."""
    db.create_all()
    create_admin_user()
    load_questions()
    print("Database initialized.")

if __name__ == '__main__':
    app.run(debug=True)

