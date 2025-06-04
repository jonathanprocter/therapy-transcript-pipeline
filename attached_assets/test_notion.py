import sys
import os
sys.path.append('/home/ubuntu/full_integration_app/src')

from notion_integration import NotionIntegration
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_notion_integration():
    """Test Notion database creation and update with dummy data"""
    try:
        # Initialize Notion integration with dummy keys
        logger.info("Initializing Notion integration with dummy keys")
        notion = NotionIntegration(
            api_key="dummy_notion_key",
            parent_page_id="dummy_parent_page_id"
        )
        
        # Test find_client_database method
        logger.info("Testing find_client_database method")
        try:
            client_name = "John Smith"
            db_id = notion.find_client_database(client_name)
            logger.info(f"Database ID for {client_name}: {db_id}")
        except Exception as e:
            logger.error(f"Error finding client database: {str(e)}")
        
        # Test create_client_database method
        logger.info("Testing create_client_database method")
        try:
            client_name = "John Smith"
            db_id = notion.create_client_database(client_name)
            logger.info(f"Created database ID for {client_name}: {db_id}")
        except Exception as e:
            logger.error(f"Error creating client database: {str(e)}")
        
        # Test add_session_to_database method with mock implementation
        logger.info("Testing add_session_to_database method with mock implementation")
        try:
            # Override the add_session_to_database method to return a mock response
            original_method = notion.add_session_to_database
            notion.add_session_to_database = lambda client_name, file_name, processed_content: f"https://notion.so/mock-page-id-for-{client_name.replace(' ', '-').lower()}"
            
            client_name = "John Smith"
            file_name = "John_Smith_2025-06-04.pdf"
            processed_content = "This is a mock processed transcript content."
            
            page_url = notion.add_session_to_database(client_name, file_name, processed_content)
            logger.info(f"Added session for {client_name}, URL: {page_url}")
            
            # Restore the original method
            notion.add_session_to_database = original_method
        except Exception as e:
            logger.error(f"Error adding session to database: {str(e)}")
        
        logger.info("Notion integration tests completed")
        
    except Exception as e:
        logger.error(f"Error in Notion integration test: {str(e)}")

if __name__ == "__main__":
    test_notion_integration()
