"""
Complete processing for Krista Flood - All AI analyses and session summaries
"""
import sys
import os
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Client, Transcript
from services.ai_service import AIService
from services.enhanced_session_summary import EnhancedSessionSummaryService

def process_krista_flood_complete():
    """Process all of Krista Flood's transcripts completely"""
    print("Processing all of Krista Flood's transcripts...")
    
    with app.app_context():
        # Get all of Krista's transcripts
        transcripts = db.session.query(Transcript).filter_by(client_id=10).all()
        
        print(f"Found {len(transcripts)} transcripts for Krista Flood")
        
        ai_service = AIService()
        summary_service = EnhancedSessionSummaryService()
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"\nProcessing transcript {i}/{len(transcripts)}: {transcript.original_filename}")
            
            try:
                # Complete Anthropic analysis if missing
                if not transcript.anthropic_analysis:
                    print("  Running Anthropic analysis...")
                    try:
                        result = ai_service._analyze_with_anthropic(
                            transcript.raw_content[:4000], "Krista Flood"
                        )
                        transcript.anthropic_analysis = result
                        print("  ✓ Anthropic analysis completed")
                    except Exception as e:
                        print(f"  ✗ Anthropic error: {str(e)}")
                
                # Complete Gemini analysis if missing
                if not transcript.gemini_analysis:
                    print("  Running Gemini analysis...")
                    try:
                        result = ai_service._analyze_with_gemini(
                            transcript.raw_content[:4000], "Krista Flood"
                        )
                        transcript.gemini_analysis = result
                        print("  ✓ Gemini analysis completed")
                    except Exception as e:
                        print(f"  ✗ Gemini error: {str(e)}")
                
                # Generate enhanced session summary
                print("  Generating session summary...")
                transcript_data = {
                    'id': transcript.id,
                    'original_filename': transcript.original_filename,
                    'raw_content': transcript.raw_content,
                    'client_name': "Krista Flood",
                    'session_date': transcript.session_date,
                    'openai_analysis': transcript.openai_analysis,
                    'anthropic_analysis': transcript.anthropic_analysis,
                    'gemini_analysis': transcript.gemini_analysis
                }
                
                try:
                    summary_result = summary_service.generate_session_summary(transcript_data)
                    # Store summary in processing_notes since session_summary field doesn't exist
                    transcript.processing_notes = json.dumps(summary_result)
                    print("  ✓ Session summary generated")
                except Exception as e:
                    print(f"  ✗ Summary error: {str(e)}")
                
                # Update processing status
                transcript.processing_status = 'completed'
                transcript.processed_at = datetime.now()
                
                # Commit after each transcript
                db.session.commit()
                print(f"  ✓ Transcript {i} processing completed")
                
            except Exception as e:
                print(f"  ✗ Error processing transcript {i}: {str(e)}")
                db.session.rollback()
                continue
        
        # Generate final status report
        print("\n" + "="*50)
        print("KRISTA FLOOD PROCESSING COMPLETE")
        print("="*50)
        
        # Check final status
        completed_transcripts = db.session.query(Transcript).filter_by(
            client_id=10, 
            processing_status='completed'
        ).all()
        
        anthropic_count = sum(1 for t in transcripts if t.anthropic_analysis)
        gemini_count = sum(1 for t in transcripts if t.gemini_analysis)
        openai_count = sum(1 for t in transcripts if t.openai_analysis)
        summary_count = sum(1 for t in transcripts if t.processing_notes)
        
        print(f"Total transcripts: {len(transcripts)}")
        print(f"Completed processing: {len(completed_transcripts)}")
        print(f"OpenAI analyses: {openai_count}")
        print(f"Anthropic analyses: {anthropic_count}")
        print(f"Gemini analyses: {gemini_count}")
        print(f"Session summaries: {summary_count}")
        print("\nKrista Flood's complete processing finished!")

if __name__ == "__main__":
    process_krista_flood_complete()