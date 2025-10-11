# ✅ Render Deployment Checklist

## Before You Deploy

- [x] Updated `requirements.txt` with python-dateutil
- [x] Updated `app.py` to use environment variables
- [x] Created `build.sh` build script
- [x] Created `render.yaml` configuration
- [x] Created deployment documentation

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Create Render Account
- Go to https://render.com
- Sign up with GitHub

### 3. Create PostgreSQL Database
- Click "New +" → "PostgreSQL"
- Name: `tyaira-db`
- Plan: Free
- Copy the **Internal Database URL**

### 4. Create Web Service
- Click "New +" → "Web Service"
- Connect your GitHub repo
- Name: `tyaira-driving-test`
- Build Command: `./build.sh`
- Start Command: `gunicorn wsgi:app`
- Plan: Free

### 5. Set Environment Variables
Add these in the Environment section:
- `SECRET_KEY`: Click "Generate"
- `DATABASE_URL`: Paste Internal Database URL
- `PYTHON_VERSION`: `3.11.5`

### 6. Deploy
- Click "Create Web Service"
- Wait 5-10 minutes

### 7. After Deployment
- [ ] Test the site at your Render URL
- [ ] Login as admin (username: `admin`, password: `admin123`)
- [ ] Change admin password immediately
- [ ] Test user registration
- [ ] Test taking a test
- [ ] Verify mobile interface works

## Your Site Will Be Live At:
`https://tyaira-driving-test.onrender.com`

## Default Admin Credentials
**⚠️ CHANGE THESE IMMEDIATELY AFTER FIRST LOGIN**
- Username: `admin`
- Password: `admin123`

## Next Steps (After Site is Live)
1. Import 400 driving test questions
2. Upload question images
3. Test all features thoroughly
4. Set up custom domain (optional)
5. Configure monitoring

## Need Help?
See `RENDER_DEPLOYMENT.md` for detailed instructions and troubleshooting.
