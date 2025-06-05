"""
Verify Krista Flood's complete processing and generate final status
"""
import os
import sys
import json
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.getcwd())

from app import app, db
from models import Client, Transcript

def verify_krista_processing():
    """Verify all of Krista Flood's transcripts are completely processed"""
    print("Verifying Krista Flood's complete processing status...")
    
    with app.app_context():
        # Get all of Krista's transcripts
        transcripts = db.session.query(Transcript).filter_by(client_id=10).all()
        
        print(f"Total transcripts for Krista Flood: {len(transcripts)}")
        print("="*60)
        
        all_complete = True
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"{i}. {transcript.original_filename}")
            
            # Check each AI analysis
            openai_status = "✓" if transcript.openai_analysis else "✗"
            anthropic_status = "✓" if transcript.anthropic_analysis else "✗"
            gemini_status = "✓" if transcript.gemini_analysis else "✗"
            
            print(f"   OpenAI: {openai_status}  Anthropic: {anthropic_status}  Gemini: {gemini_status}")
            print(f"   Status: {transcript.processing_status}")
            
            if not all([transcript.openai_analysis, transcript.anthropic_analysis, transcript.gemini_analysis]):
                all_complete = False
            
            print()
        
        print("="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        
        # Count completions
        openai_count = sum(1 for t in transcripts if t.openai_analysis)
        anthropic_count = sum(1 for t in transcripts if t.anthropic_analysis)
        gemini_count = sum(1 for t in transcripts if t.gemini_analysis)
        completed_count = sum(1 for t in transcripts if t.processing_status == 'completed')
        
        print(f"Total transcripts: {len(transcripts)}")
        print(f"OpenAI analyses: {openai_count}/{len(transcripts)}")
        print(f"Anthropic analyses: {anthropic_count}/{len(transcripts)}")
        print(f"Gemini analyses: {gemini_count}/{len(transcripts)}")
        print(f"Completed status: {completed_count}/{len(transcripts)}")
        
        if all_complete:
            print("\n🎉 ALL TRANSCRIPTS COMPLETELY PROCESSED!")
            print("Krista Flood's data is ready for Notion sync and session summary generation.")
        else:
            print(f"\n⚠️  {len(transcripts) - completed_count} transcripts need completion")
        
        return all_complete

if __name__ == "__main__":
    verify_krista_processing()