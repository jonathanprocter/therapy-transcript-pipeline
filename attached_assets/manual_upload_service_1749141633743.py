import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import logging

# Assuming 'app' is the Flask application instance and 'db' is SQLAlchemy instance
# If 'app' is not directly importable due to circular dependencies, 'db' might need to be passed
# into the service or accessed via current_app.extensions['sqlalchemy'].db
# For now, attempting direct import as seen in routes.py pattern.
from app import db
from models import Client, Transcript
from src.processing_pipeline import ProcessingPipeline # Ensure this path is correct

logger = logging.getLogger(__name__)

class ManualUploadService:
    def __init__(self, ai_service=None): # Added ai_service dependency
        """
        Initializes the ManualUploadService.
        Accepts an AIService instance for deeper AI functionalities.
        Gathers API keys needed for the ProcessingPipeline.
        """
        self.api_keys = {
            'dropbox_token': os.environ.get('DROPBOX_ACCESS_TOKEN'),
            'openai_key': os.environ.get('OPENAI_API_KEY'),
            'claude_key': os.environ.get('ANTHROPIC_API_KEY'),
            'gemini_key': os.environ.get('GEMINI_API_KEY'),
            'notion_key': os.environ.get('NOTION_INTEGRATION_SECRET'),
            'notion_parent_id': os.environ.get('NOTION_DATABASE_ID'), # This might be the main one, not client-specific
            'dropbox_folder': os.environ.get('DROPBOX_FOLDER', '/apps/otter') # Added default
        }
        self.ai_service = ai_service # Store AIService instance
        if not self.ai_service:
            logger.warning("ManualUploadService initialized without AIService. Case conceptualization will be skipped.")
        # Note: ProcessingPipeline is instantiated per-call in handle_file_upload

    def handle_file_upload(self, uploaded_file_storage):
        """
        Handles the manual file upload process.

        Args:
            uploaded_file_storage: The FileStorage object from Flask's request.files.

        Returns:
            A dictionary with:
                'success': bool,
                'message': str (on success),
                'client_name': str (on success, optional),
                'error': str (on failure)
        """
        if not uploaded_file_storage:
            return {'success': False, 'error': 'No file provided.'}
        if not uploaded_file_storage.filename: # Check if filename is not empty or None
            return {'success': False, 'error': 'File has no name.'}

        original_filename = uploaded_file_storage.filename
        allowed_extensions = {'pdf', 'txt', 'docx'}
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

        if not file_extension or file_extension not in allowed_extensions:
            logger.warning(f"Invalid file type uploaded: {original_filename} (extension: {file_extension})")
            return {'success': False, 'error': 'Invalid file type. Please upload PDF, TXT, or DOCX files.'}

        filename = secure_filename(original_filename)
        temp_file_path = None

        try:
            # Create a temporary file with the correct suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_fp:
                temp_file_path = temp_fp.name
                uploaded_file_storage.save(temp_file_path)
            
            logger.info(f"Uploaded file saved temporarily as: {temp_file_path} (original: {filename})")

            # Initialize and execute ProcessingPipeline
            # It's good practice to instantiate dependencies where they are used if their config can change
            # or if they are not lightweight. Here, api_keys are stable per service instance.
            pipeline = ProcessingPipeline(self.api_keys)
            pipeline_result = pipeline.process_single_file(temp_file_path)

            if not pipeline_result or not isinstance(pipeline_result, dict):
                 logger.error(f"ProcessingPipeline returned invalid result for {filename}: {pipeline_result}")
                 return {'success': False, 'error': 'Error processing file: Invalid result from processing pipeline.'}

            if pipeline_result.get("success", False):
                client_name = pipeline_result.get("client_name")
                if not client_name: # Handle cases where client_name might be missing from pipeline_result
                    logger.warning(f"Client name missing from pipeline result for {filename}. Defaulting to 'Unknown Client'.")
                    client_name = "Unknown Client"
                
                # Find or Create Client
                client = db.session.query(Client).filter(Client.name.ilike(client_name)).first()
                if not client:
                    logger.info(f"Creating new client: {client_name}")
                    client = Client(name=client_name)
                    db.session.add(client)
                    db.session.flush() # Flush to get client.id before creating transcript
                else:
                    logger.info(f"Found existing client: {client_name} (ID: {client.id})")
                
                # Create Transcript record
                transcript = Transcript(
                    client_id=client.id,
                    original_filename=filename,
                    dropbox_path=f"manual_upload/{filename}", # Indicate it's a manual upload
                    file_type=file_extension,
                    raw_content=pipeline_result.get("content", ""),
                    processing_status='completed', # Assuming pipeline success means completion
                    processed_at=datetime.now(timezone.utc),
                    notion_synced=bool(pipeline_result.get("notion_url")), # Ensure boolean
                    # Storing analysis results if available from pipeline_result
                    openai_analysis=pipeline_result.get("openai_analysis"),
                    anthropic_analysis=pipeline_result.get("anthropic_analysis"),
                    gemini_analysis=pipeline_result.get("gemini_analysis"),
                    sentiment_score=pipeline_result.get("sentiment_score"),
                    key_themes=pipeline_result.get("key_themes", []), # Default to empty list
                    therapy_insights=pipeline_result.get("therapy_insights_summary") or pipeline_result.get("therapy_insights"), # Prefer summary
                    progress_indicators=pipeline_result.get("progress_indicators"),
                    # New fields for Case Conceptualization
                    session_complaints=pipeline_result.get('session_complaints', []),
                    session_concerns=pipeline_result.get('session_concerns', []),
                    session_action_items=pipeline_result.get('session_action_items', []),
                    session_presentation_summary=pipeline_result.get('session_presentation_summary')
                )
                db.session.add(transcript)
                # Commit client (if new) and transcript together
                db.session.commit() 
                logger.info(f"Successfully processed and saved transcript for client: {client_name} (Client ID: {client.id}, Transcript ID: {transcript.id})")

                # Attempt to update Case Conceptualization if AIService is available
                if self.ai_service and client:
                    try:
                        existing_conceptualization = client.current_case_conceptualization
                        
                        # Prepare current session data for conceptualization prompt
                        # This dict should match what _format_session_for_conceptualization_prompt expects
                        # It's crucial that pipeline_result contains all these fields from analyze_transcript_detailed
                        current_session_analysis_dict = {
                            'session_date': transcript.session_date.isoformat() if transcript.session_date else datetime.now(timezone.utc).isoformat(),
                            'session_complaints': transcript.session_complaints,
                            'session_concerns': transcript.session_concerns,
                            'key_themes': transcript.key_themes,
                            'session_presentation_summary': transcript.session_presentation_summary,
                            'therapy_insights': transcript.therapy_insights, # This is the summary string
                            'session_action_items': transcript.session_action_items
                        }
                        
                        logger.info(f"Updating case conceptualization for client ID: {client.id} after manual upload (Transcript ID: {transcript.id})")
                        updated_conceptualization_text = self.ai_service.update_case_conceptualization(
                            existing_conceptualization,
                            [current_session_analysis_dict] # Pass as a list of one session
                        )

                        if updated_conceptualization_text:
                            client.current_case_conceptualization = updated_conceptualization_text
                            client.case_conceptualization_updated_at = datetime.now(timezone.utc)
                            db.session.commit() # Commit client update in a separate transaction
                            logger.info(f"Case conceptualization updated for client ID: {client.id} via manual upload.")
                        else:
                            logger.warning(f"Case conceptualization update returned None for client ID: {client.id} via manual upload.")
                    
                    except Exception as e_concept:
                        db.session.rollback() # Rollback client update if conceptualization failed
                        logger.error(f"Error updating case conceptualization for client ID {client.id} via manual upload: {str(e_concept)}")
                
                return {
                    'success': True, 
                    'message': f'Successfully processed transcript for {client_name}!',
                    'client_name': client_name,
                    'transcript_id': transcript.id # Return transcript_id for potential further use
                }
            else:
                error_message = pipeline_result.get("error", "Unknown error during file processing pipeline.")
                logger.warning(f"File processing pipeline failed for {filename}: {error_message}")
                return {
                    'success': False, 
                    'error': error_message
                }

        except Exception as e:
            logger.exception(f"Critical error in handle_file_upload for {filename}: {e}") # logger.exception includes stack trace
            db.session.rollback() # Rollback in case of DB errors during commit
            return {'success': False, 'error': f'An unexpected internal error occurred. Please check logs.'} # Generic message
        
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Temporary file {temp_file_path} deleted.")
                except Exception as e:
                    logger.error(f"Error removing temp file {temp_file_path}: {e}")
