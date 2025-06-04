import sys
import os
sys.path.append('/home/ubuntu/full_integration_app/src')

from pdf_extractor import PDFExtractor
from ai_processor import AIProcessor
from notion_integration import NotionIntegration
from processing_pipeline import ProcessingPipeline
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_full_pipeline():
    """Validate the full processing pipeline with a sample PDF"""
    try:
        # Create configuration with dummy keys
        config = {
            'dropbox_token': 'dummy_dropbox_token',
            'openai_key': 'dummy_openai_key',
            'claude_key': 'dummy_claude_key',
            'gemini_key': 'dummy_gemini_key',
            'notion_key': 'dummy_notion_key',
            'notion_parent_id': 'dummy_notion_parent_id',
            'dropbox_folder': '/apps/otter'
        }
        
        # Initialize the processing pipeline
        logger.info("Initializing processing pipeline")
        pipeline = ProcessingPipeline(config)
        
        # Override AI processor and Notion integration with mock implementations
        logger.info("Setting up mock implementations")
        
        # Mock AI processor
        original_ai_process = pipeline.ai_processor.process_transcript
        pipeline.ai_processor.process_transcript = lambda text: "This is a mock AI processed transcript response with comprehensive analysis."
        
        # Mock Notion integration
        original_notion_add = pipeline.notion.add_session_to_database
        pipeline.notion.add_session_to_database = lambda client_name, file_name, processed_content: f"https://notion.so/mock-page-id-for-{client_name.replace(' ', '-').lower()}"
        
        # Process a sample PDF
        sample_pdf_path = os.path.join(os.path.dirname(__file__), 'test_files', 'John_Smith_2025-06-04.pdf')
        logger.info(f"Processing sample PDF: {sample_pdf_path}")
        
        if not os.path.exists(sample_pdf_path):
            logger.error(f"Sample PDF not found at {sample_pdf_path}")
            return False
        
        result = pipeline.process_file(sample_pdf_path)
        
        # Restore original methods
        pipeline.ai_processor.process_transcript = original_ai_process
        pipeline.notion.add_session_to_database = original_notion_add
        
        # Check result
        if result.get('success', False):
            logger.info("Full pipeline validation successful!")
            logger.info(f"Client name: {result.get('client_name')}")
            logger.info(f"Notion URL: {result.get('notion_url')}")
            return True
        else:
            logger.error(f"Pipeline validation failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"Error in full pipeline validation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    validate_full_pipeline()
