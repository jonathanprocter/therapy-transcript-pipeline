import os
import logging
import json
import requests
from datetime import datetime

class NotionIntegration:
    """
    Integrates with Notion API to create and update databases for clients.
    """
    
    def __init__(self, api_key, parent_page_id):
        """
        Initialize the Notion integration with API key and parent page ID.
        
        Args:
            api_key: Notion API key
            parent_page_id: ID of the parent page where databases will be created
        """
        self.api_key = api_key
        self.parent_page_id = parent_page_id
        self.logger = logging.getLogger(__name__)
        self.api_base = "https://api.notion.com/v1"
        self.client_databases = {}  # Cache of client database IDs
    
    def _get_headers(self):
        """Get the authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def find_client_database(self, client_name):
        """
        Find a database for a specific client.
        
        Args:
            client_name: Name of the client
            
        Returns:
            str: Database ID or None if not found
        """
        # Check cache first
        if client_name in self.client_databases:
            return self.client_databases[client_name]
        
        # Search for databases in the parent page
        try:
            response = requests.post(
                f"{self.api_base}/search",
                headers=self._get_headers(),
                json={
                    "query": client_name,
                    "filter": {
                        "property": "object",
                        "value": "database"
                    }
                }
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            # Find database with matching title
            for db in results:
                title = db.get("title", [])
                if title and title[0].get("text", {}).get("content") == f"{client_name} Sessions":
                    db_id = db.get("id")
                    self.client_databases[client_name] = db_id
                    return db_id
            
            return None
        except Exception as e:
            self.logger.error(f"Error finding client database: {str(e)}")
            return None
    
    def create_client_database(self, client_name):
        """
        Create a new database for a client.
        
        Args:
            client_name: Name of the client
            
        Returns:
            str: Database ID or None if creation fails
        """
        try:
            response = requests.post(
                f"{self.api_base}/databases",
                headers=self._get_headers(),
                json={
                    "parent": {
                        "type": "page_id",
                        "page_id": self.parent_page_id
                    },
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"{client_name} Sessions"
                            }
                        }
                    ],
                    "properties": {
                        "Session Date": {
                            "date": {}
                        },
                        "File Name": {
                            "rich_text": {}
                        },
                        "Notes": {
                            "rich_text": {}
                        },
                        "Title": {
                            "title": {}
                        }
                    }
                }
            )
            response.raise_for_status()
            db_id = response.json().get("id")
            self.client_databases[client_name] = db_id
            return db_id
        except Exception as e:
            self.logger.error(f"Error creating client database: {str(e)}")
            return None
    
    def add_session_to_database(self, client_name, file_name, processed_content):
        """
        Add a session to a client's database.
        
        Args:
            client_name: Name of the client
            file_name: Name of the file
            processed_content: Processed content from AI
            
        Returns:
            str: URL of the created page or None if creation fails
        """
        # Find or create database
        db_id = self.find_client_database(client_name)
        if not db_id:
            db_id = self.create_client_database(client_name)
            if not db_id:
                raise Exception(f"Failed to create database for client {client_name}")
        
        # Extract date from filename or use current date
        from datetime import datetime
        import re
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_name)
        if date_match:
            date_str = date_match.group(1)
        
        # Create page in database
        try:
            response = requests.post(
                f"{self.api_base}/pages",
                headers=self._get_headers(),
                json={
                    "parent": {
                        "database_id": db_id
                    },
                    "properties": {
                        "Title": {
                            "title": [
                                {
                                    "text": {
                                        "content": f"Session {date_str}"
                                    }
                                }
                            ]
                        },
                        "Session Date": {
                            "date": {
                                "start": date_str
                            }
                        },
                        "File Name": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": file_name
                                    }
                                }
                            ]
                        }
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": processed_content[:2000]  # Limit content length for API
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            )
            response.raise_for_status()
            page_id = response.json().get("id")
            
            # If content is longer than 2000 chars, append the rest
            if len(processed_content) > 2000:
                remaining_content = processed_content[2000:]
                chunks = [remaining_content[i:i+2000] for i in range(0, len(remaining_content), 2000)]
                
                for chunk in chunks:
                    self._append_content_to_page(page_id, chunk)
            
            return f"https://notion.so/{page_id.replace('-', '')}"
        except Exception as e:
            self.logger.error(f"Error adding session to database: {str(e)}")
            return None
    
    def _append_content_to_page(self, page_id, content):
        """
        Append content to an existing page.
        
        Args:
            page_id: ID of the page
            content: Content to append
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.patch(
                f"{self.api_base}/blocks/{page_id}/children",
                headers=self._get_headers(),
                json={
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": content
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error appending content to page: {str(e)}")
            return False
