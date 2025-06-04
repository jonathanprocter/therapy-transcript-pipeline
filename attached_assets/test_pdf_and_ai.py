import sys
import os
sys.path.append('/home/ubuntu/full_integration_app/src')

from pdf_extractor import PDFExtractor
from ai_processor import AIProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_extraction_and_ai_processing():
    """Test PDF extraction and AI processing with a sample PDF"""
    try:
        # Initialize PDF extractor
        logger.info("Initializing PDF extractor")
        pdf_extractor = PDFExtractor()
        
        # Test PDF extraction
        sample_pdf_path = os.path.join(os.path.dirname(__file__), 'test_files', 'John_Smith_2025-06-04.pdf')
        logger.info(f"Extracting text from {sample_pdf_path}")
        
        if not os.path.exists(sample_pdf_path):
            logger.error(f"Sample PDF not found at {sample_pdf_path}")
            return
        
        text_content = pdf_extractor.extract_text(sample_pdf_path)
        logger.info(f"Extracted text length: {len(text_content)}")
        logger.info(f"Sample text: {text_content[:200]}...")
        
        # Test client name extraction
        logger.info("Testing client name extraction")
        client_name = pdf_extractor.extract_client_name(text_content)
        logger.info(f"Extracted client name: {client_name}")
        
        # Initialize AI processor with dummy keys
        logger.info("Initializing AI processor with dummy keys")
        ai_processor = AIProcessor(
            openai_key="dummy_openai_key",
            claude_key="dummy_claude_key",
            gemini_key="dummy_gemini_key"
        )
        
        # Test AI processing with mock response
        logger.info("Testing AI processing with mock response")
        try:
            # Override the process_transcript method to return a mock response
            original_method = ai_processor.process_transcript
            ai_processor.process_transcript = lambda text: "This is a mock AI processed transcript response."
            
            processed_content = ai_processor.process_transcript(text_content)
            logger.info(f"Processed content length: {len(processed_content)}")
            logger.info(f"Processed content: {processed_content}")
            
            # Restore the original method
            ai_processor.process_transcript = original_method
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
        
        logger.info("PDF extraction and AI processing tests completed")
        
    except Exception as e:
        logger.error(f"Error in PDF extraction and AI processing test: {str(e)}")

if __name__ == "__main__":
    test_pdf_extraction_and_ai_processing()
