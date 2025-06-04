import sys
import os
sys.path.append('/home/ubuntu/full_integration_app/src')

from dropbox_direct_api import DropboxDirectAPI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dropbox_api():
    """Test Dropbox API functionality with a dummy token"""
    try:
        # Initialize with dummy token
        logger.info("Initializing Dropbox API with dummy token")
        dropbox_api = DropboxDirectAPI('dummy_token_for_testing')
        
        # Test list_folder method
        logger.info("Testing list_folder method")
        try:
            files = dropbox_api.list_folder()
            logger.info(f"Files found: {len(files.get('entries', []))}")
            logger.info(f"Response structure: {files.keys()}")
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
        
        # Test get_new_files method
        logger.info("Testing get_new_files method")
        try:
            new_files = dropbox_api.get_new_files()
            logger.info(f"New files found: {len(new_files)}")
        except Exception as e:
            logger.error(f"Error getting new files: {str(e)}")
        
        # Test process_new_files method
        logger.info("Testing process_new_files method")
        try:
            download_dir = os.path.join(os.path.dirname(__file__), 'uploads')
            os.makedirs(download_dir, exist_ok=True)
            
            def dummy_callback(file_path):
                logger.info(f"Callback called with file: {file_path}")
            
            processed = dropbox_api.process_new_files(download_dir, callback=dummy_callback)
            logger.info(f"Processed files: {len(processed)}")
        except Exception as e:
            logger.error(f"Error processing new files: {str(e)}")
        
        logger.info("Dropbox API tests completed")
        
    except Exception as e:
        logger.error(f"Error in Dropbox API test: {str(e)}")

if __name__ == "__main__":
    test_dropbox_api()
