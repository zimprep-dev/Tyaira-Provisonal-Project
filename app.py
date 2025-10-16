from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Question, AnswerOption, TestResult, Answer, TestCategory, UploadedFile, TestSession, TestConfig, ActivityLog, SubscriptionPlan, PendingPayment, Transaction
from sqlalchemy import func
from datetime import datetime, timedelta
import random
import json
import os
import uuid
import file_storage
from dotenv import load_dotenv
from utils import is_mobile_device, get_device_type
from payment_handler import payment_handler

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/tyaira')

# Fix for Render's postgres:// vs postgresql:// URL format
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}

# Create upload directories if they don't exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'), exist_ok=True)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

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
    if not current_user.has_active_subscription() and len(current_user.tests_taken) >= 10:
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
    # Set subscription end date to 30 days from now (monthly subscription)
    current_user.subscription_end_date = datetime.utcnow() + relativedelta(months=1)
    db.session.commit()
    flash('Subscription activated! You now have unlimited access.')
    return redirect(url_for('dashboard'))

@app.route('/cancel_subscription', methods=['POST'])
@login_required
def cancel_subscription():
    if not current_user.is_subscriber:
        flash('You do not have an active subscription.')
        return redirect(url_for('dashboard'))
    
    # Cancel subscription but keep end date for grace period
    current_user.is_subscriber = False
    # Keep subscription_date and subscription_end_date for grace period access
    db.session.commit()
    
    if current_user.subscription_end_date:
        end_date_str = current_user.subscription_end_date.strftime('%B %d, %Y')
        flash(f'Your subscription has been cancelled. You will retain premium access until {end_date_str}.')
    else:
        flash('Your subscription has been cancelled.')
    
    return redirect(url_for('profile'))

