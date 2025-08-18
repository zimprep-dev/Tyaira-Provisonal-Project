# 🚗 Driver Testing Platform

A comprehensive web platform for Zimbabwe provisional driver testing exams, built with Python Flask.

## ✨ Features

- **Interactive Testing System**: Take timed driving tests with randomized questions
- **User Authentication**: Secure user registration and login system
- **Subscription Model**: Free tier (2 tests/day, 3 downloads) and Premium ($3/month unlimited)
- **Performance Tracking**: Monitor test scores and progress over time
- **Admin Panel**: Manage questions, users, and view platform statistics
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **PDF Downloads**: Access study materials and practice questions

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with responsive design

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project files**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## 📁 Project Structure

```
driver-testing-platform/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Landing page
│   ├── login.html       # User login
│   ├── register.html    # User registration
│   ├── dashboard.html   # User dashboard
│   ├── test.html        # Test taking interface
│   ├── admin.html       # Admin panel
│   └── profile.html     # User profile page
├── static/              # Static files
│   └── style.css       # Main stylesheet
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

The application uses these default configurations:

- **Secret Key**: `your-secret-key-change-this` (change in production!)
- **Database**: SQLite database (`driver_testing.db`)
- **Port**: 5000 (development)

### Customization

1. **Change Secret Key**: Edit `app.py` line 23
2. **Add More Questions**: Modify the `load_questions()` function in `app.py`
3. **Change Test Duration**: Edit the timer in `templates/test.html`
4. **Modify Pricing**: Update subscription details in templates

## 👥 User Roles

### Free Tier Users
- 2 tests per day
- 3 PDF downloads
- Basic performance tracking

### Premium Subscribers ($3/month)
- Unlimited tests
- Unlimited PDF downloads
- Full performance analytics
- Priority support

### Admin Users
- Access to admin panel (`/admin`)
- Manage questions and users
- View platform statistics
- Username must be "admin" (simple check)

## 📊 Database Models

### User
- Basic info (username, email, password)
- Subscription status
- Download count
- Test results relationship

### Question
- Question text and options (A, B, C)
- Correct answer
- Category classification

### TestResult
- User test scores
- Time taken
- Test date

## 🎯 Usage Examples

### Taking a Test
1. Login to your account
2. Click "Take Test" from dashboard
3. Answer 5 questions within 15 minutes
4. Submit to see your score

### Admin Functions
1. Login as user "admin"
2. Access `/admin` route
3. Manage questions, users, and view stats

### User Profile
1. Click "Profile" in navigation
2. View test history and statistics
3. Filter results by date or performance

## 🔒 Security Features

- Password hashing with Werkzeug
- User session management
- Route protection with `@login_required`
- Admin access control

## 🚧 Development Notes

### Adding New Questions
```python
# In app.py, modify load_questions() function
sample_questions = [
    {
        "question_text": "Your question here?",
        "option_a": "Option A text",
        "option_b": "Option B text", 
        "option_c": "Option C text",
        "correct_answer": "A",  # or "B" or "C"
        "category": "Category Name"
    }
]
```

### Database Operations
```python
# Create new user
user = User(username="newuser", email="user@example.com", password_hash=generate_password_hash("password"))
db.session.add(user)
db.session.commit()

# Query questions
questions = Question.query.filter_by(category="Traffic Signs").all()
```

## 🌐 Production Deployment

### Recommended Steps
1. **Change Secret Key**: Use a strong, random secret key
2. **Database**: Consider PostgreSQL for production
3. **Web Server**: Use Gunicorn or uWSGI with Nginx
4. **Environment**: Set `FLASK_ENV=production`
5. **HTTPS**: Enable SSL/TLS certificates
6. **Payment Integration**: Integrate real payment processor

### Environment Variables
```bash
export FLASK_ENV=production
export SECRET_KEY=your-super-secret-key-here
export DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## 🐛 Troubleshooting

### Common Issues

**Database errors**: Delete `driver_testing.db` and restart
**Import errors**: Ensure all requirements are installed
**Port conflicts**: Change port in `app.py` or kill existing processes

### Debug Mode
The app runs in debug mode by default. For production, remove or set `debug=False`.

## 📈 Future Enhancements

- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Email notifications
- [ ] Advanced analytics and reporting
- [ ] Question image support
- [ ] Mobile app development
- [ ] Multi-language support
- [ ] Social login (Google, Facebook)
- [ ] API endpoints for mobile apps

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 📞 Support

For support or questions:
- Create an issue in the project repository
- Contact the development team

---

**Built with ❤️ for Zimbabwe's driving community**

*This platform helps individuals prepare for their provisional driver testing exams through interactive practice tests and study resources.*











