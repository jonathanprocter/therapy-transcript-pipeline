
#!/usr/bin/env python3
"""
Test script to verify the scheduler database fixes
"""

from app import app, db
from models import Transcript, Client
from datetime import datetime, timezone

def test_transcript_creation():
    """Test that transcripts can be created without raw_content errors"""
    with app.app_context():
        # Get or create a test client
        test_client = db.session.query(Client).filter_by(name='Test Client').first()
        if not test_client:
            test_client = Client(name='Test Client')
            db.session.add(test_client)
            db.session.flush()

        # Try to create a transcript
        try:
            transcript = Transcript(
                client_id=test_client.id,
                original_filename='test_file.pdf',
                dropbox_path='/test/test_file.pdf',
                file_type='pdf',
                processing_status='pending',
                raw_content='',  # This should work now
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(transcript)
            db.session.commit()
            
            print("✅ Transcript creation test PASSED")
            
            # Clean up
            db.session.delete(transcript)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Transcript creation test FAILED: {e}")

if __name__ == "__main__":
    test_transcript_creation()
