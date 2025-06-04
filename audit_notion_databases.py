#!/usr/bin/env python3
"""
Audit existing Notion databases and fix issues
"""
import os
import sys
import logging
import requests
from datetime import datetime, timezone

# Add project root to path
sys.path.append('.')

from app import app, db
from models import Client, Transcript, ProcessingLog
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def audit_notion_databases():
    """Audit existing Notion databases and identify issues"""
    
    if not Config.NOTION_INTEGRATION_SECRET or not Config.NOTION_PARENT_PAGE_ID:
        logger.error("Notion credentials not configured")
        return
    
    notion_headers = {
        "Authorization": f"Bearer {Config.NOTION_INTEGRATION_SECRET}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Test connection
    response = requests.get("https://api.notion.com/v1/users/me", headers=notion_headers)
    if response.status_code != 200:
        logger.error(f"Notion connection failed: {response.status_code}")
        return
    
    logger.info("Notion connection successful")
    
    # Get all children of the parent page to see existing databases
    try:
        response = requests.get(
            f"https://api.notion.com/v1/blocks/{Config.NOTION_PARENT_PAGE_ID}/children",
            headers=notion_headers
        )
        
        if response.status_code == 200:
            children = response.json().get('results', [])
            
            databases = []
            for child in children:
                if child.get('type') == 'child_database':
                    title = ''
                    if child.get('child_database', {}).get('title'):
                        title = child['child_database']['title']
                    databases.append({
                        'id': child['id'],
                        'title': title,
                        'type': child['type']
                    })
            
            logger.info(f"Found {len(databases)} databases in parent page:")
            for db in databases:
                logger.info(f"  - {db['title']} (ID: {db['id']})")
            
            # Check for duplicates
            titles = [db['title'] for db in databases]
            duplicates = []
            for title in set(titles):
                if titles.count(title) > 1:
                    duplicates.append(title)
            
            if duplicates:
                logger.warning(f"Found duplicate database titles: {duplicates}")
            
            return databases
        else:
            logger.error(f"Failed to get parent page children: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error auditing databases: {str(e)}")
        return []

def check_database_content(database_id: str, notion_headers: dict):
    """Check the content of a specific database"""
    
    try:
        # Get database properties
        response = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=notion_headers
        )
        
        if response.status_code == 200:
            db_info = response.json()
            title = db_info.get('title', [{}])[0].get('text', {}).get('content', 'Unknown')
            properties = db_info.get('properties', {})
            
            logger.info(f"Database: {title}")
            logger.info(f"  Properties: {list(properties.keys())}")
            
            # Query database pages
            response = requests.post(
                f"https://api.notion.com/v1/databases/{database_id}/query",
                headers=notion_headers,
                json={}
            )
            
            if response.status_code == 200:
                pages = response.json().get('results', [])
                logger.info(f"  Pages: {len(pages)}")
                
                for page in pages[:3]:  # Check first 3 pages
                    page_title = 'Unknown'
                    if page.get('properties', {}).get('Session Title', {}).get('title'):
                        page_title = page['properties']['Session Title']['title'][0]['text']['content']
                    
                    logger.info(f"    - {page_title}")
                    
                    # Check if content has markdown
                    page_id = page['id']
                    content_response = requests.get(
                        f"https://api.notion.com/v1/blocks/{page_id}/children",
                        headers=notion_headers
                    )
                    
                    if content_response.status_code == 200:
                        blocks = content_response.json().get('results', [])
                        for block in blocks[:2]:  # Check first 2 blocks
                            if block.get('type') == 'paragraph':
                                text = block.get('paragraph', {}).get('rich_text', [])
                                if text:
                                    content = text[0].get('text', {}).get('content', '')
                                    if '#' in content or '**' in content or '*' in content:
                                        logger.warning(f"      Found markdown in content: {content[:100]}...")
            
        else:
            logger.error(f"Failed to get database info: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error checking database content: {str(e)}")

def main():
    """Main audit function"""
    
    with app.app_context():
        logger.info("Starting Notion database audit...")
        
        # Audit existing databases
        databases = audit_notion_databases()
        
        if databases:
            notion_headers = {
                "Authorization": f"Bearer {Config.NOTION_INTEGRATION_SECRET}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Check content of each database
            for db in databases:
                check_database_content(db['id'], notion_headers)
        
        # Check what clients should have databases
        with app.app_context():
            clients = db.session.query(Client).all()
            logger.info(f"Database clients: {len(clients)} total clients")
            
            kristi_clients = db.session.query(Client).filter(
                Client.name.like('%Kristi%')
            ).all()
            
            logger.info(f"Kristi Rook entries: {len(kristi_clients)}")
            for client in kristi_clients:
                logger.info(f"  - Client ID {client.id}: {client.name} (DB: {client.notion_database_id})")
                
                transcripts = db.session.query(Transcript).filter(
                    Transcript.client_id == client.id
                ).all()
                logger.info(f"    Transcripts: {len(transcripts)}")

if __name__ == "__main__":
    main()