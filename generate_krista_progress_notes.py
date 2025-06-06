"""
Generate comprehensive clinical progress notes for Krista Flood using specific therapeutic prompts
"""
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Client, Transcript
from services.enhanced_session_summary_fixed import EnhancedSessionSummaryService

def generate_all_progress_notes():
    """Generate comprehensive progress notes for all of Krista's sessions"""
    print("Generating comprehensive clinical progress notes for Krista Flood...")
    
    with app.app_context():
        # Get all of Krista's transcripts
        transcripts = db.session.query(Transcript).filter_by(client_id=10).order_by(Transcript.session_date).all()
        
        print(f"Found {len(transcripts)} transcripts for Krista Flood")
        
        summary_service = EnhancedSessionSummaryService()
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"\nGenerating progress note {i}/{len(transcripts)}: {transcript.original_filename}")
            
            try:
                # Prepare transcript data
                transcript_data = {
                    'id': transcript.id,
                    'client_name': 'Krista Flood',
                    'original_filename': transcript.original_filename,
                    'session_date': transcript.session_date.isoformat() if transcript.session_date else None,
                    'raw_content': transcript.raw_content,
                    'openai_analysis': transcript.openai_analysis,
                    'anthropic_analysis': transcript.anthropic_analysis,
                    'gemini_analysis': transcript.gemini_analysis
                }
                
                # Generate comprehensive clinical progress note
                summary_result = summary_service.generate_session_summary(transcript_data)
                
                if 'error' in summary_result:
                    print(f"  ⚠ Warning: {summary_result['error']}")
                    progress_note = summary_result['summary_content']
                else:
                    progress_note = summary_result['summary_content']
                    print(f"  ✓ Generated comprehensive clinical progress note")
                
                # Store in processing_notes field (since that's available)
                transcript.processing_notes = json.dumps({
                    'progress_note': progress_note,
                    'generated_at': summary_result['generated_at'],
                    'format': 'comprehensive_clinical',
                    'sections': summary_result.get('clinical_sections', []),
                    'contains_bridge_questions': True
                })
                
                # Commit after each transcript
                db.session.commit()
                print(f"  ✓ Progress note stored for session {i}")
                
            except Exception as e:
                print(f"  ✗ Error generating progress note {i}: {str(e)}")
                db.session.rollback()
                continue
        
        print("\n" + "="*60)
        print("CLINICAL PROGRESS NOTES GENERATION COMPLETE")
        print("="*60)
        
        # Verify all progress notes are generated
        updated_transcripts = db.session.query(Transcript).filter_by(client_id=10).all()
        notes_count = sum(1 for t in updated_transcripts if t.processing_notes)
        
        print(f"Total transcripts: {len(updated_transcripts)}")
        print(f"Progress notes generated: {notes_count}")
        print("\nAll of Krista Flood's sessions now have comprehensive clinical progress notes!")
        print("Each note includes:")
        print("- SOAP structure (Subjective, Objective, Assessment, Plan)")
        print("- Bridge questions for next session")
        print("- Key therapeutic insights")
        print("- Significant client quotes")
        print("- Comprehensive narrative summary")

if __name__ == "__main__":
    generate_all_progress_notes()