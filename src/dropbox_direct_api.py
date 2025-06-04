import os
import logging
import requests
import json
import time
from datetime import datetime

class DropboxDirectAPI:
    """
    A simplified Dropbox integration using direct API calls instead of the full SDK
    to avoid compatibility issues with Python 3.12+ environments.
    """
    
    def __init__(self, access_token, folder_path='/apps/otter'):
        self.access_token = access_token
        self.folder_path = folder_path
        self.api_base = 'https://api.dropboxapi.com/2'
        self.content_api_base = 'https://content.dropboxapi.com/2'
        self.logger = logging.getLogger(__name__)
        
    def _get_headers(self, content_type='application/json'):
        """Get the authorization headers for API requests."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': content_type
        }
    
    def list_folder(self):
        """List files in the specified folder."""
        endpoint = f"{self.api_base}/files/list_folder"
        data = {
            "path": self.folder_path,
            "recursive": False,
            "include_media_info": False,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": False
        }
        
        try:
            response = requests.post(endpoint, headers=self._get_headers(), json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error listing folder: {str(e)}")
            return {"entries": []}
    
    def download_file(self, file_path, local_path):
        """Download a file from Dropbox to a local path."""
        endpoint = f"{self.content_api_base}/files/download"
        headers = self._get_headers('application/octet-stream')
        headers['Dropbox-API-Arg'] = json.dumps({"path": file_path})
        
        try:
            response = requests.post(endpoint, headers=headers, stream=True)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            self.logger.error(f"Error downloading file {file_path}: {str(e)}")
            return False
    
    def get_new_files(self, last_check_time=None):
        """Get new PDF files added since the last check time."""
        files_list = self.list_folder()
        new_files = []
        
        for entry in files_list.get('entries', []):
            if entry.get('.tag') == 'file' and entry.get('name', '').lower().endswith('.pdf'):
                server_modified = entry.get('server_modified')
                if server_modified and (not last_check_time or server_modified > last_check_time):
                    new_files.append({
                        'path': entry.get('path_lower'),
                        'name': entry.get('name'),
                        'modified': server_modified,
                        'size': entry.get('size')
                    })
        
        return new_files
    
    def process_new_files(self, download_dir, callback=None):
        """
        Check for new files and process them.
        
        Args:
            download_dir: Directory to download files to
            callback: Function to call with the local path of each downloaded file
        
        Returns:
            List of processed files
        """
        new_files = self.get_new_files()
        processed_files = []
        
        for file_info in new_files:
            file_path = file_info['path']
            file_name = file_info['name']
            local_path = os.path.join(download_dir, file_name)
            
            self.logger.info(f"Downloading {file_name} from Dropbox")
            if self.download_file(file_path, local_path):
                processed_files.append({
                    'dropbox_path': file_path,
                    'local_path': local_path,
                    'name': file_name
                })
                
                if callback and callable(callback):
                    callback(local_path)
        
        return processed_files
