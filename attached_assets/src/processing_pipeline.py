import os
import logging
import json
from datetime import datetime
from dropbox_direct_api import DropboxDirectAPI
from pdf_extractor import PDFExtractor
from ai_processor import AIProcessor
from notion_integration import NotionIntegration

class ProcessingPipeline:
    """
    Main processing pipeline that coordinates the workflow between
    Dropbox, PDF extraction, AI processing, and Notion integration.
    """
    
    def __init__(self, config):
        """
        Initialize the processing pipeline with configuration.
        
        Args:
            config: Dictionary containing API keys and configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Initialize components if API keys are available
        self.dropbox = None
        self.ai_processor = None
        self.notion = None
        
        if self.config.get('dropbox_token'):
            self.dropbox = DropboxDirectAPI(
                self.config['dropbox_token'],
                self.config.get('dropbox_folder', '/apps/otter')
            )
        
        # Initialize AI processor if any AI service is configured
        if any([
            self.config.get('openai_key'),
            self.config.get('claude_key'),
            self.config.get('gemini_key')
        ]):
            self.ai_processor = AIProcessor(
                openai_key=self.config.get('openai_key'),
                claude_key=self.config.get('claude_key'),
                gemini_key=self.config.get('gemini_key')
            )
        
        # Initialize Notion if configured
        if self.config.get('notion_key') and self.config.get('notion_parent_id'):
            self.notion = NotionIntegration(
                self.config['notion_key'],
                self.config['notion_parent_id']
            )
        
        self.pdf_extractor = PDFExtractor()
        self.is_running = False
        self.last_check_time = None
        self.processed_files = []
        self.failed_files = []
    
    def start_monitoring(self):
        """Start monitoring Dropbox for new files."""
        if not self.dropbox:
            self.logger.error("Dropbox not configured. Cannot start monitoring.")
            return False
        
        self.is_running = True
        self.last_check_time = datetime.now().isoformat()
        self.logger.info(f"Started monitoring Dropbox folder: {self.config.get('dropbox_folder', '/apps/otter')}")
        return True
    
    def stop_monitoring(self):
        """Stop monitoring Dropbox for new files."""
        self.is_running = False
        self.logger.info("Stopped monitoring Dropbox folder")
        return True
    
    def check_dropbox(self):
        """
        Check Dropbox for new files and process them.
        
        Returns:
            dict: Results of the check operation
        """
        if not self.dropbox:
            return {
                "success": False,
                "error": "Dropbox not configured",
                "files_processed": 0
            }
        
        try:
            processed = self.dropbox.process_new_files(
                self.upload_dir,
                callback=self.process_file
            )
            
            self.last_check_time = datetime.now().isoformat()
            
            return {
                "success": True,
                "files_processed": len(processed),
                "message": f"Processed {len(processed)} new files"
            }
        except Exception as e:
            self.logger.error(f"Error checking Dropbox: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "files_processed": 0
            }
    
    def process_file(self, file_path):
        """
        Process a single file through the pipeline.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            dict: Results of the processing
        """
        try:
            filename = os.path.basename(file_path)
            self.logger.info(f"Processing file: {filename}")
            
            # Extract client name from filename
            client_name = self.extract_client_name(filename)
            
            # Extract text from PDF
            text_content = self.pdf_extractor.extract_text(file_path)
            if not text_content:
                raise Exception("Failed to extract text from PDF")
            
            # If client name not found in filename, try to extract from content
            if not client_name:
                client_name = self.pdf_extractor.extract_client_name(text_content)
            
            if not client_name:
                client_name = "Unknown Client"
            
            # Process with AI
            if not self.ai_processor:
                raise Exception("AI processor not configured")
            
            processed_content = self.ai_processor.process_transcript(text_content)
            
            # Save to Notion
            if not self.notion:
                raise Exception("Notion integration not configured")
            
            notion_url = self.notion.add_session_to_database(
                client_name, 
                filename, 
                processed_content
            )
            
            result = {
                "success": True,
                "client_name": client_name,
                "file_name": filename,
                "notion_url": notion_url,
                "timestamp": datetime.now().isoformat()
            }
            
            self.processed_files.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            error_result = {
                "success": False,
                "file_name": os.path.basename(file_path),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.failed_files.append(error_result)
            return error_result
    
    def process_single_file(self, file_path):
        """
        Process a single file uploaded through the web interface.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            dict: Results of the processing
        """
        return self.process_file(file_path)
    
    def dropbox_callback(self, file_info, local_path):
        """
        Callback function for Dropbox file processing.
        
        Args:
            file_info: Information about the file from Dropbox
            local_path: Local path where the file was downloaded
            
        Returns:
            dict: Results of the processing
        """
        return self.process_file(local_path)
    
    def extract_client_name(self, filename):
        """
        Extract client name from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            str: Client name or None if not found
        """
        # Remove extension
        name_part = os.path.splitext(filename)[0]
        
        # Common patterns:
        # "Jonathan Procter 6-3-2025 1800 hrs"
        # "J Procter - Session Notes - 2025-06-03"
        
        # Try to find a name pattern (assuming name comes before date)
        parts = name_part.split()
        if len(parts) >= 2:
            # Assume first two parts might be first and last name
            potential_name = f"{parts[0]} {parts[1]}"
            
            # Check if the next part looks like a date
            if len(parts) > 2 and any(c in parts[2] for c in ['-', '/']):
                return potential_name
        
        return None
    
    def get_status(self):
        """
        Get the current status of the pipeline.
        
        Returns:
            dict: Status information
        """
        return {
            "is_running": self.is_running,
            "dropbox_folder": self.config.get('dropbox_folder', '/apps/otter'),
            "last_check_time": self.last_check_time,
            "processed_files": len(self.processed_files),
            "failed_files": len(self.failed_files),
            "ai_services_available": {
                "openai": bool(self.config.get('openai_key')),
                "claude": bool(self.config.get('claude_key')),
                "gemini": bool(self.config.get('gemini_key'))
            },
            "recent_processed": self.processed_files[-5:] if self.processed_files else [],
            "recent_failed": self.failed_files[-5:] if self.failed_files else []
        }
