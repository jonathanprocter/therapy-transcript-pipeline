#!/usr/bin/env python3
"""
Fix the actual Notion issues identified in the audit
"""
import os
import sys
import logging
import requests
import json
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

def get_notion_headers():
    return {
        "Authorization": f"Bearer {Config.NOTION_INTEGRATION_SECRET}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def delete_duplicate_databases():
    """Delete duplicate databases keeping only one per client"""
    
    headers = get_notion_headers()
    
    # Get all databases in parent page
    response = requests.get(
        f"https://api.notion.com/v1/blocks/{Config.NOTION_PARENT_PAGE_ID}/children",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get databases: {response.status_code}")
        return
    
    children = response.json().get('results', [])
    databases = {}
    
    for child in children:
        if child.get('type') == 'child_database':
            title = child.get('child_database', {}).get('title', '')
            db_id = child['id']
            
            if title in databases:
                # This is a duplicate - delete it
                logger.info(f"Deleting duplicate database: {title}")
                delete_response = requests.delete(
                    f"https://api.notion.com/v1/blocks/{db_id}",
                    headers=headers
                )
                if delete_response.status_code == 200:
                    logger.info(f"Successfully deleted duplicate: {title}")
                else:
                    logger.error(f"Failed to delete duplicate: {delete_response.status_code}")
            else:
                databases[title] = db_id
    
    return databases

def create_kristi_rook_database():
    """Create proper database for Kristi Rook"""
    
    headers = get_notion_headers()
    
    database_data = {
        "parent": {"page_id": Config.NOTION_PARENT_PAGE_ID},
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Kristi Rook - Therapy Sessions"
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
            "Intensity": {
                "number": {
                    "format": "percent"
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
            "Progress Notes": {
                "rich_text": {}
            },
            "Action Items": {
                "rich_text": {}
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
        headers=headers,
        json=database_data
    )
    
    if response.status_code == 200:
        db_id = response.json().get('id')
        logger.info(f"Created Kristi Rook database: {db_id}")
        return db_id
    else:
        logger.error(f"Failed to create Kristi Rook database: {response.status_code} - {response.text}")
        return None

def get_proper_clinical_note(transcript):
    """Get the actual clinical progress note from the therapy analysis prompt"""
    
    # Check if we have OpenAI analysis
    if transcript.openai_analysis:
        analysis = transcript.openai_analysis
        if isinstance(analysis, dict):
            # Look for the clinical progress note
            if 'clinical_progress_note' in analysis:
                return analysis['clinical_progress_note']
            elif 'analysis' in analysis:
                return analysis['analysis']
    
    # Check Anthropic analysis
    if transcript.anthropic_analysis:
        analysis = transcript.anthropic_analysis
        if isinstance(analysis, dict):
            if 'clinical_progress_note' in analysis:
                return analysis['clinical_progress_note']
            elif 'analysis' in analysis:
                return analysis['analysis']
    
    # Check Gemini analysis
    if transcript.gemini_analysis:
        analysis = transcript.gemini_analysis
        if isinstance(analysis, dict):
            if 'clinical_progress_note' in analysis:
                return analysis['clinical_progress_note']
            elif 'analysis' in analysis:
                return analysis['analysis']
    
    return None

def create_proper_clinical_pages():
    """Create proper clinical progress note pages following the exact therapy prompt format"""
    
    headers = get_notion_headers()
    
    with app.app_context():
        # Get Kristi Rook transcripts
        kristi_client = db.session.query(Client).filter(
            Client.name == 'Kristi Rook'
        ).first()
        
        if not kristi_client:
            logger.error("Kristi Rook client not found")
            return
        
        # Get her database ID
        kristi_db_id = create_kristi_rook_database()
        if not kristi_db_id:
            return
        
        # Update client with database ID
        kristi_client.notion_database_id = kristi_db_id
        db.session.commit()
        
        # Get her transcripts
        transcripts = db.session.query(Transcript).filter(
            Transcript.client_id == kristi_client.id
        ).all()
        
        logger.info(f"Creating {len(transcripts)} clinical progress notes for Kristi Rook")
        
        for transcript in transcripts:
            clinical_note = get_proper_clinical_note(transcript)
            
            if not clinical_note:
                logger.warning(f"No clinical note found for {transcript.original_filename}")
                continue
            
            # Format session date
            session_date = transcript.session_date
            if session_date:
                if isinstance(session_date, str):
                    formatted_date = session_date
                else:
                    formatted_date = session_date.strftime('%Y-%m-%d')
            else:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
            # Create page properties
            properties = {
                "Session Title": {
                    "title": [
                        {
                            "text": {
                                "content": f"Clinical Progress Note - {formatted_date}"
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
            
            # Strip markdown and create proper rich text blocks
            clean_text = clinical_note.replace('**', '').replace('*', '').replace('#', '').replace('`', '')
            
            # Split into manageable chunks (Notion has 2000 char limit per block)
            chunks = []
            remaining = clean_text
            max_chunk = 1900
            
            while remaining:
                if len(remaining) <= max_chunk:
                    chunks.append(remaining)
                    break
                
                # Find good break point at sentence end
                chunk = remaining[:max_chunk]
                break_point = max_chunk
                
                for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
                    if chunk[i] in '.!?':
                        break_point = i + 1
                        break
                
                chunks.append(remaining[:break_point])
                remaining = remaining[break_point:]
            
            # Create content blocks
            content_blocks = []
            for chunk in chunks:
                if chunk.strip():
                    content_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": chunk.strip()
                                    }
                                }
                            ]
                        }
                    })
            
            # Create the page
            page_data = {
                "parent": {"database_id": kristi_db_id},
                "properties": properties,
                "children": content_blocks
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=page_data
            )
            
            if response.status_code == 200:
                page_id = response.json().get('id')
                logger.info(f"Created clinical note page: {transcript.original_filename}")
                
                # Update transcript
                transcript.notion_page_id = page_id
                transcript.notion_synced = True
                transcript.notion_sync_error = None
                
            else:
                logger.error(f"Failed to create page: {response.status_code} - {response.text}")
                transcript.notion_sync_error = f"Failed: {response.status_code}"
        
        db.session.commit()

def main():
    """Main function to fix all Notion issues"""
    
    logger.info("Starting Notion fixes...")
    
    # 1. Delete duplicate databases
    logger.info("Step 1: Deleting duplicate databases")
    remaining_databases = delete_duplicate_databases()
    
    # 2. Create Kristi Rook database and pages
    logger.info("Step 2: Creating Kristi Rook database and clinical notes")
    create_proper_clinical_pages()
    
    # 3. Log completion
    with app.app_context():
        log_entry = ProcessingLog(
            activity_type='notion_fix_complete',
            status='success',
            message='Fixed Notion integration: removed duplicates, created Kristi Rook database with proper clinical notes',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()
    
    logger.info("Notion fixes completed")

if __name__ == "__main__":
    main()