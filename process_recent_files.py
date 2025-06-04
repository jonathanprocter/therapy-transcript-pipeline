#!/usr/bin/env python3
"""
Simple script to process recent files from Dropbox efficiently
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

def process_recent_files():
    """Process the most recent files efficiently"""
    with app.app_context():
        print('Processing recent files efficiently...')
        
        # Initialize services
        dropbox_service = DropboxService()
        doc_processor = DocumentProcessor()
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Get processed files
        processed_paths = {t.dropbox_path for t in Transcript.query.all()}
        
        # Get new files
        new_files = dropbox_service.scan_for_new_files(list(processed_paths))
        
        # Focus on June 2025 files only
        june_files = [f for f in new_files if '6-2-2025' in f['name'] or '6-3-2025' in f['name']]
        
        print(f'Found {len(june_files)} June files to process')
        
        for i, file_info in enumerate(june_files[:3]):  # Process 3 files
            try:
                filename = file_info['name']
                print(f'{i+1}. Processing: {filename}')
                
                # Download file
                file_content = dropbox_service.download_file(file_info['path'])
                if not file_content:
                    print('   SKIP: Download failed')
                    continue
                
                # Extract text
                doc_result = doc_processor.process_document(file_content, filename)
                if not doc_result or not doc_result.get('raw_content'):
                    print('   SKIP: Text extraction failed')
                    continue
                
                content = doc_result['raw_content']
                
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
                
                # Generate shorter analysis for speed
                prompt = f"Create a comprehensive clinical progress note for this therapy session. Use NO markdown. Structure: SUBJECTIVE, OBJECTIVE, ASSESSMENT, PLAN.\n\nTranscript: {content[:12000]}"
                
                response = openai_client.chat.completions.create(
                    model='gpt-4o',
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                analysis = response.choices[0].message.content
                
                # Create transcript
                transcript = Transcript(
                    client_id=client.id,
                    original_filename=filename,
                    dropbox_path=file_info['path'],
                    file_type='pdf' if filename.endswith('.pdf') else 'txt',
                    raw_content=content,
                    session_date=session_date,
                    processing_status='completed',
                    processed_at=datetime.now(),
                    openai_analysis={'comprehensive_clinical_analysis': analysis}
                )
                
                db.session.add(transcript)
                db.session.commit()
                
                print(f'   SUCCESS: {client_name} - {session_date.strftime("%m/%d/%Y")}')
                
            except Exception as e:
                print(f'   ERROR: {str(e)[:50]}')
        
        # Final stats
        total_clients = Client.query.count()
        total_transcripts = Transcript.query.count()
        print(f'\nSystem updated: {total_clients} clients, {total_transcripts} transcripts')

if __name__ == '__main__':
    process_recent_files()