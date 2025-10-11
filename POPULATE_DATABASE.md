# 📚 Database Population Guide - Import 400 Questions

Your site is now live! Here's how to populate it with the 400 driving test questions.

---

## ✅ Automatic Import (RECOMMENDED)

**The build script now automatically imports questions on deployment!**

### What Happens:
1. ✅ Render detects the new push
2. ✅ Runs `build.sh`
3. ✅ Checks if database has questions
4. ✅ If empty, automatically runs `import_questions.py`
5. ✅ Imports all 400 questions with categories

### Status Check:
Watch the Render deployment logs to see:
```
📚 Importing driving test questions...
📥 No questions found. Running import script...
Starting question import...
Parsed 400 questions from markdown file
Created 15 categories
Successfully imported 400 questions!
```

**The import will happen automatically in ~2-3 minutes!**

---

## 🔍 Verify Import Success

### Option 1: Via Admin Dashboard
1. Go to your live site: `https://your-app.onrender.com`
2. Login with admin credentials:
   - Username: `admin`
   - Password: `admin123`
3. Go to **Admin Dashboard** → **Questions**
4. You should see 400 questions listed

### Option 2: Via Render Shell
```bash
# In Render Dashboard → Shell tab:
python -c "from app import app, db; from models import Question; app.app_context().push(); print(f'Total questions: {Question.query.count()}')"
```

---

## 🛠️ Manual Import (If Needed)

If automatic import fails or you need to re-import:

### Via Render Shell:
1. Go to **Render Dashboard** → Your web service
2. Click **"Shell"** tab
3. Run:
```bash
python import_questions.py
```

### Expected Output:
```
Starting question import...
Clearing existing questions...
Parsed 400 questions from markdown file
Created 15 categories
Imported 50 questions...
Imported 100 questions...
Imported 150 questions...
Imported 200 questions...
Imported 250 questions...
Imported 300 questions...
Imported 350 questions...
Imported 400 questions...
Successfully imported 400 questions!

Import Summary:
Total Questions: 400
Total Categories: 15
Total Answer Options: 1200

Categories created:
- Traffic Signs and Signals: 123 questions
- Right of Way: 131 questions
- General Rules: 85 questions
- Speed Limits: 12 questions
- Parking Rules: 8 questions
- Motorcycles and Bicycles: 6 questions
- Accidents and Emergencies: 5 questions
- Night Driving: 4 questions
- Vehicle Equipment: 7 questions
- Road Markings: 9 questions
- Heavy Vehicles: 3 questions
- Licensing: 2 questions
- Impaired Driving: 1 questions
- Pedestrians: 2 questions
- Intersections: 2 questions
```

---

## 📊 What Gets Imported

### Questions:
- **Total**: 400 questions
- **Format**: 3-option multiple choice (A, B, C)
- **Categories**: 15 auto-categorized
- **Difficulty**: All marked as "basic" (can be edited later)

### Categories:
1. **Traffic Signs and Signals** (123 questions)
2. **Right of Way** (131 questions)
3. **General Rules** (85 questions)
4. **Speed Limits** (12 questions)
5. **Parking Rules** (8 questions)
6. **Motorcycles and Bicycles** (6 questions)
7. **Accidents and Emergencies** (5 questions)
8. **Night Driving** (4 questions)
9. **Vehicle Equipment** (7 questions)
10. **Road Markings** (9 questions)
11. **Heavy Vehicles** (3 questions)
12. **Licensing** (2 questions)
13. **Impaired Driving** (1 question)
14. **Pedestrians** (2 questions)
15. **Intersections** (2 questions)

---

## 🔄 Re-Import Questions

If you need to clear and re-import:

### Via Render Shell:
```bash
# This will delete all existing questions and re-import
python import_questions.py
```

**⚠️ Warning**: This deletes all existing questions, test results, and user answers!

### Safe Re-Import (Keep Test Results):
If you want to keep test history, manually delete questions via admin interface first.

---

## 🧪 Test the System

After import, test the complete flow:

### 1. Take a Test
- Go to **"Take Test"**
- Should see 25 random questions
- Timer should work (30 minutes default)
- All options should display correctly

### 2. Check Results
- Submit test
- View score and review
- Correct/incorrect answers should be marked properly

### 3. Admin Functions
- View all questions in admin dashboard
- Edit questions
- Add new questions
- Manage categories

---

## 🐛 Troubleshooting

### Import Script Not Found
```bash
# Verify files exist:
ls -la import_questions.py driving_test_answers.md
```

### No Questions Imported
Check logs for errors:
```bash
# In Render Shell:
python import_questions.py 2>&1 | tee import_log.txt
```

### Database Connection Error
Verify environment variables:
```bash
# In Render Shell:
echo $DATABASE_URL
```

### Questions Show But No Options
This means the import partially failed. Re-run:
```bash
python import_questions.py
```

---

## 📈 Next Steps After Import

1. **✅ Verify all 400 questions imported**
2. **✅ Take a sample test**
3. **✅ Check question display and formatting**
4. **✅ Review categories in admin dashboard**
5. **✅ Test mobile interface**
6. **✅ Add images to relevant questions (optional)**
7. **✅ Configure test settings (questions per test, timer)**

---

## 🎯 Current Status

- ✅ Site is live on Render
- ✅ Database is connected
- ✅ Admin user created
- ✅ Automatic import configured
- 🔄 **Questions importing now...**

**Check your Render deployment logs to confirm import success!**

The import should complete in the next 2-3 minutes as part of the current deployment.

---

## 📞 Need Help?

If import fails:
1. Check Render deployment logs
2. Try manual import via Shell
3. Verify `driving_test_answers.md` is in repository
4. Check database connection

**Your database will be populated automatically!** 🎉
