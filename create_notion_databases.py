#!/usr/bin/env python3
"""
Create Notion databases for clients and sync transcripts
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

def create_client_database(client_name: str, notion_headers: dict) -> str:
    """Create a Notion database for a client"""
    
    database_data = {
        "parent": {"page_id": Config.NOTION_PARENT_PAGE_ID},
        "title": [
            {
                "type": "text",
                "text": {
                    "content": f"{client_name} - Therapy Sessions"
                }
            }
        ],
        "properties": {
            "Session Title": {
                "title": {}
            },
            "Date": {
                "date": {}
            },
            "Session Type": {
                "select": {
                    "options": [
                        {"name": "Individual", "color": "blue"},
                        {"name": "Group", "color": "green"},
                        {"name": "Family", "color": "purple"}
                    ]
                }
            },
            "Primary Emotion": {
                "select": {
                    "options": [
                        {"name": "Content", "color": "default"},
                        {"name": "Hopeful", "color": "green"},
                        {"name": "Anxious", "color": "yellow"},
                        {"name": "Sad", "color": "blue"},
                        {"name": "Frustrated", "color": "orange"}
                    ]
                }
            },
            "Key Themes": {
                "multi_select": {
                    "options": [
                        {"name": "Progress", "color": "green"},
                        {"name": "Challenges", "color": "red"},
                        {"name": "Relationships", "color": "pink"},
                        {"name": "Coping", "color": "purple"}
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Completed", "color": "green"},
                        {"name": "In Progress", "color": "yellow"}
                    ]
                }
            }
        }
    }
    
    response = requests.post(
        "https://api.notion.com/v1/databases",
        headers=notion_headers,
        json=database_data
    )
    
    if response.status_code == 200:
        return response.json().get('id')
    else:
        logger.error(f"Failed to create database: {response.status_code} - {response.text}")
        return None

def create_transcript_page(database_id: str, transcript_data: dict, notion_headers: dict) -> str:
    """Create a transcript page in Notion database"""
    
    client_name = transcript_data.get('client_name', 'Unknown')
    session_date = transcript_data.get('session_date', datetime.now())
    
    if isinstance(session_date, str):
        formatted_date = session_date
    else:
        formatted_date = session_date.strftime('%Y-%m-%d')
    
    # Create page properties
    properties = {
        "Session Title": {
            "title": [
                {
                    "text": {
                        "content": f"Session {formatted_date} - {client_name}"
                    }
                }
            ]
        },
        "Date": {
            "date": {
                "start": formatted_date
            }
        },
        "Session Type": {
            "select": {
                "name": "Individual"
            }
        },
        "Primary Emotion": {
            "select": {
                "name": "Content"
            }
        },
        "Status": {
            "select": {
                "name": "Completed"
            }
        }
    }
    
    # Create content blocks from AI analyses
    content_blocks = []
    
    # Add analyses
    openai_analysis = transcript_data.get('openai_analysis', {})
    anthropic_analysis = transcript_data.get('anthropic_analysis', {})
    gemini_analysis = transcript_data.get('gemini_analysis', {})
    
    if openai_analysis:
        content_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "OpenAI Clinical Analysis"}}]
            }
        })
        
        analysis_text = str(openai_analysis.get('clinical_progress_note', openai_analysis))[:1900]
        content_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": analysis_text}}]
            }
        })
    
    if anthropic_analysis:
        content_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Anthropic Clinical Analysis"}}]
            }
        })
        
        analysis_text = str(anthropic_analysis.get('clinical_progress_note', anthropic_analysis))[:1900]
        content_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": analysis_text}}]
            }
        })
    
    if gemini_analysis:
        content_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Gemini Clinical Analysis"}}]
            }
        })
        
        analysis_text = str(gemini_analysis.get('clinical_progress_note', gemini_analysis))[:1900]
        content_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": analysis_text}}]
            }
        })
    
    # Create the page
    page_data = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "children": content_blocks
    }
    
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=notion_headers,
        json=page_data
    )
    
    if response.status_code == 200:
        return response.json().get('id')
    else:
        logger.error(f"Failed to create page: {response.status_code} - {response.text}")
        return None

def main():
    """Main function to create databases and sync transcripts"""
    
    with app.app_context():
        # Check Notion credentials
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
        
        # Get clients without databases
        clients_without_db = db.session.query(Client).filter(
            Client.notion_database_id.is_(None)
        ).all()
        
        logger.info(f"Found {len(clients_without_db)} clients without databases")
        
        for client in clients_without_db:
            logger.info(f"Creating database for: {client.name}")
            
            # Create database
            database_id = create_client_database(client.name, notion_headers)
            
            if database_id:
                client.notion_database_id = database_id
                db.session.commit()
                
                logger.info(f"Created database {database_id} for {client.name}")
                
                # Log success
                log_entry = ProcessingLog(
                    activity_type='notion_database_creation',
                    status='success',
                    message=f'Created Notion database for {client.name}',
                    context_metadata={'client_id': client.id, 'database_id': database_id},
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                
                # Sync transcripts
                transcripts = db.session.query(Transcript).filter(
                    Transcript.client_id == client.id,
                    Transcript.notion_synced == False
                ).all()
                
                logger.info(f"Syncing {len(transcripts)} transcripts for {client.name}")
                
                for transcript in transcripts:
                    transcript_data = {
                        'client_name': client.name,
                        'session_date': transcript.session_date,
                        'filename': transcript.original_filename,
                        'openai_analysis': transcript.openai_analysis,
                        'anthropic_analysis': transcript.anthropic_analysis,
                        'gemini_analysis': transcript.gemini_analysis
                    }
                    
                    page_id = create_transcript_page(database_id, transcript_data, notion_headers)
                    
                    if page_id:
                        transcript.notion_page_id = page_id
                        transcript.notion_synced = True
                        logger.info(f"Synced transcript: {transcript.original_filename}")
                        
                        # Log transcript sync
                        log_entry = ProcessingLog(
                            transcript_id=transcript.id,
                            activity_type='notion_sync',
                            status='success',
                            message=f'Synced {transcript.original_filename} to Notion',
                            created_at=datetime.now(timezone.utc)
                        )
                        db.session.add(log_entry)
                
                db.session.commit()
            else:
                logger.error(f"Failed to create database for {client.name}")
        
        # Final summary
        synced_count = db.session.query(Transcript).filter(Transcript.notion_synced == True).count()
        clients_with_db = db.session.query(Client).filter(Client.notion_database_id.isnot(None)).count()
        
        logger.info(f"Completed: {clients_with_db} clients with databases, {synced_count} transcripts synced")
        
        # Final log
        log_entry = ProcessingLog(
            activity_type='notion_integration_complete',
            status='success',
            message=f'Notion integration completed: {clients_with_db} clients with databases, {synced_count} transcripts synced',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()

if __name__ == "__main__":
    main()