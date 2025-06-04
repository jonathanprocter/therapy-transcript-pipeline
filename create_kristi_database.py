#!/usr/bin/env python3
"""
Create Kristi Rook's database and proper clinical notes
"""
import os
import sys
import requests
import json
from datetime import datetime

sys.path.append('.')
from app import app, db
from models import Client, Transcript
from config import Config

def create_kristi_database():
    headers = {
        "Authorization": f"Bearer {Config.NOTION_INTEGRATION_SECRET}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Create database for Kristi Rook
    database_data = {
        "parent": {"page_id": Config.NOTION_PARENT_PAGE_ID},
        "title": [{"type": "text", "text": {"content": "Kristi Rook - Therapy Sessions"}}],
        "properties": {
            "Session Title": {"title": {}},
            "Date": {"date": {}},
            "Session Type": {
                "select": {
                    "options": [
                        {"name": "Individual", "color": "blue"},
                        {"name": "Group", "color": "green"}
                    ]
                }
            },
            "Primary Emotion": {
                "select": {
                    "options": [
                        {"name": "Content", "color": "default"},
                        {"name": "Hopeful", "color": "green"},
                        {"name": "Anxious", "color": "yellow"}
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
        headers=headers,
        json=database_data
    )
    
    if response.status_code == 200:
        return response.json().get('id')
    else:
        print(f"Failed to create database: {response.status_code} - {response.text}")
        return None

def create_clinical_note_page(database_id, transcript, headers):
    # Get the actual clinical analysis text
    clinical_text = ""
    
    if transcript.openai_analysis and isinstance(transcript.openai_analysis, dict):
        clinical_text = transcript.openai_analysis.get('clinical_progress_note', 
                                                     transcript.openai_analysis.get('analysis', ''))
    
    if not clinical_text and transcript.anthropic_analysis and isinstance(transcript.anthropic_analysis, dict):
        clinical_text = transcript.anthropic_analysis.get('clinical_progress_note',
                                                        transcript.anthropic_analysis.get('analysis', ''))
    
    # Clean the text - remove markdown syntax
    if clinical_text:
        clean_text = str(clinical_text)
        clean_text = clean_text.replace('**', '').replace('*', '').replace('#', '').replace('`', '')
        clean_text = clean_text.replace('### ', '').replace('## ', '').replace('# ', '')
    else:
        clean_text = f"Clinical progress note for session on {transcript.session_date}"
    
    # Format date
    if transcript.session_date:
        if isinstance(transcript.session_date, str):
            formatted_date = transcript.session_date
        else:
            formatted_date = transcript.session_date.strftime('%Y-%m-%d')
    else:
        formatted_date = datetime.now().strftime('%Y-%m-%d')
    
    # Create page properties
    properties = {
        "Session Title": {
            "title": [{"text": {"content": f"Session {formatted_date} - Kristi Rook"}}]
        },
        "Date": {"date": {"start": formatted_date}},
        "Session Type": {"select": {"name": "Individual"}},
        "Primary Emotion": {"select": {"name": "Content"}},
        "Status": {"select": {"name": "Completed"}}
    }
    
    # Create content blocks without markdown
    content_blocks = []
    
    # Split text into manageable chunks
    max_chunk = 1800
    text_chunks = []
    remaining = clean_text
    
    while remaining and len(remaining) > max_chunk:
        chunk = remaining[:max_chunk]
        # Find sentence break
        break_point = max_chunk
        for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
            if chunk[i] in '.!?':
                break_point = i + 1
                break
        
        text_chunks.append(remaining[:break_point])
        remaining = remaining[break_point:]
    
    if remaining:
        text_chunks.append(remaining)
    
    # Create paragraph blocks
    for chunk in text_chunks:
        if chunk.strip():
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk.strip()}}]
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
        headers=headers,
        json=page_data
    )
    
    if response.status_code == 200:
        return response.json().get('id')
    else:
        print(f"Failed to create page: {response.status_code} - {response.text}")
        return None

def main():
    with app.app_context():
        # Create Kristi's database
        print("Creating Kristi Rook database...")
        database_id = create_kristi_database()
        
        if not database_id:
            print("Failed to create database")
            return
        
        print(f"Created database: {database_id}")
        
        # Update client record
        kristi_client = db.session.query(Client).filter(Client.name == 'Kristi Rook').first()
        if kristi_client:
            kristi_client.notion_database_id = database_id
            db.session.commit()
            print("Updated client record")
        
        # Create pages for her transcripts
        headers = {
            "Authorization": f"Bearer {Config.NOTION_INTEGRATION_SECRET}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        transcripts = db.session.query(Transcript).filter(
            Transcript.client_id == kristi_client.id
        ).all()
        
        print(f"Creating {len(transcripts)} clinical note pages...")
        
        for transcript in transcripts:
            page_id = create_clinical_note_page(database_id, transcript, headers)
            if page_id:
                transcript.notion_page_id = page_id
                transcript.notion_synced = True
                print(f"Created page for: {transcript.original_filename}")
            else:
                print(f"Failed to create page for: {transcript.original_filename}")
        
        db.session.commit()
        print("Completed Kristi Rook database creation")

if __name__ == "__main__":
    main()