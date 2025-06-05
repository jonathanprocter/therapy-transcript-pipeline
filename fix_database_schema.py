
#!/usr/bin/env python3
"""
Fix existing database records with NULL raw_content
"""

import os
from app import app, db
from models import Transcript

def fix_null_raw_content():
    """Update all transcripts with NULL raw_content to empty string"""
    with app.app_context():
        # Find transcripts with NULL raw_content
        null_content_transcripts = db.session.query(Transcript).filter(
            Transcript.raw_content.is_(None)
        ).all()
        
        print(f"Found {len(null_content_transcripts)} transcripts with NULL raw_content")
        
        # Update them to empty string
        for transcript in null_content_transcripts:
            transcript.raw_content = ''
            print(f"Fixed transcript {transcript.id}: {transcript.original_filename}")
        
        db.session.commit()
        print("Database schema fix completed successfully")

if __name__ == "__main__":
    fix_null_raw_content()
