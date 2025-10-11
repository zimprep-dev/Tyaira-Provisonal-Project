# ☁️ Cloudinary Setup Guide - Fix Image/File Storage

## 🔍 The Problem

Your files are currently stored in the local filesystem (`uploads/` folder), which is **ephemeral on Render**:
- ❌ Files get deleted on every deployment
- ❌ Not suitable for production
- ❌ Images uploaded by users disappear

## ✅ The Solution: Cloudinary

Cloudinary provides persistent cloud storage with a generous free tier:
- ✅ **25GB storage** (free tier)
- ✅ **25GB bandwidth/month** (free tier)
- ✅ Automatic image optimization
- ✅ CDN delivery (fast worldwide)
- ✅ Perfect for images and PDFs

---

## 📋 Setup Steps

### Step 1: Create Cloudinary Account

1. Go to [cloudinary.com](https://cloudinary.com)
2. Click **"Sign Up Free"**
3. Fill in your details or sign up with Google/GitHub
4. Verify your email

### Step 2: Get Your Credentials

1. After login, you'll see your **Dashboard**
2. Find these credentials (top of dashboard):
   - **Cloud Name**: e.g., `dxxxxxxxxxxxx`
   - **API Key**: e.g., `123456789012345`
   - **API Secret**: e.g., `abcdefghijklmnopqrstuvwxyz123`

### Step 3: Add to Render Environment Variables

1. Go to **Render Dashboard** → Your web service
2. Click **"Environment"** tab
3. Add these 3 new environment variables:

| Key | Value | Example |
|-----|-------|---------|
| `CLOUDINARY_CLOUD_NAME` | Your cloud name | `dxxxxxxxxxxxx` |
| `CLOUDINARY_API_KEY` | Your API key | `123456789012345` |
| `CLOUDINARY_API_SECRET` | Your API secret | `abcdefghijklmnopqrstuvwxyz123` |

4. Click **"Save Changes"**
5. Render will automatically redeploy

---

## 🎯 What's Already Configured

The code has been updated to:

### ✅ Automatic Cloudinary Integration
- Detects if Cloudinary credentials are set
- Automatically uploads to Cloudinary if configured
- Falls back to local storage if not configured (for development)

### ✅ Database Updates
- `file_path` now stores URLs (500 chars)
- `image_path` in questions supports URLs (500 chars)
- New `cloudinary_public_id` field for file management

### ✅ File Upload Flow
```
User uploads file
    ↓
Check if Cloudinary configured?
    ↓ YES                    ↓ NO
Upload to Cloudinary    Save locally (dev mode)
    ↓                        ↓
Store URL in database   Store path in database
```

---

## 🧪 Testing

### After Adding Credentials:

1. **Wait for Render to redeploy** (~2-3 minutes)

2. **Test Image Upload**:
   - Login to admin dashboard
   - Go to **Files** → Upload an image
   - Image should upload to Cloudinary
   - URL will be like: `https://res.cloudinary.com/YOUR_CLOUD_NAME/...`

3. **Test Question with Image**:
   - Go to **Questions** → Add/Edit question
   - Upload an image
   - Image should display correctly
   - Image persists after redeployment

4. **Test PDF Upload**:
   - Upload a PDF document
   - Users should be able to download it
   - File persists after redeployment

---

## 📊 Cloudinary Dashboard

### View Your Files:
1. Go to [cloudinary.com/console](https://cloudinary.com/console)
2. Click **"Media Library"**
3. See all uploaded files organized by folders:
   - `question_images/` - Images for questions
   - `documents/` - PDF files

### Monitor Usage:
1. Dashboard shows:
   - Storage used
   - Bandwidth used
   - Number of transformations
   - Monthly quota

---

## 💰 Free Tier Limits

Cloudinary Free Tier includes:
- ✅ **25GB storage**
- ✅ **25GB bandwidth/month**
- ✅ **25,000 transformations/month**
- ✅ Unlimited images
- ✅ CDN delivery

**This is more than enough for your driving test platform!**

Estimated usage:
- 400 questions with images: ~200MB
- 50 PDF documents: ~100MB
- Monthly bandwidth: ~5-10GB (moderate traffic)

---

## 🔄 Migration Path

### For Existing Files (if any):

If you already have files uploaded locally that you want to keep:

1. **Download them from Render** (if still available)
2. **Re-upload via admin interface** after Cloudinary is configured
3. Files will automatically go to Cloudinary

### For New Deployments:
- ✅ All new uploads go directly to Cloudinary
- ✅ No manual migration needed

---

## 🐛 Troubleshooting

### Files Still Not Loading?

**Check Cloudinary Configuration:**
```bash
# In Render Shell:
python -c "import os; print('Cloud Name:', os.getenv('CLOUDINARY_CLOUD_NAME')); print('API Key:', os.getenv('CLOUDINARY_API_KEY')[:5] + '...' if os.getenv('CLOUDINARY_API_KEY') else 'Not set')"
```

**Verify Upload Works:**
```bash
# In Render Shell:
python -c "import file_storage; print('Cloudinary configured:', file_storage.is_cloudinary_configured())"
```

### Upload Fails?

1. **Check credentials are correct** (no extra spaces)
2. **Verify API secret is complete** (copy-paste carefully)
3. **Check Cloudinary dashboard** for error logs

### Images Show Broken?

1. **Check URL in database** - should start with `https://res.cloudinary.com/`
2. **Verify image exists in Cloudinary Media Library**
3. **Check browser console** for CORS or loading errors

---

## 🔒 Security Notes

### ✅ Credentials are Safe:
- Stored as environment variables (not in code)
- Not exposed to users
- Only server can access

### ✅ File Access:
- All files are publicly accessible via URL
- No authentication required to view
- This is normal for CDN-delivered content

### ⚠️ If You Need Private Files:
Cloudinary supports signed URLs for private content (upgrade required)

---

## 🚀 Next Steps

1. **✅ Create Cloudinary account**
2. **✅ Add credentials to Render**
3. **✅ Wait for deployment**
4. **✅ Test file uploads**
5. **✅ Verify images display correctly**
6. **✅ Upload question images**

---

## 📞 Support

### Cloudinary Documentation:
- [Getting Started](https://cloudinary.com/documentation)
- [Python SDK](https://cloudinary.com/documentation/python_integration)
- [Upload API](https://cloudinary.com/documentation/upload_images)

### Need Help?
- Cloudinary Support: [support.cloudinary.com](https://support.cloudinary.com)
- Free tier includes email support

---

## ✨ Benefits After Setup

Once Cloudinary is configured:

- ✅ **Persistent Storage** - Files never disappear
- ✅ **Fast Delivery** - CDN makes images load quickly worldwide
- ✅ **Automatic Optimization** - Images are compressed automatically
- ✅ **Scalable** - Handles traffic spikes easily
- ✅ **Professional** - Production-ready file management

**Your platform will be production-ready!** 🎉

---

## 🎯 Current Status

- ✅ Code updated to support Cloudinary
- ✅ Database migration created
- ✅ Fallback to local storage (for development)
- 🔄 **Waiting for Cloudinary credentials**

**Add the 3 environment variables to Render and you're done!**
