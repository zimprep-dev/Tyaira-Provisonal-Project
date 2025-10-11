import re
from app import app
from models import db, Question, AnswerOption, TestCategory

def parse_and_populate():
    """Parses the markdown file and populates the database."""
    print("Starting database population from markdown files...")
    with app.app_context():
        # Clear existing questions and answers to avoid duplication
        print("Clearing existing questions, answers, and categories...")
        AnswerOption.query.delete()
        Question.query.delete()
        TestCategory.query.delete()
        db.session.commit()

        try:
            with open('driving_test_answers.md', 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print("Error: 'driving_test_answers.md' not found. Please ensure the file is in the root directory.")
            return

        # Split content by tests using a lookahead to keep the delimiter
        tests = re.split(r'(?=## Test \d+)', content)
        if not tests[0].strip(): # Remove any leading empty string
            tests = tests[1:]

        for test_block in tests:
            test_title_match = re.search(r'## (Test \d+)', test_block)
            if not test_title_match:
                continue
            
            category_name = test_title_match.group(1).strip()
            
            # Create or get the category
            category = TestCategory.query.filter_by(name=category_name).first()
            if not category:
                category = TestCategory(name=category_name, description=f"Questions for {category_name}")
                db.session.add(category)
                db.session.commit()
            print(f"Processing category: {category.name}")

            # Regex to find questions and their options
            question_blocks = re.findall(r'(\d+)\.\s*\*\*(.*?)\*\*([\s\S]*?)(?=\n\d+\. |\Z)', test_block)

            for q_num, q_text, options_block in question_blocks:
                question_text = q_text.strip()
                
                # Create the question
                new_question = Question(
                    question_text=question_text,
                    category_id=category.id,
                    difficulty='basic' # Default difficulty
                )
                db.session.add(new_question)
                db.session.commit() # Commit to get the question ID

                # Parse and add answer options
                option_lines = re.findall(r'-\s+([A-D])\)\s+(.*)', options_block)
                for letter, text in option_lines:
                    is_correct = '✓' in text
                    # Clean up the text
                    option_text = text.replace('**', '').replace('✓', '').strip()

                    new_option = AnswerOption(
                        question_id=new_question.id,
                        option_text=option_text,
                        is_correct=is_correct,
                        option_letter=letter
                    )
                    db.session.add(new_option)
                
                print(f"  - Added Question {q_num}: {question_text[:50]}...")

        db.session.commit()
        print("Database population complete!")

if __name__ == '__main__':
    parse_and_populate()

