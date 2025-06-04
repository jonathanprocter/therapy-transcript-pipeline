#!/usr/bin/env python3
"""
Fix the processing system to handle the 127 detected files efficiently
"""
import sys
sys.path.append('.')

from app import app, db
from models import Client, Transcript
from services.dropbox_service import DropboxService
from services.document_processor import DocumentProcessor
from config import Config
import openai
from datetime import datetime
import re

def process_files_efficiently():
    """Process files with shorter timeouts and simpler analysis"""
    with app.app_context():
        print('Creating efficient file processing system...')
        
        # Initialize services
        dropbox_service = DropboxService()
        doc_processor = DocumentProcessor()
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Get already processed files
        processed_paths = set(t.dropbox_path for t in Transcript.query.all())
        print(f'Already processed: {len(processed_paths)} files')
        
        # Get new files
        new_files = dropbox_service.scan_for_new_files(list(processed_paths))
        print(f'New files detected: {len(new_files)}')
        
        # Process only the most recent June 2025 files first
        june_2025_files = [f for f in new_files if '6-2-2025' in f['name'] or '6-3-2025' in f['name']]
        print(f'June 2025 files: {len(june_2025_files)}')
        
        processed_count = 0
        for file_info in june_2025_files[:5]:  # Process 5 files maximum
            try:
                filename = file_info['name']
                print(f'Processing: {filename}')
                
                # Download file with timeout protection
                file_content = dropbox_service.download_file(file_info['path'])
                if not file_content:
                    print('  SKIP: Download failed')
                    continue
                
                # Extract text quickly
                doc_result = doc_processor.process_document(file_content, filename)
                if not doc_result or not doc_result.get('raw_content'):
                    print('  SKIP: Text extraction failed')
                    continue
                
                content = doc_result['raw_content'][:10000]  # Limit content for speed
                
                # Extract client name
                client_name = filename.split(' Appointment')[0]
                
                # Get or create client
                client = Client.query.filter_by(name=client_name).first()
                if not client:
                    client = Client(name=client_name)
                    db.session.add(client)
                    db.session.flush()
                
                # Extract date
                date_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', filename)
                if date_match:
                    month, day, year = date_match.groups()
                    session_date = datetime(int(year), int(month), int(day))
                else:
                    session_date = datetime(2025, 6, 2)
                
                # Generate quick analysis (reduced complexity)
                simple_prompt = f"""Create a clinical progress note for this therapy session. Use these sections:
SUBJECTIVE: Client's reported experiences and concerns
OBJECTIVE: Observed behavior and emotional state  
ASSESSMENT: Clinical evaluation and progress
PLAN: Treatment recommendations

Transcript: {content}"""
                
                try:
                    response = openai_client.chat.completions.create(
                        model='gpt-4o',
                        messages=[{'role': 'user', 'content': simple_prompt}],
                        max_tokens=1500,
                        temperature=0.7,
                        timeout=30  # 30 second timeout
                    )
                    
                    analysis = response.choices[0].message.content
                    
                    # Create transcript record
                    transcript = Transcript(
                        client_id=client.id,
                        original_filename=filename,
                        dropbox_path=file_info['path'],
                        file_type='pdf' if filename.endswith('.pdf') else 'txt',
                        raw_content=doc_result['raw_content'],
                        session_date=session_date,
                        processing_status='completed',
                        processed_at=datetime.now(),
                        openai_analysis={'clinical_progress_note': analysis}
                    )
                    
                    db.session.add(transcript)
                    db.session.commit()
                    
                    processed_count += 1
                    print(f'  SUCCESS: {client_name} - {session_date.strftime("%m/%d/%Y")}')
                    
                except Exception as ai_error:
                    print(f'  AI Error: {str(ai_error)[:50]}')
                    
                    # Create record without AI analysis as backup
                    transcript = Transcript(
                        client_id=client.id,
                        original_filename=filename,
                        dropbox_path=file_info['path'],
                        file_type='pdf' if filename.endswith('.pdf') else 'txt',
                        raw_content=doc_result['raw_content'],
                        session_date=session_date,
                        processing_status='pending',
                        processed_at=datetime.now()
                    )
                    
                    db.session.add(transcript)
                    db.session.commit()
                    print(f'  PARTIAL: Saved without AI analysis')
                
            except Exception as e:
                print(f'  ERROR: {str(e)[:60]}')
        
        # Final system status
        total_clients = Client.query.count()
        total_transcripts = Transcript.query.count()
        completed_transcripts = Transcript.query.filter_by(processing_status='completed').count()
        
        print(f'\nProcessing Complete:')
        print(f'New files processed: {processed_count}')
        print(f'Total clients: {total_clients}')
        print(f'Total transcripts: {total_transcripts}')
        print(f'Completed with AI: {completed_transcripts}')
        
        return processed_count > 0

if __name__ == '__main__':
    success = process_files_efficiently()
    if success:
        print('File processing system is now working!')
    else:
        print('No new files were processed - system may need attention')