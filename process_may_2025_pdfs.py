#!/usr/bin/env python3
"""
Process only May 2025 PDFs from Dropbox, avoiding duplicates
"""
import os
import sys
import logging
from datetime import datetime, timezone
import re

# Add project root to path
sys.path.append('.')

from app import app, db
from models import Client, Transcript, ProcessingLog
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from services.document_processor import DocumentProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class May2025Processor:
    def __init__(self):
        self.dropbox_service = DropboxService()
        self.ai_service = AIService()
        self.notion_service = NotionService()
        self.document_processor = DocumentProcessor()
        
    def extract_date_from_filename(self, filename):
        """Extract date from filename if it contains May 2025 format"""
        # Look for patterns like "5-1-2025", "5-15-2025", etc.
        date_patterns = [
            r'5-(\d{1,2})-2025',  # 5-1-2025, 5-15-2025
            r'(\d{1,2})-5-2025',  # 1-5-2025 (day-month-year)
            r'2025-5-(\d{1,2})',  # 2025-5-1
            r'2025-05-(\d{1,2})', # 2025-05-01
            r'05-(\d{1,2})-2025', # 05-01-2025
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                if '5-' in pattern and pattern.startswith(r'5-'):
                    # Month first: 5-day-2025
                    day = int(match.group(1))
                    return datetime(2025, 5, day).date()
                elif pattern.startswith(r'(\d'):
                    # Day first: day-5-2025  
                    day = int(match.group(1))
                    return datetime(2025, 5, day).date()
                else:
                    # Year first: 2025-5-day
                    day = int(match.group(1))
                    return datetime(2025, 5, day).date()
        
        return None
    
    def is_may_2025_pdf(self, filename):
        """Check if filename indicates May 2025 PDF"""
        if not filename.lower().endswith('.pdf'):
            return False
            
        date = self.extract_date_from_filename(filename)
        return date is not None and date.month == 5 and date.year == 2025
    
    def get_existing_transcripts(self):
        """Get list of already processed transcripts"""
        with app.app_context():
            transcripts = db.session.query(Transcript).all()
            existing_files = set()
            for t in transcripts:
                # Use both filename and dropbox path as identifiers
                existing_files.add(t.original_filename)
                if t.dropbox_path:
                    existing_files.add(t.dropbox_path)
            return existing_files
    
    def get_may_2025_files_from_dropbox(self):
        """Get May 2025 PDF files from Dropbox"""
        try:
            if not self.dropbox_service.test_connection():
                logger.error("Dropbox connection failed")
                return []
            
            all_files = self.dropbox_service.list_files()
            may_files = []
            
            for file_info in all_files:
                if self.is_may_2025_pdf(file_info['name']):
                    may_files.append(file_info)
                    logger.info(f"Found May 2025 PDF: {file_info['name']}")
            
            logger.info(f"Found {len(may_files)} May 2025 PDF files in Dropbox")
            return may_files
            
        except Exception as e:
            logger.error(f"Error getting files from Dropbox: {str(e)}")
            return []
    
    def find_or_create_client(self, filename):
        """Extract client name from filename and find or create client record"""
        # Extract client name (everything before "Appointment")
        name_match = re.search(r'^(.+?)\s+Appointment', filename)
        if not name_match:
            logger.warning(f"Could not extract client name from: {filename}")
            return None
            
        client_name = name_match.group(1).strip()
        
        with app.app_context():
            # Look for existing client
            client = db.session.query(Client).filter(
                Client.name.ilike(f'%{client_name}%')
            ).first()
            
            if not client:
                # Create new client
                client = Client(name=client_name)
                db.session.add(client)
                db.session.flush()
                logger.info(f"Created new client: {client_name}")
            else:
                logger.info(f"Found existing client: {client_name}")
            
            return client
    
    def process_file(self, file_info):
        """Process a single May 2025 PDF file"""
        try:
            filename = file_info['name']
            logger.info(f"Processing file: {filename}")
            
            # Find or create client
            client = self.find_or_create_client(filename)
            if not client:
                logger.error(f"Could not determine client for file: {filename}")
                return False
            
            # Extract session date
            session_date = self.extract_date_from_filename(filename)
            
            # Download file content
            file_content = self.dropbox_service.download_file(file_info['path'])
            if not file_content:
                logger.error(f"Could not download file: {filename}")
                return False
            
            # Extract text from PDF
            raw_content = self.document_processor.extract_text_from_pdf(file_content)
            if not raw_content:
                logger.error(f"Could not extract text from: {filename}")
                return False
            
            # Create transcript record
            with app.app_context():
                transcript = Transcript(
                    client_id=client.id,
                    original_filename=filename,
                    dropbox_path=file_info['path'],
                    file_type='pdf',
                    raw_content=raw_content,
                    session_date=session_date,
                    processing_status='processing'
                )
                
                db.session.add(transcript)
                db.session.flush()
                
                # Process with AI
                logger.info(f"Running AI analysis for: {filename}")
                
                # OpenAI Analysis
                openai_result = self.ai_service.analyze_transcript_openai(raw_content)
                if openai_result:
                    transcript.openai_analysis = openai_result
                
                # Anthropic Analysis  
                anthropic_result = self.ai_service.analyze_transcript_anthropic(raw_content)
                if anthropic_result:
                    transcript.anthropic_analysis = anthropic_result
                
                # Gemini Analysis
                gemini_result = self.ai_service.analyze_transcript_gemini(raw_content)
                if gemini_result:
                    transcript.gemini_analysis = gemini_result
                
                # Extract insights
                insights = self.ai_service.extract_therapy_insights(raw_content)
                if insights:
                    transcript.therapy_insights = insights
                    transcript.sentiment_score = insights.get('sentiment_score')
                    transcript.key_themes = insights.get('key_themes', [])
                    transcript.progress_indicators = insights.get('progress_indicators', {})
                
                transcript.processing_status = 'completed'
                transcript.processed_at = datetime.now(timezone.utc)
                
                db.session.commit()
                
                # Log successful processing
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='file_process',
                    status='success',
                    message=f'Successfully processed May 2025 file: {filename}',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
                
                logger.info(f"Successfully processed: {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            
            # Log error
            with app.app_context():
                log_entry = ProcessingLog(
                    activity_type='file_process',
                    status='error',
                    message=f'Failed to process May 2025 file: {filename}',
                    error_details=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
            
            return False
    
    def run_processing(self):
        """Run the May 2025 processing workflow"""
        logger.info("Starting May 2025 PDF processing")
        
        # Get existing transcripts to avoid duplicates
        existing_files = self.get_existing_transcripts()
        logger.info(f"Found {len(existing_files)} existing transcript records")
        
        # Get May 2025 files from Dropbox
        may_files = self.get_may_2025_files_from_dropbox()
        
        if not may_files:
            logger.info("No May 2025 PDF files found in Dropbox")
            return
        
        processed_count = 0
        skipped_count = 0
        
        for file_info in may_files:
            filename = file_info['name']
            
            # Check if already processed (avoid duplicates)
            if filename in existing_files or file_info['path'] in existing_files:
                logger.info(f"Skipping already processed file: {filename}")
                skipped_count += 1
                continue
            
            # Process the file
            if self.process_file(file_info):
                processed_count += 1
                logger.info(f"Progress: {processed_count} processed, {skipped_count} skipped")
                
                # Add small delay to avoid overwhelming APIs
                import time
                time.sleep(2)
        
        logger.info(f"May 2025 processing complete: {processed_count} processed, {skipped_count} skipped")
        
        # Final log entry
        with app.app_context():
            log_entry = ProcessingLog(
                activity_type='batch_process',
                status='success',
                message=f'May 2025 batch processing complete: {processed_count} new files processed, {skipped_count} duplicates skipped',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(log_entry)
            db.session.commit()

def main():
    """Main execution function"""
    processor = May2025Processor()
    processor.run_processing()

if __name__ == "__main__":
    main()