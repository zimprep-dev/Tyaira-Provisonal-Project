# 🚀 Render Deployment Guide - Tyaira Driving Theory Test

## ✅ Pre-Deployment Checklist

Your project is now ready for Render deployment with:
- ✅ Environment variable configuration
- ✅ PostgreSQL database support
- ✅ Automated build script
- ✅ Production-ready dependencies
- ✅ Gunicorn WSGI server

---

## 📋 Quick Deploy Steps

### **Option 1: Deploy via Render Dashboard (Recommended)**

#### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended for auto-deploy)
3. Verify your email

#### Step 2: Push Code to GitHub
```bash
# If not already a git repository
git init
git add .
git commit -m "Ready for Render deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/tyaira-driving-test.git
git branch -M main
git push -u origin main
```

#### Step 3: Create PostgreSQL Database
1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `tyaira-db`
   - **Database**: `tyaira`
   - **User**: `tyaira_user` (auto-generated)
   - **Region**: Choose closest to your users
   - **Plan**: **Free** (for testing)
3. Click **"Create Database"**
4. **IMPORTANT**: Copy the **Internal Database URL** (you'll need this)

#### Step 4: Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `tyaira-driving-test`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: **Python 3**
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn wsgi:app`
   - **Plan**: **Free** (for testing)

#### Step 5: Set Environment Variables
In the **Environment** section, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Click "Generate" or use a random string |
| `DATABASE_URL` | Paste the Internal Database URL from Step 3 |
| `PYTHON_VERSION` | `3.11.5` |

#### Step 6: Deploy
1. Click **"Create Web Service"**
2. Render will automatically:
   - Install dependencies
   - Run database migrations
   - Create admin user
   - Start the application
3. Wait 5-10 minutes for first deployment

#### Step 7: Access Your Site
- Your site will be available at: `https://tyaira-driving-test.onrender.com`
- Admin login:
  - **Username**: `admin`
  - **Password**: `admin123`
  - ⚠️ **CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN**

---

### **Option 2: Deploy via render.yaml (Infrastructure as Code)**

If you want to deploy everything with one click:

1. Push your code to GitHub (including `render.yaml`)
2. In Render Dashboard, click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will automatically create:
   - PostgreSQL database
   - Web service
   - All environment variables
5. Click **"Apply"**

---

## 🔧 Post-Deployment Tasks

### 1. Change Admin Password
```python
# In Render Shell (Dashboard → Shell tab):
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.password_hash = generate_password_hash('YOUR_NEW_SECURE_PASSWORD')
    db.session.commit()
    print('Password updated!')
```

### 2. Import Questions (Optional)
If you want to import the 400 driving test questions:

```bash
# In Render Shell:
python import_questions.py
```

### 3. Test Everything
- [ ] User registration
- [ ] User login
- [ ] Take a test
- [ ] View test results
- [ ] Admin dashboard
- [ ] Upload images/PDFs
- [ ] Mobile interface

---

## 🗄️ Database Management

### Access Database
1. Go to your database in Render Dashboard
2. Click **"Connect"** → **"External Connection"**
3. Use provided credentials with any PostgreSQL client

### Backup Database
```bash
# From Render Shell or locally with connection string:
pg_dump $DATABASE_URL > backup.sql
```

### Run Migrations
```bash
# In Render Shell:
flask db upgrade
```

---

## 🔄 Continuous Deployment

Render automatically redeploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Render will automatically:
# 1. Detect the push
# 2. Run build.sh
# 3. Deploy new version
# 4. Zero-downtime deployment
```

---

## 📊 Monitoring & Logs

### View Logs
1. Go to your web service in Render Dashboard
2. Click **"Logs"** tab
3. Real-time logs of your application

### Metrics
1. Click **"Metrics"** tab
2. View:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

---

## 💰 Pricing & Limits

### Free Tier Includes:
- ✅ 750 hours/month (enough for 1 service)
- ✅ Automatic SSL
- ✅ Custom domains
- ✅ Auto-deploy from Git
- ⚠️ Services spin down after 15 min of inactivity
- ⚠️ 90-second startup time after inactivity

### Upgrade to Paid ($7/month):
- ✅ No spin down
- ✅ Faster builds
- ✅ More resources
- ✅ Better performance

---

## 🔒 Security Checklist

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY (auto-generated by Render)
- [ ] Enable HTTPS (automatic on Render)
- [ ] Review uploaded files regularly
- [ ] Monitor user activity
- [ ] Set up database backups

---

## 🌐 Custom Domain (Optional)

### Add Custom Domain
1. Go to your web service
2. Click **"Settings"** → **"Custom Domains"**
3. Add your domain (e.g., `tyaira.com`)
4. Update DNS records:
   ```
   Type: CNAME
   Name: www (or @)
   Value: tyaira-driving-test.onrender.com
   ```
5. SSL certificate auto-provisioned

---

## 🐛 Troubleshooting

### Build Fails
```bash
# Check build.sh has execute permissions
chmod +x build.sh
git add build.sh
git commit -m "Fix build.sh permissions"
git push
```

### Database Connection Error
- Verify DATABASE_URL is set correctly
- Check database is in same region as web service
- Use **Internal Database URL** (not External)

### App Won't Start
- Check logs for errors
- Verify all environment variables are set
- Ensure `gunicorn` is in requirements.txt

### Slow Performance (Free Tier)
- Service spins down after 15 min inactivity
- First request after spin down takes ~90 seconds
- Upgrade to paid plan for always-on service

---

## 📞 Support Resources

- **Render Docs**: [docs.render.com](https://docs.render.com)
- **Render Community**: [community.render.com](https://community.render.com)
- **Flask Deployment**: [flask.palletsprojects.com/deploying](https://flask.palletsprojects.com/deploying/)

---

## 🎯 Next Steps

1. **Deploy the site** using Option 1 above
2. **Test thoroughly** on the live URL
3. **Import questions** if needed
4. **Configure custom domain** (optional)
5. **Set up monitoring** (UptimeRobot, etc.)
6. **Plan database migration** (we'll handle this next)

---

## ✨ What's Configured

Your deployment includes:

### Application
- Flask web framework
- Gunicorn WSGI server
- Environment-based configuration
- Automatic HTTPS/SSL

### Database
- PostgreSQL database
- Flask-Migrate for migrations
- Automatic schema creation
- Admin user auto-creation

### Features
- User authentication
- Test taking system (25 questions, timed)
- Admin CMS
- Image/PDF uploads
- Mobile-responsive design
- Test results & review
- Subscription system

---

**Ready to deploy!** 🚀

Follow **Option 1** above to get your site live in ~10 minutes.

After deployment, we'll handle the database setup and question import.
