import os
import logging
import dropbox
from typing import List, Dict, Optional
from datetime import datetime, timezone
from config import Config

logger = logging.getLogger(__name__)

class DropboxService:
    """Service for interacting with Dropbox API"""

    def __init__(self):
        """Initialize Dropbox service with API token"""
        try:
            # Force reload of environment variables
            import os
            from importlib import reload
            import config
            reload(config)

            self.access_token = os.environ.get('DROPBOX_ACCESS_TOKEN') or Config.DROPBOX_ACCESS_TOKEN
            self.monitor_folder = Config.DROPBOX_MONITOR_FOLDER

            if not self.access_token or self.access_token.startswith('your_'):
                logger.warning("Dropbox access token not configured properly")
                self.client = None
                return

            # Initialize with fresh token
            self.client = dropbox.Dropbox(self.access_token)

            # Test the connection immediately
            try:
                self.client.users_get_current_account()
                logger.info("Dropbox service initialized and authenticated successfully")
            except dropbox.exceptions.AuthError as e:
                logger.error(f"Dropbox authentication failed: {str(e)}")
                self.client = None

        except Exception as e:
            logger.error(f"Error initializing Dropbox service: {str(e)}")
            self.client = None

    def test_connection(self):
        """Test the Dropbox connection"""
        try:
            if not self.client:
                logger.warning("Dropbox client not initialized")
                return False

            account = self.client.users_get_current_account()
            logger.info(f"Dropbox connection successful. Account: {account.name.display_name}")
            return True

        except dropbox.exceptions.AuthError as e:
            logger.error(f"Dropbox authentication failed: {str(e)}")
            # Try to reinitialize with fresh token
            self.__init__()
            return False
        except Exception as e:
            logger.error(f"Dropbox connection test failed: {str(e)}")
            return False

    def list_files(self, folder_path: str = None) -> List[Dict]:
        """List files in the specified folder"""
        if folder_path is None:
            folder_path = self.monitor_folder

        try:
            files = []
            result = self.client.files_list_folder(folder_path)

            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    # Check if file type is supported
                    file_ext = os.path.splitext(entry.name)[1].lower()
                    if file_ext in Config.SUPPORTED_FILE_TYPES:
                        files.append({
                            'name': entry.name,
                            'path': entry.path_lower,
                            'size': entry.size,
                            'modified': entry.client_modified,
                            'content_hash': entry.content_hash
                        })

            # Handle pagination if there are more files
            while result.has_more:
                result = self.client.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        file_ext = os.path.splitext(entry.name)[1].lower()
                        if file_ext in Config.SUPPORTED_FILE_TYPES:
                            files.append({
                                'name': entry.name,
                                'path': entry.path_lower,
                                'size': entry.size,
                                'modified': entry.client_modified,
                                'content_hash': entry.content_hash
                            })

            logger.info(f"Found {len(files)} supported files in {folder_path}")
            return files

        except dropbox.exceptions.ApiError as e:
            logger.error(f"Dropbox API error while listing files: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while listing files: {str(e)}")
            return []

    def download_file(self, file_path: str) -> Optional[bytes]:
        """Download a file from Dropbox"""
        try:
            _, response = self.client.files_download(file_path)
            logger.info(f"Downloaded file: {file_path} ({len(response.content)} bytes)")
            return response.content
        except dropbox.exceptions.ApiError as e:
            logger.error(f"Dropbox API error while downloading {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while downloading {file_path}: {str(e)}")
            return None

    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        """Get metadata for a specific file"""
        try:
            metadata = self.client.files_get_metadata(file_path)
            if isinstance(metadata, dropbox.files.FileMetadata):
                return {
                    'name': metadata.name,
                    'path': metadata.path_lower,
                    'size': metadata.size,
                    'modified': metadata.client_modified,
                    'content_hash': metadata.content_hash
                }
        except dropbox.exceptions.ApiError as e:
            logger.error(f"Dropbox API error while getting metadata for {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while getting metadata for {file_path}: {str(e)}")
            return None

    def scan_for_new_files(self, processed_files: List[str]) -> List[Dict]:
        """Scan for new files that haven't been processed yet"""
        try:
            all_files = self.list_files()
            new_files = []

            for file_info in all_files:
                # Check if file has already been processed
                if file_info['path'] not in processed_files:
                    # Additional validation
                    if self._is_valid_file(file_info):
                        new_files.append(file_info)
                        logger.info(f"Found new file: {file_info['name']}")

            logger.info(f"Found {len(new_files)} new files to process")
            return new_files

        except Exception as e:
            logger.error(f"Error scanning for new files: {str(e)}")
            return []

    def _is_valid_file(self, file_info: Dict) -> bool:
        """Validate if a file should be processed"""
        # Check file size
        max_size_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_info['size'] > max_size_bytes:
            logger.warning(f"File {file_info['name']} is too large ({file_info['size']} bytes)")
            return False

        # Check file extension
        file_ext = os.path.splitext(file_info['name'])[1].lower()
        if file_ext not in Config.SUPPORTED_FILE_TYPES:
            logger.warning(f"File {file_info['name']} has unsupported extension: {file_ext}")
            return False

        # Check if file is recent (within last 30 days for initial processing)
        if file_info['modified']:
            # Ensure both datetimes are timezone-aware
            now_utc = datetime.now(timezone.utc)
            file_modified = file_info['modified']

            # Convert to UTC if naive datetime
            if file_modified.tzinfo is None:
                file_modified = file_modified.replace(tzinfo=timezone.utc)

            days_old = (now_utc - file_modified).days
            if days_old > 30:
                logger.info(f"Skipping old file {file_info['name']} (modified {days_old} days ago)")
                return False

        return True

    def create_backup_folder(self, folder_name: str) -> bool:
        """Create a backup folder for processed files"""
        try:
            backup_path = f"{self.monitor_folder}/processed/{folder_name}"
            self.client.files_create_folder_v2(backup_path)
            logger.info(f"Created backup folder: {backup_path}")
            return True
        except dropbox.exceptions.ApiError as e:
            if "path/conflict/folder" in str(e):
                logger.info(f"Backup folder already exists: {backup_path}")
                return True
            logger.error(f"Error creating backup folder: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating backup folder: {str(e)}")
            return False