import os
import logging
import tempfile
from datetime import datetime, timedelta
import time
import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import FileMetadata, FolderMetadata

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DropboxIntegration:
    def __init__(self, access_token, folder_path='/apps/otter'):
        """
        Initialize Dropbox integration with the provided access token.
        
        Args:
            access_token (str): Dropbox API access token
            folder_path (str): Path to monitor in Dropbox
        """
        self.access_token = access_token
        self.folder_path = folder_path
        self.dbx = None
        self.cursor = None
        self.last_check_time = datetime.now() - timedelta(hours=1)  # Start by checking files from the last hour
        
    def connect(self):
        """Establish connection to Dropbox API"""
        try:
            self.dbx = dropbox.Dropbox(self.access_token)
            # Test the connection
            account = self.dbx.users_get_current_account()
            logger.info(f"Connected to Dropbox account: {account.name.display_name}")
            return True
        except AuthError as e:
            logger.error(f"Dropbox authentication error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Dropbox connection error: {str(e)}")
            return False
    
    def list_files(self):
        """
        List all files in the specified Dropbox folder
        
        Returns:
            list: List of file metadata objects
        """
        if not self.dbx:
            if not self.connect():
                return []
        
        try:
            result = self.dbx.files_list_folder(self.folder_path)
            files = []
            
            # Process entries
            for entry in result.entries:
                if isinstance(entry, FileMetadata) and entry.name.lower().endswith('.pdf'):
                    files.append({
                        'name': entry.name,
                        'path': entry.path_display,
                        'id': entry.id,
                        'modified': entry.server_modified,
                        'size': entry.size
                    })
            
            # If there are more files, continue listing
            while result.has_more:
                result = self.dbx.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    if isinstance(entry, FileMetadata) and entry.name.lower().endswith('.pdf'):
                        files.append({
                            'name': entry.name,
                            'path': entry.path_display,
                            'id': entry.id,
                            'modified': entry.server_modified,
                            'size': entry.size
                        })
            
            return files
        except ApiError as e:
            logger.error(f"Dropbox API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error listing Dropbox files: {str(e)}")
            return []
    
    def get_new_files(self):
        """
        Get new PDF files added since the last check
        
        Returns:
            list: List of new file metadata objects
        """
        all_files = self.list_files()
        new_files = [f for f in all_files if f['modified'] > self.last_check_time]
        self.last_check_time = datetime.now()
        return new_files
    
    def download_file(self, file_path):
        """
        Download a file from Dropbox
        
        Args:
            file_path (str): Path to the file in Dropbox
            
        Returns:
            str: Path to the downloaded file (temporary file)
            None: If download fails
        """
        if not self.dbx:
            if not self.connect():
                return None
        
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download the file
            self.dbx.files_download_to_file(temp_path, file_path)
            logger.info(f"Downloaded file from {file_path} to {temp_path}")
            return temp_path
        except ApiError as e:
            logger.error(f"Dropbox API error downloading {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {str(e)}")
            return None
    
    def setup_longpoll(self):
        """
        Set up long polling for folder changes
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if not self.dbx:
            if not self.connect():
                return False
        
        try:
            result = self.dbx.files_list_folder(self.folder_path)
            self.cursor = result.cursor
            return True
        except Exception as e:
            logger.error(f"Error setting up longpoll: {str(e)}")
            return False
    
    def check_for_changes(self, timeout=30):
        """
        Check for changes in the monitored folder using longpoll
        
        Args:
            timeout (int): Timeout in seconds for the longpoll request
            
        Returns:
            bool: True if changes detected, False otherwise
        """
        if not self.cursor:
            if not self.setup_longpoll():
                return False
        
        try:
            result = self.dbx.files_list_folder_longpoll(self.cursor, timeout)
            if result.changes:
                # Update cursor
                result = self.dbx.files_list_folder_continue(self.cursor)
                self.cursor = result.cursor
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking for changes: {str(e)}")
            self.cursor = None  # Reset cursor to force setup on next check
            return False
    
    def monitor_folder(self, callback, interval=60):
        """
        Monitor the folder for new PDF files and process them
        
        Args:
            callback (function): Function to call with the path to each new file
            interval (int): Polling interval in seconds
        """
        logger.info(f"Starting to monitor Dropbox folder: {self.folder_path}")
        
        while True:
            try:
                # Get new files
                new_files = self.get_new_files()
                
                # Process each new file
                for file_info in new_files:
                    if file_info['name'].lower().endswith('.pdf'):
                        logger.info(f"New PDF file detected: {file_info['name']}")
                        local_path = self.download_file(file_info['path'])
                        if local_path:
                            try:
                                # Call the callback function with the file info and local path
                                callback(file_info, local_path)
                            except Exception as e:
                                logger.error(f"Error in callback for file {file_info['name']}: {str(e)}")
                            finally:
                                # Clean up the temporary file
                                try:
                                    os.unlink(local_path)
                                except:
                                    pass
                
                # Wait for the next check
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitor_folder: {str(e)}")
                time.sleep(interval)  # Wait before retrying

# Example usage
if __name__ == "__main__":
    # This is just for testing
    access_token = "YOUR_DROPBOX_ACCESS_TOKEN"
    folder_path = "/apps/otter"
    
    def process_file(file_info, local_path):
        print(f"Processing file: {file_info['name']} at {local_path}")
        # Add your processing logic here
    
    dropbox_client = DropboxIntegration(access_token, folder_path)
    dropbox_client.monitor_folder(process_file)
