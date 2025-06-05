import os
import time
import logging
from threading import Thread
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from models import Transcript, ProcessingLog, Client
from app import db, app
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self.is_running = False
        self.thread = None

        # Initialize services with error handling
        try:
            self.dropbox_service = DropboxService()
            logger.info("Dropbox service initialized in scheduler")
        except Exception as e:
            logger.warning(f"Error initializing Dropbox service: {str(e)}")
            self.dropbox_service = None

        try:
            self.ai_service = AIService()
            logger.info("AI service initialized in scheduler")
        except Exception as e:
            logger.warning(f"Error initializing AI service: {str(e)}")
            self.ai_service = None

        try:
            self.notion_service = NotionService()
            logger.info("Notion service initialized in scheduler")
        except Exception as e:
            logger.warning(f"Error initializing Notion service: {str(e)}")
            self.notion_service = None

    def start(self):
        """Start the background monitoring"""
        if self.is_running:
            logger.info("Scheduler already running")
            return

        self.is_running = True
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Background scheduler started successfully")

    def stop(self):
        """Stop the background monitoring"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background scheduler stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        check_interval = int(os.environ.get('DROPBOX_CHECK_INTERVAL', '600'))  # 10 minutes default

        while self.is_running:
            try:
                if self.dropbox_service:
                    self._check_for_new_files()
                else:
                    logger.warning("Dropbox service not available, skipping file check")
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

    def _check_for_new_files(self):
        """Check for new files and process them"""
        try:
            with app.app_context():
                # Get already processed files
                processed_files = []
                try:
                    transcripts = db.session.query(Transcript).all()
                    processed_files = [t.dropbox_path for t in transcripts if t.dropbox_path]
                except Exception as e:
                    logger.error(f"Error getting processed files: {str(e)}")
                    return

                # Scan for new files
                new_files = self.dropbox_service.scan_for_new_files(processed_files)

                if new_files and len(new_files) > 0:
                    logger.info(f"Found {len(new_files)} new files to process")

                    for file_info in new_files[:5]:  # Process max 5 files at a time
                        try:
                            self._process_file(file_info)
                        except Exception as e:
                            logger.error(f"Error processing file {file_info.get('name', 'unknown')}: {str(e)}")
                else:
                    logger.debug("No new files found")

        except Exception as e:
            logger.error(f"Error checking for new files: {str(e)}")

    def _process_file(self, file_info):
        """Process a single file"""
        try:
            with app.app_context():
                # Extract client name and session date from filename
                filename = file_info.get('name', 'Unknown File')
                client_name = self._extract_client_name(filename)

                # Get or create client
                client = db.session.query(Client).filter_by(name=client_name).first()
                if not client:
                    client = Client(name=client_name)
                    db.session.add(client)
                    db.session.flush()

                # Check if transcript already exists
                existing = db.session.query(Transcript).filter_by(
                    dropbox_path=file_info.get('path_display', filename)
                ).first()

                if existing:
                    logger.debug(f"Transcript already exists: {filename}")
                    return

                # Create transcript record
                transcript = Transcript(
                    client_id=client.id,
                    original_filename=filename,
                    dropbox_path=file_info.get('path_display', filename),
                    file_type=filename.split('.')[-1].lower() if '.' in filename else 'unknown',
                    processing_status='pending',
                    raw_content='',  # Set empty string instead of None to avoid NOT NULL constraint
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(transcript)
                db.session.commit()

                # Log processing start
                try:
                    log_entry = ProcessingLog(
                        transcript_id=transcript.id,
                        activity_type='file_discovery',
                        status='info',
                        message=f'New file discovered: {filename}',
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"Error creating log entry: {str(e)}")

                logger.info(f"Added new transcript for processing: {filename}")

        except Exception as e:
            logger.error(f"Error processing file {file_info.get('name', 'unknown')}: {str(e)}")

    def _extract_client_name(self, filename):
        """Extract client name from filename"""
        try:
            # Remove file extension
            name_part = filename.rsplit('.', 1)[0]

            # Common patterns for therapy transcripts
            # Pattern: "Client Name Appointment ..."
            if 'Appointment' in name_part:
                parts = name_part.split('Appointment')[0].strip()
                return parts

            # Pattern: "Client Name Session ..."  
            if 'Session' in name_part:
                parts = name_part.split('Session')[0].strip()
                return parts

            # Pattern: "FirstName LastName Date/Time"
            parts = name_part.split()
            if len(parts) >= 2:
                # Assume first two parts are first and last name
                potential_name = f"{parts[0]} {parts[1]}"

                # Check if the next part looks like a date
                if len(parts) > 2 and any(c in parts[2] for c in ['-', '/', ':']):
                    return potential_name

            # Default: use first two words or whole filename
            parts = name_part.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1]}"
            else:
                return name_part
        except Exception as e:
            logger.error(f"Error extracting client name from {filename}: {str(e)}")
            return "Unknown Client"

def process_new_files():
    """Process new files discovered by manual scan"""
    try:
        with app.app_context():
            logger.info("Starting background processing of new files")

            # Get files that are pending processing
            pending_transcripts = db.session.query(Transcript).filter_by(
                processing_status='pending'
            ).limit(5).all()

            if not pending_transcripts:
                logger.info("No pending transcripts to process")
                return

            from services.ai_service import AIService
            from services.document_processor import DocumentProcessor
            from services.dropbox_service import DropboxService

            # Initialize services
            ai_service = AIService()
            doc_processor = DocumentProcessor()
            dropbox_service = DropboxService()

            for transcript in pending_transcripts:
                try:
                    logger.info(f"Processing transcript: {transcript.original_filename}")

                    # Download file content if needed
                    if not transcript.raw_content and transcript.dropbox_path:
                        file_content = dropbox_service.download_file(transcript.dropbox_path)
                        if file_content:
                            doc_result = doc_processor.process_document(file_content, transcript.original_filename)
                            transcript.raw_content = doc_result.get('cleaned_content', '')

                    # Process with AI if we have content
                    if transcript.raw_content and ai_service:
                        # Use the new detailed analysis method
                        client_name_for_analysis = transcript.client.name if transcript.client else "Unknown Client"
                        analysis_result = ai_service.analyze_transcript_detailed(transcript.raw_content, client_name_for_analysis)

                        if analysis_result:
                            # Assuming analyze_transcript_detailed returns a flat dict with all fields
                            # Existing fields (adapt if structure from analyze_transcript_detailed is different)
                            # For now, we assume the new method is the primary source for OpenAI based insights.
                            # If other providers are used by other methods, that logic would remain separate.
                            # The `raw_openai_clinical_note` could be stored if a model field exists for it.
                            # transcript.openai_analysis = analysis_result.get('raw_openai_clinical_note') # Or a more structured part if available

                            transcript.key_themes = analysis_result.get('key_themes', [])
                            transcript.therapy_insights = analysis_result.get('therapy_insights_summary') # Using the summary from detailed analysis
                            transcript.sentiment_score = analysis_result.get('sentiment_score')

                            # New fields for Case Conceptualization
                            transcript.session_complaints = analysis_result.get('session_complaints', [])
                            transcript.session_concerns = analysis_result.get('session_concerns', [])
                            transcript.session_action_items = analysis_result.get('session_action_items', [])
                            transcript.session_presentation_summary = analysis_result.get('session_presentation_summary')

                            transcript.processing_status = 'completed'
                            transcript.processed_at = datetime.now(timezone.utc)
                            db.session.commit() # Commit transcript updates first
                            logger.info(f"Successfully processed and saved transcript: {transcript.original_filename}")

                            # Attempt to update Case Conceptualization
                            try:
                                client = transcript.client
                                if not client: # Should not happen if transcript.client_id is set
                                     client = db.session.query(Client).get(transcript.client_id)

                                if client:
                                    existing_conceptualization = client.current_case_conceptualization

                                    # Prepare current session data for conceptualization prompt
                                    # This dict should match what _format_session_for_conceptualization_prompt expects
                                    current_session_analysis_dict = {
                                        'session_date': transcript.session_date.isoformat() if transcript.session_date else datetime.now(timezone.utc).isoformat(), # Ensure it's a string
                                        'session_complaints': transcript.session_complaints,
                                        'session_concerns': transcript.session_concerns,
                                        'key_themes': transcript.key_themes,
                                        'session_presentation_summary': transcript.session_presentation_summary,
                                        'therapy_insights': transcript.therapy_insights, # This is the summary string
                                        'session_action_items': transcript.session_action_items
                                    }

                                    logger.info(f"Updating case conceptualization for client ID: {client.id} based on transcript ID: {transcript.id}")
                                    updated_conceptualization_text = ai_service.update_case_conceptualization(
                                        existing_conceptualization, 
                                        [current_session_analysis_dict] # Pass as a list of one session
                                    )

                                    if updated_conceptualization_text:
                                        client.current_case_conceptualization = updated_conceptualization_text
                                        client.case_conceptualization_updated_at = datetime.now(timezone.utc)
                                        db.session.commit() # Commit client update
                                        logger.info(f"Case conceptualization updated for client ID: {client.id}")
                                    else:
                                        logger.warning(f"Case conceptualization update returned None for client ID: {client.id}")
                                else:
                                    logger.error(f"Could not find client for transcript ID: {transcript.id} to update conceptualization.")

                            except Exception as e_concept:
                                db.session.rollback() # Rollback client update if conceptualization failed
                                logger.error(f"Error updating case conceptualization for client ID {transcript.client_id}: {str(e_concept)}")

                        else: # if analysis_result is None or empty
                            transcript.processing_status = 'failed'
                            logger.warning(f"AI analysis (detailed) failed or returned empty for: {transcript.original_filename}")
                            db.session.commit() 
                    else: # if no raw_content or no ai_service
                        transcript.processing_status = 'failed'
                        logger.warning(f"No content or AI service available for: {transcript.original_filename}")
                        db.session.commit()

                except Exception as e:
                    db.session.rollback() # Rollback any partial changes to transcript for this iteration
                    logger.error(f"Error processing transcript {transcript.id}: {str(e)}")
                    transcript.processing_status = 'failed'
                    db.session.commit()

            logger.info("Background processing completed")

    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")

# Global scheduler instance
scheduler = None

def start_background_scheduler():
    """Start the background scheduler"""
    global scheduler

    try:
        if scheduler is None:
            scheduler = BackgroundScheduler()

        if not scheduler.is_running:
            scheduler.start()
        else:
            logger.info("Scheduler already running")
    except Exception as e:
        logger.error(f"Error starting background scheduler: {str(e)}")

def stop_background_scheduler():
    """Stop the background scheduler"""
    global scheduler

    try:
        if scheduler and scheduler.is_running:
            scheduler.stop()
    except Exception as e:
        logger.error(f"Error stopping background scheduler: {str(e)}")

def process_document_content(file_content, filename):
    """Process document content based on file type"""
    try:
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext == '.pdf':
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            content = processor.extract_text_from_pdf(file_content)
            return content if content else f"[PDF content extraction failed for {filename}]"
        elif file_ext == '.txt':
            try:
                content = file_content.decode('utf-8')
                return content if content.strip() else f"[Empty text file: {filename}]"
            except UnicodeDecodeError:
                try:
                    content = file_content.decode('latin-1')
                    return content if content.strip() else f"[Empty text file: {filename}]"
                except:
                    return f"[Text file encoding error for {filename}]"
        elif file_ext == '.docx':
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            content = processor.extract_text_from_docx(file_content)
            return content if content else f"[DOCX content extraction failed for {filename}]"
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return f"[Unsupported file type {file_ext} for {filename}]"

    except Exception as e:
        logger.error(f"Error processing document content for {filename}: {str(e)}")
        return f"[Document processing error for {filename}: {str(e)}]"