@app.route('/download_pdf/<int:file_id>')
@login_required
def download_pdf(file_id):
    # Check if user has downloads left or is a subscriber
    FREE_DOWNLOAD_LIMIT = 3
    if not current_user.has_active_subscription() and current_user.downloads_count >= FREE_DOWNLOAD_LIMIT:
        flash(f'You have reached the free tier limit of {FREE_DOWNLOAD_LIMIT} downloads. Subscribe for unlimited downloads!', 'error')
        return redirect(url_for('dashboard'))

    file_to_download = UploadedFile.query.get_or_404(file_id)

    if file_to_download.file_type != 'pdf':
        flash('Invalid file type.')
        return redirect(url_for('dashboard'))

    # Increment download count for free users
    if not current_user.has_active_subscription():
        current_user.downloads_count += 1
        db.session.commit()
        
        # Show warning when approaching limit
        if current_user.downloads_count == 2:
            flash('You have 1 download remaining. Subscribe for unlimited downloads!', 'warning')
        elif current_user.downloads_count >= 3:
            flash('You have used all your free downloads. Subscribe for unlimited access!', 'warning')
    
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
        TestCategory.name,
        func.count(Answer.id).label('total'),
        func.sum(case((Answer.is_correct, 1), else_=0)).label('correct')
    ).join(Question, Question.category_id == TestCategory.id
    ).join(Answer, Answer.question_id == Question.id
    ).group_by(TestCategory.name).all()

    category_performance = {
        cat_name: round((correct / total) * 100, 2) if total > 0 else 0
        for cat_name, total, correct in category_performance_raw
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

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.username != 'admin':
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    # Get all users with their test statistics
    users = User.query.all()
    
    user_data = []
    for user in users:
        # Calculate user statistics
        tests_taken = TestResult.query.filter_by(user_id=user.id).count()
        
        if tests_taken > 0:
            # Average score
            avg_score_raw = db.session.query(
                func.avg(TestResult.score * 100.0 / TestResult.total_questions)
            ).filter(TestResult.user_id == user.id).scalar()
            avg_score = round(avg_score_raw, 2) if avg_score_raw else 0
            
            # Best score
            best_result = db.session.query(
                func.max(TestResult.score * 100.0 / TestResult.total_questions)
            ).filter(TestResult.user_id == user.id).scalar()
            best_score = round(best_result, 2) if best_result else 0
            
            # Last test date
            last_test = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.test_date.desc()).first()
            last_test_date = last_test.test_date if last_test else None
        else:
            avg_score = 0
            best_score = 0
            last_test_date = None
        
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_subscriber': user.is_subscriber,
            'subscription_date': user.subscription_date,
            'tests_taken': tests_taken,
            'avg_score': avg_score,
            'best_score': best_score,
            'downloads_count': user.downloads_count,
            'last_test_date': last_test_date
        })
    
    # Sort by tests taken (most active first)
    user_data.sort(key=lambda x: x['tests_taken'], reverse=True)
    
    # Summary statistics
    summary = {
        'total_users': len(users),
        'premium_users': sum(1 for u in user_data if u['is_subscriber']),
        'free_users': sum(1 for u in user_data if not u['is_subscriber']),
        'active_users': sum(1 for u in user_data if u['tests_taken'] > 0),
        'inactive_users': sum(1 for u in user_data if u['tests_taken'] == 0)
    }
    
    return render_template('admin_users.html', users=user_data, summary=summary)

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
                # Try Cloudinary first, fallback to local storage
                if file_storage.is_cloudinary_configured():
                    success, result = file_storage.upload_image(file, folder='question_images')
                    if success:
                        file_url = result
                        public_id = file_storage.get_public_id_from_url(file_url)
                    else:
                        flash(f'Error uploading {file.filename}: {result}', 'error')
                        continue
                else:
                    # Fallback to local storage
                    success, result = file_storage.save_local_file(file, app.config['UPLOAD_FOLDER'], 'images')
                    if success:
                        file_url = f"/uploads/{result}"
                        public_id = None
                    else:
                        flash(f'Error uploading {file.filename}: {result}', 'error')
                        continue
                
                # Save to database
                uploaded_file = UploadedFile(
                    filename=os.path.basename(file_url),
                    original_filename=file.filename,
                    file_path=file_url,
                    file_type='image',
                    file_size=0,  # Cloudinary doesn't provide size easily
                    uploaded_by=current_user.id,
                    cloudinary_public_id=public_id
                )
                db.session.add(uploaded_file)
                uploaded_files.append(file.filename)
    
    # Handle PDF files
    if 'pdfs' in request.files:
        pdf_files = request.files.getlist('pdfs')
        for file in pdf_files:
            if file and file.filename and allowed_file(file.filename, 'pdf'):
                # Try Cloudinary first, fallback to local storage
                if file_storage.is_cloudinary_configured():
                    success, result = file_storage.upload_pdf(file, folder='documents')
                    if success:
                        file_url = result
                        public_id = file_storage.get_public_id_from_url(file_url)
                    else:
                        flash(f'Error uploading {file.filename}: {result}', 'error')
                        continue
                else:
                    # Fallback to local storage
                    success, result = file_storage.save_local_file(file, app.config['UPLOAD_FOLDER'], 'pdfs')
                    if success:
                        file_url = f"/uploads/{result}"
                        public_id = None
                    else:
                        flash(f'Error uploading {file.filename}: {result}', 'error')
                        continue
                
                # Save to database
                uploaded_file = UploadedFile(
                    filename=os.path.basename(file_url),
                    original_filename=file.filename,
                    file_path=file_url,
                    file_type='pdf',
                    file_size=0,  # Cloudinary doesn't provide size easily
                    uploaded_by=current_user.id,
                    cloudinary_public_id=public_id
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
    # Check free tier limit (10 tests)
    FREE_TEST_LIMIT = 10
    if not current_user.has_active_subscription():
        tests_taken_count = TestResult.query.filter_by(user_id=current_user.id).count()
        if tests_taken_count >= FREE_TEST_LIMIT:
            return jsonify({
                'error': 'free_limit_reached',
                'message': f'You have reached the free tier limit of {FREE_TEST_LIMIT} tests. Subscribe for unlimited access!',
                'tests_taken': tests_taken_count,
                'limit': FREE_TEST_LIMIT
            }), 403
    
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
    print("Database initialized.")

# ===================================
# PAYMENT & SUBSCRIPTION ROUTES
# ===================================

@app.route('/subscription')
@login_required
def subscription_page():
    """Display subscription plans and user's current subscription"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.duration_days).all()
    
    # Get user's latest transaction
    latest_transaction = Transaction.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).order_by(Transaction.created_at.desc()).first()
    
    return render_template('subscription.html',
                         plans=plans,
                         latest_transaction=latest_transaction,
                         has_subscription=current_user.has_active_subscription())

@app.route('/subscribe/<int:plan_id>', methods=['POST'])
@login_required
def initiate_payment(plan_id):
    """Initiate payment for a subscription plan"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if not plan.is_active:
        flash('This subscription plan is not available', 'error')
        return redirect(url_for('subscription_page'))
    
    # Generate unique reference
    reference = f"TYA-{current_user.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create payment with Paynow
    result = payment_handler.create_payment(current_user, plan, reference)
    
    if result['success']:
        # Save pending payment in database
        pending = PendingPayment(
            user_id=current_user.id,
            payment_reference=reference,
            poll_url=result['poll_url'],
            amount=plan.price,
            currency=plan.currency,
            plan_id=plan.id,
            status='pending'
        )
        db.session.add(pending)
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            username=current_user.username,
            description=f"Initiated payment for {plan.name} subscription (${plan.price})"
        )
        db.session.add(log)
        db.session.commit()
        
        # Redirect user to Paynow payment page
        return redirect(result['payment_url'])
    else:
        flash(f"Payment initialization failed: {result.get('error', 'Unknown error')}", 'error')
        return redirect(url_for('subscription_page'))

