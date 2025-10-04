"""
Cleanup script to organize project files
Run this before deployment to clean up the project structure
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'docs',
        'tests',
        'scripts',
        'archive'
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ Created directory: {dir_name}")

def move_files():
    """Move files to appropriate directories"""
    
    # Move documentation
    docs_files = [
        'CHANGELOG.md',
        'CMS.md',
        'MOBILE_INTERFACE.md',
        'MOBILE_COMPLETE.md',
        'QUICK_START_MOBILE.md'
    ]
    
    for file in docs_files:
        if os.path.exists(file):
            shutil.move(file, f'docs/{file}')
            print(f"✓ Moved {file} to docs/")
    
    # Move test files
    test_files = [
        'test_api.py',
        'test_mobile.py'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            shutil.move(file, f'tests/{file}')
            print(f"✓ Moved {file} to tests/")
    
    # Move scripts
    script_files = [
        'import_questions.py',
        'seed.py'
    ]
    
    for file in script_files:
        if os.path.exists(file):
            if os.path.exists(f'scripts/{file}'):
                os.remove(f'scripts/{file}')
            shutil.copy(file, f'scripts/{file}')
            print(f"✓ Copied {file} to scripts/")
    
    # Archive data files
    archive_files = [
        'driving_test_questions.md'
    ]
    
    for file in archive_files:
        if os.path.exists(file):
            shutil.move(file, f'archive/{file}')
            print(f"✓ Archived {file}")

def delete_files():
    """Delete unnecessary files"""
    files_to_delete = [
        'reset_db.py'  # Empty file
    ]
    
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ Deleted {file}")

def clean_pycache():
    """Remove Python cache files"""
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))
            print(f"✓ Removed {os.path.join(root, '__pycache__')}")
        
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                print(f"✓ Removed {os.path.join(root, file)}")

def create_gitkeep():
    """Create .gitkeep files for empty directories"""
    directories = [
        'uploads/images',
        'uploads/pdfs'
    ]
    
    for dir_path in directories:
        gitkeep_path = os.path.join(dir_path, '.gitkeep')
        if not os.path.exists(gitkeep_path):
            Path(gitkeep_path).touch()
            print(f"✓ Created {gitkeep_path}")

def update_readme():
    """Rename new README"""
    if os.path.exists('README_NEW.md'):
        if os.path.exists('ReadMe.md'):
            shutil.move('ReadMe.md', 'archive/ReadMe_OLD.md')
            print("✓ Archived old README")
        shutil.move('README_NEW.md', 'README.md')
        print("✓ Updated README.md")

def main():
    """Run all cleanup tasks"""
    print("🧹 Starting cleanup...\n")
    
    print("📁 Creating directories...")
    create_directories()
    
    print("\n📦 Moving files...")
    move_files()
    
    print("\n🗑️ Deleting unnecessary files...")
    delete_files()
    
    print("\n🧼 Cleaning Python cache...")
    clean_pycache()
    
    print("\n📝 Creating .gitkeep files...")
    create_gitkeep()
    
    print("\n📄 Updating README...")
    update_readme()
    
    print("\n✅ Cleanup complete!")
    print("\n📋 Next steps:")
    print("1. Review the changes")
    print("2. Update .env file with your configuration")
    print("3. Test the application: flask run")
    print("4. Deploy to production")
    print("\nSee DEPLOYMENT_GUIDE.md for deployment instructions")

if __name__ == '__main__':
    main()
