#!/usr/bin/env python3
"""
Script to import driving test questions from markdown file into the database.
This will parse the driving_test_answers.md file and populate the database
with all questions, options, and correct answers.
"""

import re
from app import app
from models import db, Question, AnswerOption, TestCategory

def parse_markdown_questions(file_path):
    """Parse the markdown file and extract questions with answers."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions = []
    current_category = "General"  # Default category
    
    # Split content by question numbers
    question_pattern = r'(\d+)\.\s+\*\*(.*?)\*\*\s*\n((?:\s*-\s+.*?\n)+)'
    matches = re.findall(question_pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        question_num, question_text, options_text = match
        
        # Clean up question text
        question_text = question_text.strip()
        
        # Parse options
        option_lines = [line.strip() for line in options_text.strip().split('\n') if line.strip()]
        options = []
        correct_answer = None
        
        for line in option_lines:
            # Match pattern: - A) Option text or - **A) Option text** ✓
            option_match = re.match(r'-\s+(\*\*)?\s*([ABC])\)\s+(.*?)(\s*\*\*)?\s*✓?\s*$', line)
            if option_match:
                is_bold_start, letter, text, is_bold_end = option_match.groups()
                
                # Clean up the option text
                text = text.strip()
                if text.endswith('**'):
                    text = text[:-2].strip()
                
                # Check if this is the correct answer (has ✓ or is bold)
                is_correct = '✓' in line or (is_bold_start and is_bold_end)
                
                options.append({
                    'letter': letter,
                    'text': text,
                    'is_correct': is_correct
                })
                
                if is_correct:
                    correct_answer = letter
        
        # Determine category based on question content
        category = determine_category(question_text)
        
        if len(options) >= 2:  # Only add questions with at least 2 options
            questions.append({
                'number': int(question_num),
                'text': question_text,
                'category': category,
                'options': options,
                'correct_answer': correct_answer
            })
    
    return questions

def determine_category(question_text):
    """Determine the category based on question content."""
    question_lower = question_text.lower()
    
    if any(word in question_lower for word in ['sign', 'indicates', 'robot', 'light']):
        return "Traffic Signs and Signals"
    elif any(word in question_lower for word in ['car', 'vehicle', 'right of way', 'gives way', 'stop']):
        return "Right of Way"
    elif any(word in question_lower for word in ['speed', 'limit', 'km/h']):
        return "Speed Limits"
    elif any(word in question_lower for word in ['park', 'parking']):
        return "Parking Rules"
    elif any(word in question_lower for word in ['motorcycle', 'bicycle']):
        return "Motorcycles and Bicycles"
    elif any(word in question_lower for word in ['accident', 'emergency']):
        return "Accidents and Emergencies"
    elif any(word in question_lower for word in ['night', 'lights', 'headlight']):
        return "Night Driving"
    elif any(word in question_lower for word in ['horn', 'sound']):
        return "Vehicle Equipment"
    elif any(word in question_lower for word in ['line', 'marking', 'road marking']):
        return "Road Markings"
    elif any(word in question_lower for word in ['heavy vehicle', 'tow', 'trailer']):
        return "Heavy Vehicles"
    elif any(word in question_lower for word in ['learner', 'license', 'permit']):
        return "Licensing"
    elif any(word in question_lower for word in ['alcohol', 'drink', 'driving']):
        return "Impaired Driving"
    elif any(word in question_lower for word in ['pedestrian', 'crosswalk']):
        return "Pedestrians"
    elif any(word in question_lower for word in ['weather', 'rain', 'fog']):
        return "Weather Conditions"
    elif any(word in question_lower for word in ['intersection', 'junction']):
        return "Intersections"
    else:
        return "General Rules"

def import_questions_to_db():
    """Import all questions from the markdown file to the database."""
    
    print("Starting question import...")
    
    # Clear existing questions and categories (optional - comment out if you want to keep existing data)
    print("Clearing existing questions...")
    AnswerOption.query.delete()
    Question.query.delete()
    TestCategory.query.delete()
    db.session.commit()
    
    # Parse questions from markdown
    questions = parse_markdown_questions('driving_test_answers.md')
    print(f"Parsed {len(questions)} questions from markdown file")
    
    # Create categories
    categories = {}
    for question in questions:
        category_name = question['category']
        if category_name not in categories:
            category = TestCategory(
                name=category_name,
                description=f"Questions related to {category_name.lower()}"
            )
            db.session.add(category)
            categories[category_name] = category
    
    db.session.flush()  # Get category IDs
    print(f"Created {len(categories)} categories")
    
    # Import questions
    imported_count = 0
    for question_data in questions:
        try:
            # Create question
            question = Question(
                question_text=question_data['text'],
                category_id=categories[question_data['category']].id,
                difficulty='basic'
            )
            db.session.add(question)
            db.session.flush()  # Get question ID
            
            # Add answer options
            for option_data in question_data['options']:
                option = AnswerOption(
                    question_id=question.id,
                    option_text=option_data['text'],
                    option_letter=option_data['letter'],
                    is_correct=option_data['is_correct']
                )
                db.session.add(option)
            
            imported_count += 1
            
            if imported_count % 50 == 0:
                print(f"Imported {imported_count} questions...")
                
        except Exception as e:
            print(f"Error importing question {question_data['number']}: {e}")
            continue
    
    # Commit all changes
    db.session.commit()
    print(f"Successfully imported {imported_count} questions!")
    
    # Print summary
    print("\nImport Summary:")
    print(f"Total Questions: {Question.query.count()}")
    print(f"Total Categories: {TestCategory.query.count()}")
    print(f"Total Answer Options: {AnswerOption.query.count()}")
    
    print("\nCategories created:")
    for category in TestCategory.query.all():
        question_count = Question.query.filter_by(category_id=category.id).count()
        print(f"- {category.name}: {question_count} questions")

if __name__ == '__main__':
    with app.app_context():
        import_questions_to_db()
