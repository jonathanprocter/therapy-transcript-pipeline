import logging
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from app import app, db
from models import Client, Transcript, ProcessingLog
from services.dropbox_service import DropboxService
from services.document_processor import DocumentProcessor
from services.ai_service import AIService
from services.notion_service import NotionService
from services.content_parser import ContentParser
from services.emotional_analysis import EmotionalAnalysis
from services.visualization_service import VisualizationService
from config import Config
import json

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def start_background_scheduler():
    """Start the background scheduler for automated tasks"""
    global scheduler
    
    if scheduler is not None:
        logger.info("Scheduler already running")
        return
    
    try:
        scheduler = BackgroundScheduler(daemon=True)
        
        # Add job to scan Dropbox for new files
        scheduler.add_job(
            func=scan_and_process_files,
            trigger=IntervalTrigger(minutes=Config.DROPBOX_SCAN_INTERVAL_MINUTES),
            id='dropbox_scan',
            name='Scan Dropbox for new transcripts',
            replace_existing=True
        )
        
        # Add job to retry failed processing
        scheduler.add_job(
            func=retry_failed_processing,
            trigger=IntervalTrigger(hours=1),
            id='retry_failed',
            name='Retry failed transcript processing',
            replace_existing=True
        )
        
        # Add job to sync with Notion
        scheduler.add_job(
            func=sync_with_notion,
            trigger=IntervalTrigger(minutes=30),
            id='notion_sync',
            name='Sync completed transcripts with Notion',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Background scheduler started successfully")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown() if scheduler else None)
        
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {str(e)}")

def scan_and_process_files():
    """Scan Dropbox for new files and process them efficiently"""
    with app.app_context():
        try:
            logger.info("Starting Dropbox scan for new files")
            
            # Initialize services
            dropbox_service = DropboxService()
            document_processor = DocumentProcessor()
            
            # Get list of already processed files
            processed_files = [t.dropbox_path for t in db.session.query(Transcript).all()]
            
            # Scan for new files
            new_files = dropbox_service.scan_for_new_files(processed_files)
            
            if not new_files:
                logger.info("No new files found")
                return
            
            logger.info(f"Found {len(new_files)} new files to process")
            
            # Process only recent files (last 30 days) to avoid overwhelming the system
            recent_files = [f for f in new_files if 'june' in f['name'].lower() or '6-' in f['name'] or '2025' in f['name']][:10]
            
            logger.info(f"Processing {len(recent_files)} recent files")
            
            # Process each recent file
            for file_info in recent_files:
                try:
                    process_single_file_efficiently(file_info, dropbox_service, document_processor)
                except Exception as e:
                    logger.error(f"Error processing file {file_info['name']}: {str(e)}")
                    
                    # Log the error
                    try:
                        error_log = ProcessingLog()
                        error_log.activity_type = 'file_process'
                        error_log.status = 'error'
                        error_log.message = f"Failed to process {file_info['name']}"
                        error_log.error_details = str(e)
                        error_log.context_metadata = {'file_info': file_info}
                        db.session.add(error_log)
                        db.session.commit()
                    except:
                        pass
            
            logger.info("Dropbox scan completed")
            
        except Exception as e:
            logger.error(f"Error during Dropbox scan: {str(e)}")
            
            # Log the error
            try:
                error_log = ProcessingLog()
                error_log.activity_type = 'dropbox_scan'
                error_log.status = 'error'
                error_log.message = "Dropbox scan failed"
                error_log.error_details = str(e)
                db.session.add(error_log)
                db.session.commit()
            except Exception as log_error:
                logger.error(f"Failed to log error: {str(log_error)}")

def process_single_file_efficiently(file_info, dropbox_service, document_processor):
    """Process a single file efficiently with reduced complexity"""
    import openai
    import re
    from datetime import datetime
    
    try:
        logger.info(f"Processing file efficiently: {file_info['name']}")
        
        # Download the file
        file_content = dropbox_service.download_file(file_info['path'])
        if not file_content:
            raise ValueError("Failed to download file")
        
        # Process the document
        processed_data = document_processor.process_document(file_content, file_info['name'])
        if not processed_data or not processed_data.get('raw_content'):
            raise ValueError("Failed to extract content")
        
        content = processed_data['raw_content']
        
        # Extract client name from filename
        filename = file_info['name']
        client_name = filename.split(' Appointment')[0] if 'Appointment' in filename else filename.replace('.pdf', '').replace('.txt', '').split('_')[0]
        
        # Find or create client
        client = db.session.query(Client).filter(Client.name.ilike(f'%{client_name}%')).first()
        if not client:
            client = Client()
            client.name = client_name
            db.session.add(client)
            db.session.flush()
            logger.info(f"Created new client: {client_name}")
        
        # Extract date from filename
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', filename)
        if date_match:
            month, day, year = date_match.groups()
            session_date = datetime(int(year), int(month), int(day))
        else:
            session_date = datetime.now()
        
        # Check for duplicates
        existing_transcript = Transcript.query.filter_by(
            client_id=client.id,
            original_filename=filename
        ).first()
        
        if existing_transcript:
            logger.info(f"Duplicate detected - skipping {filename}")
            return True
        
        # Generate AI analysis efficiently
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        simple_prompt = f"""Create a clinical progress note for this therapy session. Use these sections:
SUBJECTIVE: Client's reported experiences and concerns
OBJECTIVE: Observed behavior and emotional state  
ASSESSMENT: Clinical evaluation and progress
PLAN: Treatment recommendations

Transcript: {content[:12000]}"""
        
        try:
            response = openai_client.chat.completions.create(
                model='gpt-4o',
                messages=[{'role': 'user', 'content': simple_prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content
            
            # Create transcript with analysis
            transcript = Transcript()
            transcript.client_id = client.id
            transcript.original_filename = filename
            transcript.dropbox_path = file_info['path']
            transcript.file_type = 'pdf' if filename.endswith('.pdf') else 'txt'
            transcript.raw_content = content
            transcript.session_date = session_date
            transcript.processing_status = 'completed'
            transcript.processed_at = datetime.now()
            transcript.openai_analysis = {'clinical_progress_note': analysis}
            
            db.session.add(transcript)
            db.session.commit()
            
            logger.info(f"Successfully processed {filename} for {client_name}")
            return True
            
        except Exception as ai_error:
            logger.warning(f"AI analysis failed for {filename}: {str(ai_error)}")
            
            # Save without AI analysis as backup
            transcript = Transcript()
            transcript.client_id = client.id
            transcript.original_filename = filename
            transcript.dropbox_path = file_info['path']
            transcript.file_type = 'pdf' if filename.endswith('.pdf') else 'txt'
            transcript.raw_content = content
            transcript.session_date = session_date
            transcript.processing_status = 'pending'
            transcript.processed_at = datetime.now()
            
            db.session.add(transcript)
            db.session.commit()
            
            logger.info(f"Saved {filename} without AI analysis")
            return True
        
    except Exception as e:
        logger.error(f"Failed to process {file_info['name']}: {str(e)}")
        return False

def process_single_file(file_info, dropbox_service, document_processor, ai_service):
    """Process a single file from Dropbox"""
    try:
        logger.info(f"Processing file: {file_info['name']}")
        
        # Download the file
        file_content = dropbox_service.download_file(file_info['path'])
        if not file_content:
            raise ValueError("Failed to download file")
        
        # Process the document
        processed_data = document_processor.process_document(file_content, file_info['name'])
        
        # Validate content
        validation_result = document_processor.validate_content(processed_data['cleaned_content'])
        if not validation_result['is_valid']:
            logger.warning(f"File {file_info['name']} failed validation: {validation_result['issues']}")
        
        # Initialize content parser for intelligent extraction
        content_parser = ContentParser()
        
        # Extract client name and date intelligently
        extraction_info = content_parser.extract_comprehensive_info(
            file_info['name'], 
            processed_data['cleaned_content']
        )
        
        client_name = extraction_info['client_name'] or 'Unknown Client'
        session_date = extraction_info['session_date'] or processed_data.get('extracted_date')
        
        # Find or create client
        client = db.session.query(Client).filter(Client.name.ilike(f'%{client_name}%')).first()
        if not client:
            client = Client(name=client_name)
            db.session.add(client)
            db.session.flush()  # Get the ID
            logger.info(f"Created new client: {client_name}")
        
        # Check for duplicates - skip if transcript already exists
        existing_transcript = Transcript.query.filter_by(
            client_id=client.id,
            original_filename=file_info['name']
        ).first()
        
        # Also check by dropbox path to catch path duplicates
        existing_by_path = Transcript.query.filter_by(
            dropbox_path=file_info['path']
        ).first()
        
        if existing_transcript or existing_by_path:
            logger.info(f"Duplicate detected - skipping {file_info['name']} for {client_name}")
            return True
        
        # Create transcript record with chronological ordering
        transcript = Transcript(
            client_id=client.id,
            original_filename=file_info['name'],
            dropbox_path=file_info['path'],
            file_type=processed_data['file_type'],
            raw_content=processed_data['raw_content'],
            session_date=session_date,
            processing_status='processing'
        )
        db.session.add(transcript)
        db.session.flush()  # Get the ID
        
        # Perform comprehensive therapy analysis using the clinical prompt
        logger.info(f"Starting comprehensive therapy analysis for transcript {transcript.id}")
        
        # Use the comprehensive therapy analysis prompt for ALL PDFs
        therapy_prompt = Config.THERAPY_ANALYSIS_PROMPT + processed_data['raw_content']
        
        # Generate comprehensive clinical progress note
        import openai
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        try:
            response = openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert clinical therapist creating comprehensive progress notes with deep clinical analysis.'
                    },
                    {
                        'role': 'user', 
                        'content': therapy_prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            comprehensive_analysis = response.choices[0].message.content
            logger.info(f"Generated comprehensive clinical analysis: {len(comprehensive_analysis)} characters")
            
            # Store the comprehensive analysis
            analysis_results = {
                'comprehensive_clinical_analysis': comprehensive_analysis,
                'openai_analysis': comprehensive_analysis
            }
            
        except Exception as e:
            logger.error(f"Comprehensive therapy analysis failed: {e}")
            # Fallback to standard analysis
            analysis_results = ai_service.analyze_transcript(
                processed_data['cleaned_content'],
                client_name
            )
        
        # Update transcript with comprehensive analysis results
        transcript.openai_analysis = analysis_results.get('openai_analysis')
        transcript.anthropic_analysis = analysis_results.get('anthropic_analysis')
        transcript.gemini_analysis = analysis_results.get('gemini_analysis')
        
        # Extract consolidated insights
        consolidated = analysis_results.get('consolidated_insights', {})
        transcript.sentiment_score = consolidated.get('client_mood')
        transcript.key_themes = consolidated.get('key_topics', [])
        transcript.therapy_insights = consolidated
        
        # Extract progress indicators
        progress_indicators = {}
        for provider_key in ['openai_analysis', 'anthropic_analysis', 'gemini_analysis']:
            provider_data = analysis_results.get(provider_key, {})
            if provider_data and 'client_progress_indicators' in provider_data:
                progress_indicators[provider_key] = provider_data['client_progress_indicators']
        
        transcript.progress_indicators = progress_indicators
        transcript.processing_status = 'completed'
        transcript.processed_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Successfully processed transcript {transcript.id} for client {client_name}")
        
        # Log successful processing
        success_log = ProcessingLog(
            transcript_id=transcript.id,
            activity_type='file_process',
            status='success',
            message=f"Successfully processed {file_info['name']}",
            context_metadata={'client_name': client_name, 'file_size': file_info['size']}
        )
        db.session.add(success_log)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error processing file {file_info['name']}: {str(e)}")
        
        # Mark transcript as failed if it was created
        try:
            if 'transcript' in locals():
                transcript.processing_status = 'failed'
                db.session.commit()
        except Exception:
            pass
        
        raise

def retry_failed_processing():
    """Retry processing of failed transcripts"""
    with app.app_context():
        try:
            logger.info("Starting retry of failed transcript processing")
            
            # Get failed transcripts
            failed_transcripts = db.session.query(Transcript)\
                .filter(Transcript.processing_status == 'failed')\
                .limit(5).all()  # Limit retries to avoid overwhelming the system
            
            if not failed_transcripts:
                logger.info("No failed transcripts to retry")
                return
            
            logger.info(f"Retrying {len(failed_transcripts)} failed transcripts")
            
            # Initialize services
            ai_service = AIService()
            
            for transcript in failed_transcripts:
                try:
                    if not transcript.raw_content:
                        logger.warning(f"Transcript {transcript.id} has no content, skipping retry")
                        continue
                    
                    logger.info(f"Retrying transcript {transcript.id}")
                    
                    # Mark as processing
                    transcript.processing_status = 'processing'
                    db.session.commit()
                    
                    # Retry AI analysis
                    client_name = transcript.client.name if transcript.client else "Unknown"
                    analysis_results = ai_service.analyze_transcript(transcript.raw_content, client_name)
                    
                    # Update with results
                    transcript.openai_analysis = analysis_results.get('openai_analysis')
                    transcript.anthropic_analysis = analysis_results.get('anthropic_analysis')
                    transcript.gemini_analysis = analysis_results.get('gemini_analysis')
                    
                    consolidated = analysis_results.get('consolidated_insights', {})
                    transcript.sentiment_score = consolidated.get('client_mood')
                    transcript.key_themes = consolidated.get('key_topics', [])
                    transcript.therapy_insights = consolidated
                    
                    transcript.processing_status = 'completed'
                    transcript.processed_at = datetime.now(timezone.utc)
                    
                    db.session.commit()
                    
                    logger.info(f"Successfully retried transcript {transcript.id}")
                    
                except Exception as e:
                    logger.error(f"Error retrying transcript {transcript.id}: {str(e)}")
                    transcript.processing_status = 'failed'
                    db.session.commit()
            
        except Exception as e:
            logger.error(f"Error during failed transcript retry: {str(e)}")

def sync_with_notion():
    """Sync completed transcripts with Notion"""
    with app.app_context():
        try:
            logger.info("Starting Notion sync")
            
            # Initialize Notion service
            notion_service = NotionService()
            if not notion_service.headers:
                logger.info("Notion not configured, skipping sync")
                return
            
            # Get transcripts that need syncing
            unsynced_transcripts = db.session.query(Transcript)\
                .filter(Transcript.processing_status == 'completed')\
                .filter(Transcript.notion_synced == False)\
                .limit(10).all()  # Limit to avoid rate limiting
            
            if not unsynced_transcripts:
                logger.info("No transcripts need Notion sync")
                return
            
            logger.info(f"Syncing {len(unsynced_transcripts)} transcripts with Notion")
            
            for transcript in unsynced_transcripts:
                try:
                    client = transcript.client
                    if not client or not client.notion_database_id:
                        logger.warning(f"Transcript {transcript.id} has no Notion database, skipping")
                        continue
                    
                    # Prepare session data
                    session_data = {
                        'original_filename': transcript.original_filename,
                        'session_date': transcript.session_date.isoformat() if transcript.session_date else None,
                        'consolidated_insights': transcript.therapy_insights or {}
                    }
                    
                    # Add to Notion
                    page_id = notion_service.add_session_to_database(
                        client.notion_database_id,
                        session_data
                    )
                    
                    if page_id:
                        transcript.notion_page_id = page_id
                        transcript.notion_synced = True
                        transcript.notion_sync_error = None
                        logger.info(f"Synced transcript {transcript.id} to Notion page {page_id}")
                    else:
                        transcript.notion_sync_error = "Failed to create Notion page"
                        logger.error(f"Failed to sync transcript {transcript.id} to Notion")
                    
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error syncing transcript {transcript.id} to Notion: {str(e)}")
                    transcript.notion_sync_error = str(e)
                    db.session.commit()
            
            logger.info("Notion sync completed")
            
        except Exception as e:
            logger.error(f"Error during Notion sync: {str(e)}")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
