#!/usr/bin/env python3
"""
Fix Notion integration by creating proper client databases and syncing transcripts
"""
import os
import sys
import logging
from datetime import datetime, timezone

# Add project root to path
sys.path.append('.')

from app import app, db
from models import Client, Transcript, ProcessingLog
from services.notion_service import NotionService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_notion_integration():
    """Fix Notion integration by creating databases and syncing transcripts"""
    
    with app.app_context():
        # Initialize Notion service
        notion_service = NotionService()
        
        # Test Notion connection first
        if not notion_service.test_connection():
            logger.error("Notion connection failed. Please check your integration secret.")
            return
        
        logger.info("Notion connection successful. Starting database creation...")
        
        # Get clients that need Notion databases
        clients_without_db = db.session.query(Client).filter(
            Client.notion_database_id.is_(None)
        ).all()
        
        logger.info(f"Found {len(clients_without_db)} clients without Notion databases")
        
        for client in clients_without_db:
            try:
                logger.info(f"Creating Notion database for: {client.name}")
                
                # Create client database
                database_id = notion_service.create_client_database(client.name)
                
                if database_id:
                    # Update client with database ID
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
                    
                    # Now sync existing transcripts for this client
                    transcripts = db.session.query(Transcript).filter(
                        Transcript.client_id == client.id,
                        Transcript.notion_synced == False
                    ).all()
                    
                    logger.info(f"Syncing {len(transcripts)} transcripts for {client.name}")
                    
                    for transcript in transcripts:
                        try:
                            # Prepare transcript data for Notion
                            notion_data = {
                                'transcript_id': transcript.id,
                                'client_name': client.name,
                                'session_date': transcript.session_date,
                                'filename': transcript.original_filename,
                                'openai_analysis': transcript.openai_analysis,
                                'anthropic_analysis': transcript.anthropic_analysis,
                                'gemini_analysis': transcript.gemini_analysis,
                                'therapy_insights': transcript.therapy_insights,
                                'sentiment_score': transcript.sentiment_score,
                                'key_themes': transcript.key_themes
                            }
                            
                            # Create transcript page in Notion
                            page_id = notion_service.create_transcript_page(database_id, notion_data)
                            
                            if page_id:
                                transcript.notion_page_id = page_id
                                transcript.notion_synced = True
                                transcript.notion_sync_error = None
                                
                                logger.info(f"Synced transcript {transcript.original_filename} to Notion")
                                
                                # Log transcript sync success
                                log_entry = ProcessingLog(
                                    transcript_id=transcript.id,
                                    activity_type='notion_sync',
                                    status='success',
                                    message=f'Synced {transcript.original_filename} to Notion database',
                                    created_at=datetime.now(timezone.utc)
                                )
                                db.session.add(log_entry)
                            else:
                                logger.warning(f"Failed to sync transcript {transcript.original_filename}")
                                transcript.notion_sync_error = "Failed to create Notion page"
                                
                        except Exception as e:
                            logger.error(f"Error syncing transcript {transcript.original_filename}: {str(e)}")
                            transcript.notion_sync_error = str(e)
                            
                            # Log transcript sync error
                            log_entry = ProcessingLog(
                                transcript_id=transcript.id,
                                activity_type='notion_sync',
                                status='error',
                                message=f'Failed to sync {transcript.original_filename} to Notion',
                                error_details=str(e),
                                created_at=datetime.now(timezone.utc)
                            )
                            db.session.add(log_entry)
                    
                    db.session.commit()
                    
                else:
                    logger.error(f"Failed to create database for {client.name}")
                    
                    # Log database creation failure
                    log_entry = ProcessingLog(
                        activity_type='notion_database_creation',
                        status='error',
                        message=f'Failed to create Notion database for {client.name}',
                        context_metadata={'client_id': client.id},
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                    
            except Exception as e:
                logger.error(f"Error processing client {client.name}: {str(e)}")
                
                # Log general error
                log_entry = ProcessingLog(
                    activity_type='notion_database_creation',
                    status='error',
                    message=f'Error processing client {client.name}',
                    error_details=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
        
        # Final summary
        synced_count = db.session.query(Transcript).filter(
            Transcript.notion_synced == True
        ).count()
        
        clients_with_db = db.session.query(Client).filter(
            Client.notion_database_id.isnot(None)
        ).count()
        
        logger.info(f"Notion integration fix complete:")
        logger.info(f"- Clients with databases: {clients_with_db}")
        logger.info(f"- Transcripts synced: {synced_count}")
        
        # Final summary log
        log_entry = ProcessingLog(
            activity_type='notion_integration_fix',
            status='success',
            message=f'Notion integration fix completed. {clients_with_db} clients with databases, {synced_count} transcripts synced',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()

if __name__ == "__main__":
    fix_notion_integration()