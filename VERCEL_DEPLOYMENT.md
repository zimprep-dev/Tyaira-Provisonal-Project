# Vercel + Supabase Deployment Guide

## 🚀 **Overview**

Deploy your driving theory test platform on **Vercel** (hosting) + **Supabase** (PostgreSQL database).

### **Why Vercel + Supabase?**

**Pros:**
- ✅ **Global CDN** - Lightning fast worldwide
- ✅ **Automatic HTTPS** - Built-in SSL
- ✅ **Zero config** - Deploy with `vercel` command
- ✅ **Free tier** - Generous limits
- ✅ **Serverless** - Auto-scaling
- ✅ **Supabase free PostgreSQL** - 500MB database included

**Cons:**
- ⚠️ **Cold starts** - First request may be slow (serverless limitation)
- ⚠️ **10 second timeout** - Long-running operations limited
- ⚠️ **No persistent storage** - Use Cloudinary for uploads (already configured)

---

## 📋 **Prerequisites**

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **Supabase Account** - Sign up at [supabase.com](https://supabase.com)
3. **Vercel CLI** - Install globally:
   ```bash
   npm install -g vercel
   ```

---

## 🗄️ **Step 1: Set Up Supabase Database**

### **1.1 Create Supabase Project**

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Click **"New Project"**
3. Fill in details:
   - **Name:** `tyaira-driving-tests`
   - **Database Password:** (generate strong password - save it!)
   - **Region:** Choose closest to your users
4. Click **"Create new project"**
5. Wait 2-3 minutes for setup

### **1.2 Get Database Connection String**

1. In your Supabase project dashboard
2. Click **"Project Settings"** (gear icon)
3. Click **"Database"** in left sidebar
4. Find **"Connection string"** section
5. Select **"URI"** tab
6. Copy the connection string (looks like):
   ```
   postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
7. **Replace `[YOUR-PASSWORD]`** with your actual database password
8. **Add `?sslmode=require`** to the end:
   ```
   postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
   ```

### **1.3 Enable Required Extensions (Optional)**

In Supabase SQL Editor, run:
```sql
-- Enable UUID extension (if needed in future)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## 🔧 **Step 2: Configure Vercel Deployment**

### **2.1 Update App for Vercel Compatibility**

The app is already configured! Key files:

- ✅ `vercel.json` - Vercel configuration
- ✅ `api/index.py` - Serverless entry point
- ✅ `requirements.txt` - Python dependencies

### **2.2 Set Environment Variables**

Create `.env.production` (for reference, don't commit):

```bash
# Database
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require

# Flask
SECRET_KEY=your-production-secret-key-min-32-chars
FLASK_ENV=production

# Cloudinary (your existing credentials)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Paynow (your existing credentials)
PAYNOW_INTEGRATION_ID=your-id
PAYNOW_INTEGRATION_KEY=your-key

# Base URL (will be your-site.vercel.app)
BASE_URL=https://your-site.vercel.app
```

---

## 🚀 **Step 3: Deploy to Vercel**

### **3.1 Login to Vercel**

```bash
vercel login
```

Follow the authentication prompts.

### **3.2 First Deployment (Link Project)**

```bash
cd c:/Users/hp/Tyaira
vercel
```

You'll be asked:
1. **Set up and deploy?** → Yes
2. **Which scope?** → Your account
3. **Link to existing project?** → No
4. **Project name?** → `tyaira-driving-tests` (or your choice)
5. **Directory?** → `./` (press Enter)
6. **Override settings?** → No

Vercel will:
- Upload your code
- Install dependencies
- Deploy the app
- Give you a URL: `https://tyaira-driving-tests.vercel.app`

⚠️ **First deployment will fail** - we need to add environment variables!

### **3.3 Add Environment Variables**

**Option A: Via CLI (Recommended)**

```bash
# Database
vercel env add DATABASE_URL
# Paste your Supabase connection string
# Select: Production, Preview, Development

# Secret Key
vercel env add SECRET_KEY
# Enter your secret key
# Select: Production, Preview, Development

# Cloudinary
vercel env add CLOUDINARY_CLOUD_NAME
vercel env add CLOUDINARY_API_KEY
vercel env add CLOUDINARY_API_SECRET

# Paynow
vercel env add PAYNOW_INTEGRATION_ID
vercel env add PAYNOW_INTEGRATION_KEY

# Base URL
vercel env add BASE_URL
# Enter: https://your-site.vercel.app (use your actual Vercel URL)
```

**Option B: Via Dashboard**

1. Go to [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. Click your project
3. Click **"Settings"** tab
4. Click **"Environment Variables"**
5. Add each variable:
   - **Name:** `DATABASE_URL`
   - **Value:** Your Supabase connection string
   - **Environments:** Production ✓, Preview ✓, Development ✓
6. Repeat for all variables above

### **3.4 Redeploy with Environment Variables**

```bash
vercel --prod
```

This will:
- Redeploy with all environment variables
- Run database migrations (via `build.sh` if configured)
- Give you production URL

---

## 🗃️ **Step 4: Initialize Database**

### **4.1 Run Migrations**

After deployment, run migrations manually:

```bash
# Install Vercel CLI if not already
npm install -g vercel

# Run remote command
vercel env pull .env.vercel.production
# Then connect via Supabase SQL Editor and run:
```

**OR** use Supabase SQL Editor:

1. Go to Supabase Dashboard → **SQL Editor**
2. Run migration SQL manually (see Step 4.2)

### **4.2 Manual Migration SQL**

If automatic migrations don't work, run this SQL in Supabase:

```sql
-- Run each migration file in order:
-- 1. Initial migration (already done)
-- 2. Add subscription_end_date
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;

-- 3. Increase password hash
ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255);

-- 4. Update file storage
ALTER TABLE uploaded_file ALTER COLUMN file_path TYPE TEXT;

-- 5. Add payment models (check if tables exist first)
CREATE TABLE IF NOT EXISTS subscription_plan (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    plan_type VARCHAR(20),
    duration_days INTEGER NOT NULL,
    duration_months INTEGER,
    price FLOAT NOT NULL,
    currency VARCHAR(3),
    description TEXT,
    has_unlimited_tests BOOLEAN DEFAULT TRUE,
    test_credits INTEGER DEFAULT 0,
    max_tests_per_month INTEGER,
    has_download_access BOOLEAN DEFAULT TRUE,
    has_progress_tracking BOOLEAN DEFAULT TRUE,
    has_performance_analytics BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pending_payment (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id),
    plan_id INTEGER REFERENCES subscription_plan(id),
    poll_url TEXT NOT NULL,
    amount FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    paynow_reference VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS transaction (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id),
    plan_id INTEGER REFERENCES subscription_plan(id),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    paynow_reference VARCHAR(100),
    poll_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Add user and plan fields
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS subscription_plan_id INTEGER REFERENCES subscription_plan(id);
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- Update existing data
UPDATE "user" SET created_at = NOW() WHERE created_at IS NULL;
UPDATE "user" SET subscription_start_date = subscription_date WHERE is_subscriber = TRUE AND subscription_date IS NOT NULL;

UPDATE subscription_plan SET plan_type = 'subscription' WHERE plan_type IS NULL;
UPDATE subscription_plan SET duration_months = ROUND(duration_days / 30.0) WHERE duration_months IS NULL;
UPDATE subscription_plan SET has_unlimited_tests = TRUE WHERE has_unlimited_tests IS NULL;
UPDATE subscription_plan SET test_credits = 0 WHERE test_credits IS NULL;
UPDATE subscription_plan SET has_download_access = TRUE WHERE has_download_access IS NULL;
UPDATE subscription_plan SET has_progress_tracking = TRUE WHERE has_progress_tracking IS NULL;
UPDATE subscription_plan SET has_performance_analytics = TRUE WHERE has_performance_analytics IS NULL;
UPDATE subscription_plan SET is_featured = FALSE WHERE is_featured IS NULL;
```

### **4.3 Create Admin User**

Run in Supabase SQL Editor:

```sql
-- Create admin user (change password!)
INSERT INTO "user" (username, email, password_hash, is_subscriber, created_at)
VALUES (
    'admin',
    'admin@tyaira.com',
    'scrypt:32768:8:1$YourHashHere',  -- Generate with werkzeug.security.generate_password_hash('your-password')
    TRUE,
    NOW()
);
```

Or use Python to generate hash:
```python
from werkzeug.security import generate_password_hash
print(generate_password_hash('your-admin-password'))
```

### **4.4 Create Initial Plans**

Run in Supabase SQL Editor:

```sql
INSERT INTO subscription_plan (
    name, plan_type, duration_days, duration_months, price, currency, description,
    has_unlimited_tests, has_download_access, has_progress_tracking,
    has_performance_analytics, is_active, is_featured
) VALUES (
    'Premium Monthly',
    'subscription',
    30,
    1,
    5.00,
    'USD',
    'Monthly subscription - unlimited access to all driving theory tests',
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
);
```

---

## 🔄 **Step 5: Update & Redeploy**

### **For Future Updates:**

```bash
# Make your code changes
git add .
git commit -m "Your changes"
git push

# Deploy to production
vercel --prod
```

Vercel will automatically:
- Build your app
- Deploy to production
- Update the live site

---

## ⚙️ **Vercel Configuration Details**

### **vercel.json Explained:**

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",           // Entry point
      "use": "@vercel/python"    // Python runtime
    }
  ],
  "routes": [
    {
      "src": "/(.*)",            // All routes
      "dest": "app.py"           // Go to Flask app
    }
  ]
}
```

### **Serverless Limitations:**

- ⏱️ **10 second timeout** - Long operations will fail
- 💾 **50MB max response** - Large file downloads limited
- 🔄 **Stateless** - No persistent file storage (use Cloudinary)
- ❄️ **Cold starts** - First request after inactivity may be slow (1-3 seconds)

---

## 📊 **Comparison: Render vs Vercel**

| Feature | Render | Vercel + Supabase |
|---------|--------|-------------------|
| **Setup** | Easy | Easy |
| **Speed** | Good | Excellent (CDN) |
| **Database** | Built-in PostgreSQL | Supabase (separate) |
| **Free Tier** | 512MB RAM | Generous limits |
| **Cold Starts** | No (always on) | Yes (serverless) |
| **Request Timeout** | 30 seconds | 10 seconds |
| **File Storage** | Ephemeral | Ephemeral (use Cloudinary) |
| **Scaling** | Manual | Automatic |
| **Custom Domain** | Yes | Yes |
| **SSL** | Yes | Yes |
| **Best For** | Traditional apps | Modern jamstack |

---

## 🐛 **Troubleshooting**

### **Error: "No module named 'app'"**

- Check `api/index.py` exists
- Verify `vercel.json` configuration

### **Error: "Function execution timed out"**

- Vercel has 10 second limit
- Optimize slow operations
- Consider moving to Render for long tasks

### **Database Connection Failed**

- Check `DATABASE_URL` in Vercel dashboard
- Ensure `?sslmode=require` is in connection string
- Verify Supabase project is active

### **Cold Start Latency**

- First request after 5+ minutes will be slow
- Consider Render for always-on servers
- Or upgrade to Vercel Pro (keeps functions warm)

### **Static Files Not Loading**

- Use absolute URLs
- Cloudinary handles all uploads (already configured)
- CSS/JS should be in `static/` folder

---

## 🎯 **Testing Both Platforms**

Run both simultaneously:

- **Render:** `https://tyaira-provisonal-project.onrender.com`
- **Vercel:** `https://tyaira-driving-tests.vercel.app`

Compare:
1. ⚡ **Speed** - Which loads faster?
2. 🌍 **Global Performance** - Test from different locations
3. 💰 **Cost** - Which stays under free tier?
4. 🔧 **Maintenance** - Which is easier to manage?
5. 🐛 **Stability** - Which has fewer issues?

---

## 📝 **Quick Reference**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy (development)
vercel

# Deploy (production)
vercel --prod

# Check logs
vercel logs

# List environment variables
vercel env ls

# Pull environment variables locally
vercel env pull
```

---

## 🚀 **Next Steps**

1. ✅ Create Supabase project
2. ✅ Get database connection string
3. ✅ Deploy to Vercel
4. ✅ Add environment variables
5. ✅ Run database migrations
6. ✅ Create admin user
7. ✅ Test the site
8. ✅ Compare with Render

---

**Choose the platform that works best for your needs!** 🎉
