#!/usr/bin/env python
"""Fix password_hash column length"""

from app import app, db
from sqlalchemy import text

with app.app_context():
    # Update password_hash column to 255 characters
    db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255);'))
    db.session.commit()
    print('✅ Password hash column updated to 255 characters')
