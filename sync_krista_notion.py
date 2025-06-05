"""
Sync Krista Flood's completed transcripts to Notion
"""
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Client, Transcript
from services.notion_service import NotionService

def sync_krista_to_notion():
    """Sync all of Krista Flood's transcripts to Notion"""
    print("Syncing Krista Flood's transcripts to Notion...")
    
    with app.app_context():
        # Get all of Krista's completed transcripts
        transcripts = db.session.query(Transcript).filter_by(
            client_id=10, 
            processing_status='completed'
        ).all()
        
        print(f"Found {len(transcripts)} completed transcripts for Krista Flood")
        
        notion_service = NotionService()
        success_count = 0
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"\nSyncing transcript {i}/{len(transcripts)}: {transcript.original_filename}")
            
            try:
                # Prepare transcript data for Notion
                transcript_data = {
                    'client_name': 'Krista Flood',
                    'session_date': transcript.session_date.isoformat() if transcript.session_date else datetime.now().isoformat(),
                    'filename': transcript.original_filename,
                    'openai_analysis': json.loads(transcript.openai_analysis) if transcript.openai_analysis else {},
                    'anthropic_analysis': json.loads(transcript.anthropic_analysis) if transcript.anthropic_analysis else {},
                    'gemini_analysis': json.loads(transcript.gemini_analysis) if transcript.gemini_analysis else {},
                    'raw_content': transcript.raw_content[:1000] if transcript.raw_content else "Content processed"
                }
                
                # Create Notion page
                page_id = notion_service.create_session_page(transcript_data)
                
                if page_id:
                    print(f"  ✓ Successfully synced to Notion: {page_id}")
                    success_count += 1
                else:
                    print(f"  ✗ Failed to sync to Notion")
                
            except Exception as e:
                print(f"  ✗ Error syncing transcript {i}: {str(e)}")
        
        print(f"\n" + "="*50)
        print("NOTION SYNC COMPLETE")
        print("="*50)
        print(f"Total transcripts: {len(transcripts)}")
        print(f"Successfully synced: {success_count}")
        print(f"Failed syncs: {len(transcripts) - success_count}")
        print("\nKrista Flood's data is now available in Notion!")

if __name__ == "__main__":
    sync_krista_to_notion()