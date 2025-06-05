"""
Quick Demo - Process one client transcript completely
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Client, Transcript
from services.ai_service import AIService
from services.enhanced_session_summary import EnhancedSessionSummaryService

def process_one_transcript():
    """Process one transcript completely for demonstration"""
    print("Starting quick demo processing...")
    
    with app.app_context():
        # Get Sarah Palladino's first transcript
        transcript = db.session.query(Transcript).filter_by(client_id=18).first()
        
        if not transcript:
            print("No transcript found")
            return
        
        print(f"Processing: {transcript.original_filename}")
        
        ai_service = AIService()
        summary_service = EnhancedSessionSummaryService()
        
        # Complete Anthropic analysis if missing
        if not transcript.anthropic_analysis:
            print("Adding Anthropic analysis...")
            try:
                result = ai_service._analyze_with_anthropic(transcript.raw_content[:3000], "Sarah Palladino")
                transcript.anthropic_analysis = result
                print("Anthropic analysis completed")
            except Exception as e:
                print(f"Anthropic error: {str(e)}")
        
        # Complete Gemini analysis if missing
        if not transcript.gemini_analysis:
            print("Adding Gemini analysis...")
            try:
                result = ai_service._analyze_with_gemini(transcript.raw_content[:3000], "Sarah Palladino")
                transcript.gemini_analysis = result
                print("Gemini analysis completed")
            except Exception as e:
                print(f"Gemini error: {str(e)}")
        
        # Generate session summary
        print("Generating session summary...")
        transcript_data = {
            'id': transcript.id,
            'original_filename': transcript.original_filename,
            'raw_content': transcript.raw_content,
            'client_name': "Sarah Palladino",
            'session_date': transcript.session_date,
            'openai_analysis': transcript.openai_analysis,
            'anthropic_analysis': transcript.anthropic_analysis,
            'gemini_analysis': transcript.gemini_analysis
        }
        
        try:
            summary_result = summary_service.generate_session_summary(transcript_data)
            # Store as JSON string since session_summary doesn't exist in model
            transcript.processing_notes = str(summary_result)
            print("Session summary generated")
        except Exception as e:
            print(f"Summary error: {str(e)}")
        
        # Update status
        transcript.processing_status = 'completed'
        transcript.processed_at = datetime.now()
        
        try:
            db.session.commit()
            print("Transcript updated successfully")
            print(f"Transcript ID: {transcript.id}")
            print("Demo processing completed!")
        except Exception as e:
            print(f"Database error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    process_one_transcript()