@app.route('/payment/notify', methods=['POST', 'GET'])
def payment_notify():
    """
    Webhook endpoint for Paynow to send payment status updates
    This is called automatically by Paynow when payment status changes
    """
    try:
        # Get payment data from Paynow
        reference = request.values.get('reference')
        paynow_ref = request.values.get('paynowreference')
        status = request.values.get('status')
        amount = request.values.get('amount')
        hash_value = request.values.get('hash')
        
        if not reference:
            return 'Missing reference', 400
        
        # Verify and process payment
        success = payment_handler.verify_payment(
            reference=reference,
            status=status,
            paynow_reference=paynow_ref,
            hash_value=hash_value
        )
        
        if success:
            # Log the notification
            print(f"Payment notification processed: {reference} - {status}")
            return 'OK', 200
        else:
            return 'Payment verification failed', 400
            
    except Exception as e:
        print(f"Error processing payment notification: {e}")
        return 'Error', 500

@app.route('/payment/return')
@login_required
def payment_return():
    """
    User returns here after completing/cancelling payment on Paynow
    """
    reference = request.args.get('reference')
    
    if not reference:
        flash('Invalid payment reference', 'error')
        return redirect(url_for('subscription_page'))
    
    # Find the pending payment
    pending = PendingPayment.query.filter_by(
        payment_reference=reference,
        user_id=current_user.id
    ).first()
    
    if not pending:
        flash('Payment not found', 'error')
        return redirect(url_for('subscription_page'))
    
    # Check payment status with Paynow
    status_response = payment_handler.check_payment_status(pending.poll_url)
    status = status_response.get('status', '').lower()
    
    if status in ['paid', 'delivered', 'sent']:
        # Payment successful
        flash('Payment successful! Your subscription is now active.', 'success')
        return redirect(url_for('dashboard'))
    elif status in ['cancelled', 'failed']:
        # Payment failed
        flash('Payment was cancelled or failed. Please try again.', 'warning')
        return redirect(url_for('subscription_page'))
    else:
        # Payment pending
        flash('Payment is being processed. You will receive confirmation shortly.', 'info')
        return redirect(url_for('payment_status', reference=reference))

@app.route('/payment/status/<reference>')
@login_required
def payment_status(reference):
    """Check status of a pending payment"""
    pending = PendingPayment.query.filter_by(
        payment_reference=reference,
        user_id=current_user.id
    ).first()
    
    if not pending:
        flash('Payment not found', 'error')
        return redirect(url_for('subscription_page'))
    
    return render_template('payment_status.html', pending=pending)

