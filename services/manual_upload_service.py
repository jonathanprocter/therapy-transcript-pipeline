
import os
import tempfile
import logging
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from app import db
from models import Client, Transcript

logger = logging.getLogger(__name__)

class ManualUploadService:
    """Service for handling manual file uploads"""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.allowed_extensions = {'pdf', 'txt', 'docx'}
    
    def handle_file_upload(self, file):
        """Handle uploaded file and process it"""
        try:
            if not file or not file.filename:
                return {'success': False, 'error': 'No file provided'}
            
            # Check file extension
            if not self._allowed_file(file.filename):
                return {'success': False, 'error': 'Invalid file type. Please upload PDF, TXT, or DOCX files.'}
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
                file_path = temp.name
                file.save(file_path)
            
            filename = secure_filename(file.filename)
            logger.info(f"Processing uploaded file: {filename}")
            
            try:
                # Extract content from file
                content = self._extract_content(file_path)
                
                if not content:
                    return {'success': False, 'error': 'Could not extract content from file'}
                
                # Create basic analysis if AI service is available
                analysis_result = {}
                if self.ai_service:
                    try:
                        analysis_result = self.ai_service.process_transcript(content)
                    except Exception as e:
                        logger.warning(f"AI analysis failed: {str(e)}")
                
                # Extract or generate client name
                client_name = self._extract_client_name(filename, content)
                
                # Create client record if it doesn't exist
                client = Client.query.filter_by(name=client_name).first()
                if not client:
                    client = Client(name=client_name)
                    db.session.add(client)
                    db.session.commit()
                
                # Create transcript record
                transcript = Transcript(
                    client_id=client.id,
                    original_filename=filename,
                    dropbox_path=f"manual_upload/{filename}",
                    file_type=filename.rsplit('.', 1)[1].lower(),
                    raw_content=content,
                    processing_status='completed',
                    processed_at=datetime.now(timezone.utc),
                    openai_analysis=analysis_result.get('openai_analysis'),
                    anthropic_analysis=analysis_result.get('anthropic_analysis'),
                    gemini_analysis=analysis_result.get('gemini_analysis'),
                    notion_synced=False
                )
                db.session.add(transcript)
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f'Successfully processed transcript for {client_name}!',
                    'client_name': client_name,
                    'transcript_id': transcript.id
                }
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Error removing temp file: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _extract_content(self, file_path):
        """Extract text content from uploaded file"""
        try:
            file_ext = file_path.split('.')[-1].lower()
            
            if file_ext == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_ext == 'pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        return text
                except ImportError:
                    logger.error("PyPDF2 not available for PDF processing")
                    return None
            
            elif file_ext == 'docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    logger.error("python-docx not available for DOCX processing")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return None
    
    def _extract_client_name(self, filename, content):
        """Extract client name from filename or content"""
        try:
            # Try to extract from filename pattern
            name_part = filename.replace('.pdf', '').replace('.txt', '').replace('.docx', '')
            
            # Look for common patterns like "FirstName_LastName_Date"
            if '_' in name_part:
                parts = name_part.split('_')
                if len(parts) >= 2:
                    # Assume first two parts are name
                    return f"{parts[0]} {parts[1]}"
            
            # If pattern doesn't work, use the whole filename (cleaned)
            return name_part.replace('_', ' ').title()
            
        except Exception as e:
            logger.error(f"Error extracting client name: {str(e)}")
            return "Unknown Client"
