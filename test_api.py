#!/usr/bin/env python3
"""
Simple test script to verify the API endpoint works correctly.
"""

from app import app
from models import db, Question, TestCategory
import json

def test_api():
    with app.app_context():
        # Test the API logic directly
        category = 'all'
        question_count = 25
        
        if category == 'all':
            all_questions = Question.query.all()
        else:
            # Find category by name
            test_category = TestCategory.query.filter_by(name=category).first()
            if test_category:
                all_questions = Question.query.filter_by(category_id=test_category.id).all()
            else:
                all_questions = []

        print(f"Found {len(all_questions)} questions")
        
        if all_questions:
            # Take first question as sample
            q = all_questions[0]
            print(f"\nSample question:")
            print(f"ID: {q.id}")
            print(f"Text: {q.question_text}")
            print(f"Category: {q.category.name if q.category else 'Unknown'}")
            
            # Get answer options for this question
            options = {}
            correct_answer = None
            for option in q.options:
                options[option.option_letter] = option.option_text
                if option.is_correct:
                    correct_answer = option.option_letter
            
            print(f"Options: {options}")
            print(f"Correct answer: {correct_answer}")
            
            # Test the JSON structure that would be returned
            question_data = {
                'id': q.id,
                'text': q.question_text,
                'category': q.category.name if q.category else 'Unknown',
                'difficulty': q.difficulty,
                'options': options,
                'correct_answer': correct_answer,
                'image_url': None
            }
            
            print(f"\nJSON structure:")
            print(json.dumps(question_data, indent=2))

if __name__ == '__main__':
    test_api()