@app.route('/payment/check/<reference>')
@login_required
def check_payment(reference):
    """AJAX endpoint to check payment status"""
    pending = PendingPayment.query.filter_by(
        payment_reference=reference,
        user_id=current_user.id
    ).first()
    
    if not pending:
        return jsonify({'error': 'Payment not found'}), 404
    
    # Check with Paynow
    status_response = payment_handler.check_payment_status(pending.poll_url)
    status = status_response.get('status', 'Unknown')
    
    return jsonify({
        'status': pending.status,
        'paynow_status': status,
        'amount': pending.amount,
        'plan_name': pending.plan.name if pending.plan else 'Unknown'
    })

@app.route('/payment/mock')
def mock_payment():
    """Mock payment page for testing (development only)"""
    if os.getenv('FLASK_ENV') == 'production':
        return 'Not available', 404
    
    reference = request.args.get('ref')
    return render_template('mock_payment.html', reference=reference)

@app.route('/payment/mock/complete', methods=['POST'])
def mock_payment_complete():
    """Complete mock payment (development only)"""
    if os.getenv('FLASK_ENV') == 'production':
        return 'Not available', 404
    
    reference = request.form.get('reference')
    action = request.form.get('action')  # 'pay' or 'cancel'
    
    if action == 'pay':
        # Simulate successful payment
        payment_handler.verify_payment(
            reference=reference,
            status='Paid',
            paynow_reference=f'MOCK-{reference}'
        )
        flash('Mock payment successful!', 'success')
    else:
        # Simulate cancelled payment
        payment_handler.verify_payment(
            reference=reference,
            status='Cancelled'
        )
        flash('Mock payment cancelled', 'warning')
    
    return redirect(url_for('payment_return', reference=reference))

@app.route('/transactions')
@login_required
def my_transactions():
    """View user's payment history"""
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.created_at.desc()).all()
    
    return render_template('transactions.html', transactions=transactions)

# Admin: Manage subscription plans
@app.route('/admin/plans')
@login_required
def admin_plans():
    """Admin page to manage subscription plans"""
    if current_user.username != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.duration_days).all()
    return render_template('admin_plans.html', plans=plans)

@app.route('/admin/plans/add', methods=['POST'])
@login_required
def admin_add_plan():
    """Add new subscription plan"""
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        plan = SubscriptionPlan(
            name=request.form.get('name'),
            duration_days=int(request.form.get('duration_days')),
            price=float(request.form.get('price')),
            currency=request.form.get('currency', 'USD'),
            description=request.form.get('description'),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(plan)
        db.session.commit()
        
        flash('Subscription plan added successfully', 'success')
        return redirect(url_for('admin_plans'))
    except Exception as e:
        flash(f'Error adding plan: {str(e)}', 'error')
        return redirect(url_for('admin_plans'))

@app.route('/admin/plans/edit/<int:plan_id>', methods=['POST'])
@login_required
def admin_edit_plan(plan_id):
    """Edit subscription plan"""
    if current_user.username != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    try:
        plan.name = request.form.get('name')
        plan.duration_days = int(request.form.get('duration_days'))
        plan.price = float(request.form.get('price'))
        plan.currency = request.form.get('currency', 'USD')
        plan.description = request.form.get('description')
        plan.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash('Plan updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating plan: {str(e)}', 'error')
    
    return redirect(url_for('admin_plans'))

@app.route('/admin/transactions')
@login_required
def admin_transactions():
    """Admin view of all transactions"""
    if current_user.username != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(100).all()
    
    # Calculate statistics
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'completed'
    ).scalar() or 0
    
    total_transactions = Transaction.query.filter_by(status='completed').count()
    pending_payments = PendingPayment.query.filter_by(status='pending').count()
    
    return render_template('admin_transactions.html',
                         transactions=transactions,
                         total_revenue=total_revenue,
                         total_transactions=total_transactions,
                         pending_payments=pending_payments)

if __name__ == '__main__':
    app.run(debug=True)

