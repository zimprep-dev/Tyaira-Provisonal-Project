from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_subscriber = db.Column(db.Boolean, default=False)
    subscription_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)  # When subscription access ends
    tests_taken = db.relationship('TestResult', backref='user', lazy=True)
    downloads_count = db.Column(db.Integer, default=0)
    
    def has_active_subscription(self):
        """Check if user has an active subscription (including grace period after cancellation)"""
        if not self.is_subscriber and not self.subscription_end_date:
            return False
        
        # If subscription is active
        if self.is_subscriber:
            return True
        
        # If subscription was cancelled but still within the paid period
        if self.subscription_end_date and datetime.utcnow() < self.subscription_end_date:
            return True
        
        return False

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
    image_path = db.Column(db.String(500))  # Now stores URL or local path
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
    file_path = db.Column(db.String(500), nullable=False)  # Now stores URL or local path
    file_type = db.Column(db.String(20), nullable=False)  # 'image' or 'pdf'
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cloudinary_public_id = db.Column(db.String(300))  # For Cloudinary file management

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

# Payment Models
class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "1 Month", "3 Months", "12 Months"
    duration_days = db.Column(db.Integer, nullable=False)  # 30, 90, 365
    price = db.Column(db.Float, nullable=False)  # in USD
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PendingPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_reference = db.Column(db.String(100), unique=True, nullable=False)
    poll_url = db.Column(db.String(500))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'))
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled, expired
    paynow_reference = db.Column(db.String(100))  # Paynow's internal reference
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='pending_payments')
    plan = db.relationship('SubscriptionPlan', backref='pending_payments')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    reference = db.Column(db.String(100), unique=True, nullable=False)
    paynow_reference = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False)  # completed, failed, refunded, disputed
    payment_method = db.Column(db.String(50), default='paynow')
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'))
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='transactions')
    plan = db.relationship('SubscriptionPlan', backref='transactions')
