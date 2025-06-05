
#!/usr/bin/env python3
"""
Comprehensive system health check
"""

from app import app, db
from models import Transcript, Client, ProcessingLog
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_health():
    """Check database connectivity and basic stats"""
    try:
        with app.app_context():
            client_count = db.session.query(Client).count()
            transcript_count = db.session.query(Transcript).count()
            pending_count = db.session.query(Transcript).filter_by(processing_status='pending').count()
            completed_count = db.session.query(Transcript).filter_by(processing_status='completed').count()
            failed_count = db.session.query(Transcript).filter_by(processing_status='failed').count()
            
            print("📊 DATABASE HEALTH:")
            print(f"  Total Clients: {client_count}")
            print(f"  Total Transcripts: {transcript_count}")
            print(f"  Pending: {pending_count}")
            print(f"  Completed: {completed_count}")
            print(f"  Failed: {failed_count}")
            print("  ✅ Database connection OK")
            return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def check_services():
    """Check all external services"""
    print("\n🔌 EXTERNAL SERVICES:")
    
    # Dropbox
    try:
        dropbox_service = DropboxService()
        if dropbox_service.test_connection():
            print("  ✅ Dropbox connection OK")
        else:
            print("  ⚠️ Dropbox connection failed")
    except Exception as e:
        print(f"  ❌ Dropbox error: {e}")
    
    # AI Service
    try:
        ai_service = AIService()
        openai_ok = ai_service.is_openai_available()
        anthropic_ok = ai_service.is_anthropic_available()
        gemini_ok = ai_service.is_gemini_available()
        
        print(f"  {'✅' if openai_ok else '❌'} OpenAI: {'Available' if openai_ok else 'Not available'}")
        print(f"  {'✅' if anthropic_ok else '❌'} Anthropic: {'Available' if anthropic_ok else 'Not available'}")
        print(f"  {'✅' if gemini_ok else '❌'} Gemini: {'Available' if gemini_ok else 'Not available'}")
    except Exception as e:
        print(f"  ❌ AI Service error: {e}")
    
    # Notion
    try:
        notion_service = NotionService()
        if notion_service.test_connection():
            print("  ✅ Notion connection OK")
        else:
            print("  ⚠️ Notion connection failed")
    except Exception as e:
        print(f"  ❌ Notion error: {e}")

def check_processing_backlog():
    """Check for processing issues"""
    print("\n⚙️ PROCESSING STATUS:")
    
    with app.app_context():
        # Check for old pending files
        old_pending = db.session.query(Transcript).filter(
            Transcript.processing_status == 'pending',
            Transcript.created_at < datetime.now(timezone.utc).replace(hour=datetime.now(timezone.utc).hour-1)
        ).count()
        
        if old_pending > 0:
            print(f"  ⚠️ {old_pending} files pending for over 1 hour")
        else:
            print("  ✅ No stale pending files")
        
        # Check recent logs
        recent_errors = db.session.query(ProcessingLog).filter(
            ProcessingLog.status == 'error',
            ProcessingLog.created_at >= datetime.now(timezone.utc).replace(hour=datetime.now(timezone.utc).hour-1)
        ).count()
        
        if recent_errors > 0:
            print(f"  ⚠️ {recent_errors} processing errors in last hour")
        else:
            print("  ✅ No recent processing errors")

def main():
    """Run comprehensive health check"""
    print("🏥 SYSTEM HEALTH CHECK")
    print("=" * 50)
    
    db_ok = check_database_health()
    check_services()
    check_processing_backlog()
    
    print("\n" + "=" * 50)
    if db_ok:
        print("🎉 System appears healthy and ready for production!")
    else:
        print("⚠️ System has issues that need attention")

if __name__ == "__main__":
    main()
