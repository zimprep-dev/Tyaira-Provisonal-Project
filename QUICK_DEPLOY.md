# ⚡ Quick Deploy to Render

## 1️⃣ Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

## 2️⃣ Go to Render
👉 https://render.com → Sign up with GitHub

## 3️⃣ Create Database
- Click **"New +"** → **"PostgreSQL"**
- Name: `tyaira-db`
- Click **"Create Database"**
- 📋 **Copy the Internal Database URL**

## 4️⃣ Create Web Service
- Click **"New +"** → **"Web Service"**
- Select your GitHub repo
- Name: `tyaira-driving-test`
- Build: `./build.sh`
- Start: `gunicorn wsgi:app`

## 5️⃣ Add Environment Variables
- `SECRET_KEY` → Click "Generate"
- `DATABASE_URL` → Paste from step 3
- `PYTHON_VERSION` → `3.11.5`

## 6️⃣ Deploy
Click **"Create Web Service"** → Wait 5-10 min ☕

## 7️⃣ Done! 🎉
Your site: `https://tyaira-driving-test.onrender.com`

**Login**: admin / admin123 (⚠️ change this!)

---

**Need more details?** See `RENDER_DEPLOYMENT.md`
