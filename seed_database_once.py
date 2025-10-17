"""
One-time database seeding script for Tyaira Driving Theory Test
Populates the database with questions from driving_test_answers.md
"""

import re
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def seed_database(database_url):
    """Populate database with questions from markdown file"""
    
    print("🚀 Starting database seeding process...")
    print(f"📡 Connecting to database...")
    
    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Test connection
        session.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Add missing columns if they don't exist - COMPREHENSIVE CHECK
        print("\n🔧 Checking and fixing database schema for ALL tables...")
        try:
            # USER table
            session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_date TIMESTAMP"))
            session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP"))
            session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP"))
            session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_plan_id INTEGER"))
            session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS downloads_count INTEGER DEFAULT 0"))
            print("   ✅ User table schema updated")
            
            # QUESTION table
            session.execute(text("ALTER TABLE question ADD COLUMN IF NOT EXISTS difficulty VARCHAR(20) DEFAULT 'basic'"))
            session.execute(text("ALTER TABLE question ADD COLUMN IF NOT EXISTS image_path VARCHAR(500)"))
            session.execute(text("ALTER TABLE question ADD COLUMN IF NOT EXISTS created_date TIMESTAMP DEFAULT NOW()"))
            print("   ✅ Question table schema updated")
            
            # ANSWER_OPTION table - Fix option_letter and option_label columns
            # Check for option_letter column
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='answer_option' AND column_name='option_letter'
            """))
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                # Column doesn't exist, add it
                session.execute(text("ALTER TABLE answer_option ADD COLUMN option_letter VARCHAR(1) DEFAULT 'A'"))
            else:
                # Column exists, make sure it doesn't have NOT NULL constraint and has default
                session.execute(text("ALTER TABLE answer_option ALTER COLUMN option_letter DROP NOT NULL"))
                session.execute(text("ALTER TABLE answer_option ALTER COLUMN option_letter SET DEFAULT 'A'"))
                # Update any NULL values
                session.execute(text("UPDATE answer_option SET option_letter = 'A' WHERE option_letter IS NULL"))
            
            # Check for option_label column and handle it
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='answer_option' AND column_name='option_label'
            """))
            label_exists = result.fetchone() is not None
            
            if label_exists:
                # option_label exists - remove NOT NULL constraint or set default
                try:
                    session.execute(text("ALTER TABLE answer_option ALTER COLUMN option_label DROP NOT NULL"))
                except:
                    pass
                try:
                    session.execute(text("ALTER TABLE answer_option ALTER COLUMN option_label SET DEFAULT 'A'"))
                except:
                    pass
                # Update any NULL values
                try:
                    session.execute(text("UPDATE answer_option SET option_label = 'A' WHERE option_label IS NULL"))
                except:
                    pass
            
            print("   ✅ Answer option table schema updated")
            
            # TEST_RESULT table
            session.execute(text("ALTER TABLE test_result ADD COLUMN IF NOT EXISTS time_taken INTEGER"))
            print("   ✅ Test result table schema updated")
            
            # ACTIVITY_LOG table
            session.execute(text("ALTER TABLE activity_log ADD COLUMN IF NOT EXISTS username VARCHAR(80)"))
            print("   ✅ Activity log table schema updated")
            
            # TRANSACTION table
            session.execute(text("ALTER TABLE transaction ADD COLUMN IF NOT EXISTS reference VARCHAR(100)"))
            session.execute(text("ALTER TABLE transaction ADD COLUMN IF NOT EXISTS subscription_start TIMESTAMP"))
            session.execute(text("ALTER TABLE transaction ADD COLUMN IF NOT EXISTS subscription_end TIMESTAMP"))
            session.execute(text("ALTER TABLE transaction ADD COLUMN IF NOT EXISTS notes TEXT"))
            print("   ✅ Transaction table schema updated")
            
            # PENDING_PAYMENT table
            session.execute(text("ALTER TABLE pending_payment ADD COLUMN IF NOT EXISTS payment_reference VARCHAR(100)"))
            session.execute(text("ALTER TABLE pending_payment ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD'"))
            session.execute(text("ALTER TABLE pending_payment ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()"))
            print("   ✅ Pending payment table schema updated")
            
            # SUBSCRIPTION_PLAN table
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS plan_type VARCHAR(20) DEFAULT 'subscription'"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS duration_months INTEGER DEFAULT 1"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_unlimited_tests BOOLEAN DEFAULT TRUE"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS test_credits INTEGER DEFAULT 0"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS max_tests_per_month INTEGER"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_download_access BOOLEAN DEFAULT TRUE"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_progress_tracking BOOLEAN DEFAULT TRUE"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_performance_analytics BOOLEAN DEFAULT TRUE"))
            session.execute(text("ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE"))
            print("   ✅ Subscription plan table schema updated")
            
            # UPLOADED_FILE table
            session.execute(text("ALTER TABLE uploaded_file ADD COLUMN IF NOT EXISTS cloudinary_public_id VARCHAR(300)"))
            print("   ✅ Uploaded file table schema updated")
            
            # TEST_SESSION table
            session.execute(text("ALTER TABLE test_session ADD COLUMN IF NOT EXISTS time_limit_seconds INTEGER DEFAULT 1800"))
            print("   ✅ Test session table schema updated")
            
            # TEST_CONFIG table
            session.execute(text("ALTER TABLE test_config ADD COLUMN IF NOT EXISTS categories TEXT"))
            session.execute(text("ALTER TABLE test_config ADD COLUMN IF NOT EXISTS difficulty_distribution TEXT"))
            print("   ✅ Test config table schema updated")
            
            session.commit()
            print("\n✅ ALL DATABASE SCHEMAS UPDATED SUCCESSFULLY!")
            
        except Exception as e:
            print(f"\n⚠️  Schema check warning: {e}")
            session.rollback()
        
        # Clear existing data
        print("\n🗑️  Clearing existing questions and categories...")
        session.execute(text("DELETE FROM answer_option"))
        session.execute(text("DELETE FROM question"))
        session.execute(text("DELETE FROM test_category"))
        session.commit()
        print("✅ Existing data cleared!")
        
        # Read markdown file
        print("\n📖 Reading questions from driving_test_answers.md...")
        try:
            with open('driving_test_answers.md', 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print("❌ Error: 'driving_test_answers.md' not found!")
            print("   Please ensure the file is in the same directory as this script.")
            return False
        
        # Parse tests/categories
        tests = re.split(r'(?=## Test \d+)', content)
        if not tests[0].strip():
            tests = tests[1:]
        
        total_questions = 0
        total_categories = 0
        
        for test_block in tests:
            test_title_match = re.search(r'## (Test \d+)', test_block)
            if not test_title_match:
                continue
            
            category_name = test_title_match.group(1).strip()
            
            # Create category
            result = session.execute(
                text("INSERT INTO test_category (name, description) VALUES (:name, :desc) RETURNING id"),
                {"name": category_name, "desc": f"Questions for {category_name}"}
            )
            category_id = result.fetchone()[0]
            session.commit()
            total_categories += 1
            
            print(f"\n📚 Processing {category_name}...")
            
            # Find all questions in this category
            question_blocks = re.findall(r'(\d+)\.\s*\*\*(.*?)\*\*([\s\S]*?)(?=\n\d+\. |\Z)', test_block)
            
            for q_num, q_text, options_block in question_blocks:
                question_text = q_text.strip()
                
                # Insert question
                result = session.execute(
                    text("""
                        INSERT INTO question (question_text, category_id, difficulty, created_date)
                        VALUES (:text, :cat_id, :diff, NOW())
                        RETURNING id
                    """),
                    {
                        "text": question_text,
                        "cat_id": category_id,
                        "diff": "basic"
                    }
                )
                question_id = result.fetchone()[0]
                session.commit()
                
                # Parse answer options
                option_lines = re.findall(r'-\s+([A-D])\)\s+(.*)', options_block)
                for letter, option_raw_text in option_lines:
                    is_correct = '✓' in option_raw_text
                    option_text = option_raw_text.replace('**', '').replace('✓', '').strip()
                    
                    # Check if option_label column exists and include it in INSERT
                    try:
                        session.execute(
                            text("""
                                INSERT INTO answer_option (question_id, option_label, option_text, is_correct, option_letter)
                                VALUES (:q_id, :label, :text, :correct, :letter)
                            """),
                            {
                                "q_id": question_id,
                                "label": letter,  # Use same value as option_letter
                                "text": option_text,
                                "correct": is_correct,
                                "letter": letter
                            }
                        )
                    except:
                        # If option_label column doesn't exist, insert without it
                        session.execute(
                            text("""
                                INSERT INTO answer_option (question_id, option_text, is_correct, option_letter)
                                VALUES (:q_id, :text, :correct, :letter)
                            """),
                            {
                                "q_id": question_id,
                                "text": option_text,
                                "correct": is_correct,
                                "letter": letter
                            }
                        )
                
                total_questions += 1
                if total_questions % 10 == 0:
                    print(f"   ✅ Added {total_questions} questions so far...")
            
            session.commit()
        
        print("\n" + "="*60)
        print("🎉 DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"📊 Statistics:")
        print(f"   - Categories created: {total_categories}")
        print(f"   - Questions added: {total_questions}")
        print(f"   - Average questions per category: {total_questions // total_categories if total_categories > 0 else 0}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        session.rollback()
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()
        engine.dispose()


def main():
    """Main entry point"""
    print("="*60)
    print("🚗 TYAIRA DRIVING TEST - DATABASE SEEDER")
    print("="*60)
    print()
    
    # Get database URL
    print("Please enter your Supabase DATABASE_URL:")
    print("(Format: postgresql://user:password@host:port/database)")
    print()
    
    database_url = input("DATABASE_URL: ").strip()
    
    if not database_url:
        print("\n❌ No database URL provided. Exiting.")
        sys.exit(1)
    
    # Validate URL format
    if not database_url.startswith('postgresql://'):
        print("\n❌ Invalid database URL. Must start with 'postgresql://'")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Run seeding
    success = seed_database(database_url)
    
    if success:
        print("\n✅ You can now close this window. Your database is ready!")
        print("🌐 Visit your app to start testing!")
    else:
        print("\n❌ Seeding failed. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
