# 🚗 Tyaira Driving Test Platform

A comprehensive web-based driving theory test platform with adaptive mobile/desktop interfaces, admin CMS, and analytics dashboard.

## ✨ Features

### **For Students**
- 📱 **Adaptive Interface** - Automatic mobile/desktop optimization
- ✅ **Practice Tests** - 25-question timed tests
- 🖼️ **Visual Questions** - Traffic diagrams and scenarios
- 📊 **Detailed Review** - See correct answers and explanations
- 📈 **Progress Tracking** - View test history and scores
- 📄 **Study Materials** - Download PDF resources

### **For Administrators**
- 🎛️ **Content Management** - Add/edit questions and categories
- 📸 **Image Upload** - Attach diagrams to questions
- 📁 **File Management** - Upload study materials
- 📊 **Analytics Dashboard** - Track user performance
- 👥 **User Management** - Monitor registrations and activity

### **Technical Features**
- 🔐 **Secure Authentication** - User login/registration
- 📱 **Mobile-First Design** - Touch-optimized interface
- 🗄️ **PostgreSQL Database** - Reliable data storage
- 🚀 **Production Ready** - Deployment guides included
- 🎨 **Modern UI** - Clean, professional design

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- PostgreSQL 12+
- pip or pipenv

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tyaira-driving-test.git
   cd tyaira-driving-test
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   ```

6. **Import questions**
   ```bash
   python import_questions.py
   ```

7. **Run the application**
   ```bash
   flask run
   ```

8. **Access the platform**
   - Open browser: `http://localhost:5000`
   - Register an account
   - Start taking tests!

---

## 📁 Project Structure

```
tyaira-driving-test/
├── app.py                      # Main application
├── utils.py                    # Helper functions
├── wsgi.py                     # Production server entry
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment configuration
├── .env.example               # Environment template
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── style.css          # Main styles
│   │   ├── mobile-test.css    # Mobile test styles
│   │   └── mobile-review.css  # Mobile review styles
│   └── js/
│       ├── test-interface.js  # Desktop test logic
│       └── mobile-test.js     # Mobile test logic
│
├── templates/                  # HTML templates
│   ├── base.html
│   ├── auth/                  # Login/register
│   ├── test/                  # Test interface
│   ├── admin/                 # CMS pages
│   └── mobile/                # Mobile templates
│
├── uploads/                    # User uploads
│   ├── images/                # Question images
│   └── pdfs/                  # Study materials
│
├── migrations/                 # Database migrations
└── docs/                      # Documentation
    ├── DEPLOYMENT.md          # Deployment guide
    └── API.md                 # API documentation
```

---

## 🎯 Usage

### **Taking a Test**
1. Login to your account
2. Click "Take Test"
3. Select test category or "Full Test"
4. Answer 25 questions within time limit
5. Submit and view results
6. Review answers with explanations

### **Admin Functions**
1. Login as admin (username: `admin`)
2. Access CMS from dashboard
3. Add/edit questions and categories
4. Upload images for questions
5. Manage study materials
6. View analytics

---

## 🔧 Configuration

### **Environment Variables**
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
FLASK_ENV=development
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
```

### **Database Setup**
```bash
# Create database
createdb tyaira

# Run migrations
flask db upgrade

# Import sample questions
python import_questions.py
```

### **Create Admin User**
```python
from app import db, User
from werkzeug.security import generate_password_hash

admin = User(
    username='admin',
    email='admin@example.com',
    password_hash=generate_password_hash('admin123')
)
db.session.add(admin)
db.session.commit()
```

---

## 🚀 Deployment

### **Recommended: Railway.app**
1. Push code to GitHub
2. Connect Railway to your repo
3. Add PostgreSQL service
4. Set environment variables
5. Deploy automatically

[Full deployment guide →](docs/DEPLOYMENT.md)

### **Other Options**
- **Heroku** - Easy deployment, free tier
- **DigitalOcean** - Full control, $6/month
- **Render** - Free tier with auto-deploy
- **AWS/GCP** - Enterprise scale

---

## 📱 Mobile Features

The platform automatically detects mobile devices and serves an optimized interface:

- ✅ Touch-friendly buttons (64px minimum)
- ✅ Simplified navigation
- ✅ Image zoom functionality
- ✅ Responsive design
- ✅ Landscape mode support
- ✅ Offline-ready (PWA capable)

---

## 🛠️ Tech Stack

### **Backend**
- Flask 3.0
- SQLAlchemy (ORM)
- PostgreSQL
- Flask-Login (Auth)
- Flask-Migrate (DB migrations)

### **Frontend**
- HTML5/CSS3
- Vanilla JavaScript
- Feather Icons
- Responsive CSS Grid/Flexbox

### **Deployment**
- Gunicorn (WSGI server)
- Nginx (Reverse proxy)
- Let's Encrypt (SSL)

---

## 📊 Database Schema

### **Main Tables**
- `users` - User accounts
- `test_categories` - Question categories
- `questions` - Test questions
- `answer_options` - Multiple choice options
- `test_results` - Completed tests
- `answers` - Individual answers
- `test_sessions` - Active test sessions
- `uploaded_files` - Study materials

---

## 🔒 Security Features

- ✅ Password hashing (Werkzeug)
- ✅ CSRF protection
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ XSS protection
- ✅ Secure session management
- ✅ File upload validation
- ✅ Environment variable secrets

---

## 🧪 Testing

```bash
# Run tests
python -m pytest

# Test mobile detection
python test_mobile.py

# Test API endpoints
python test_api.py
```

---

## 📈 Performance

- Database indexing on frequently queried fields
- Static file caching
- Gzip compression
- Lazy loading for images
- Optimized SQL queries

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/tyaira-driving-test/issues)
- **Email**: support@example.com

---

## 🎯 Roadmap

### **Version 2.0 (Planned)**
- [ ] PWA with offline mode
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Video explanations
- [ ] Gamification (badges, leaderboard)
- [ ] Mobile apps (React Native)
- [ ] AI-powered study recommendations

---

## 🙏 Acknowledgments

- Feather Icons for beautiful icons
- Flask community for excellent documentation
- All contributors and testers

---

**Made with ❤️ for driving students**

[Live Demo](https://tyaira-driving-test.railway.app) | [Documentation](docs/) | [Report Bug](https://github.com/yourusername/tyaira-driving-test/issues)
