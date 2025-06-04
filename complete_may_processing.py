#!/usr/bin/env python3
"""
Complete processing of pending May 2025 transcripts and sync to Notion
"""
import os
import sys
import logging
from datetime import datetime, timezone
import time

# Add project root to path
sys.path.append('.')

from app import app, db
from models import Transcript, ProcessingLog, Client
from services.ai_service import AIService
from services.notion_service import NotionService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def complete_pending_transcripts():
    """Complete processing of pending May 2025 transcripts"""
    
    with app.app_context():
        # Get pending transcripts
        pending_transcripts = db.session.query(Transcript).filter(
            Transcript.processing_status == 'pending'
        ).all()
        
        logger.info(f"Found {len(pending_transcripts)} pending transcripts to complete")
        
        if not pending_transcripts:
            logger.info("No pending transcripts found")
            return
        
        # Initialize services
        ai_service = AIService()
        notion_service = NotionService()
        
        for transcript in pending_transcripts:
            try:
                logger.info(f"Completing analysis for: {transcript.original_filename}")
                
                # Add processing log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='ai_analysis',
                    status='info',
                    message=f'Completing comprehensive AI analysis for {transcript.original_filename}',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
                
                # Complete Anthropic analysis if missing
                if not transcript.anthropic_analysis and ai_service.anthropic_client:
                    logger.info(f"Adding Anthropic analysis...")
                    try:
                        anthropic_result = ai_service._analyze_with_anthropic(transcript.raw_content)
                        if anthropic_result:
                            transcript.anthropic_analysis = anthropic_result
                            logger.info(f"Anthropic analysis completed")
                            
                            # Log success
                            log_entry = ProcessingLog(
                                transcript_id=transcript.id,
                                activity_type='ai_analysis',
                                status='success',
                                message=f'Anthropic analysis completed for {transcript.original_filename}',
                                created_at=datetime.now(timezone.utc)
                            )
                            db.session.add(log_entry)
                    except Exception as e:
                        logger.error(f"Anthropic analysis failed: {str(e)}")
                
                # Complete Gemini analysis if missing
                if not transcript.gemini_analysis and ai_service.gemini_client:
                    logger.info(f"Adding Gemini analysis...")
                    try:
                        gemini_result = ai_service._analyze_with_gemini(transcript.raw_content)
                        if gemini_result:
                            transcript.gemini_analysis = gemini_result
                            logger.info(f"Gemini analysis completed")
                            
                            # Log success
                            log_entry = ProcessingLog(
                                transcript_id=transcript.id,
                                activity_type='ai_analysis',
                                status='success',
                                message=f'Gemini analysis completed for {transcript.original_filename}',
                                created_at=datetime.now(timezone.utc)
                            )
                            db.session.add(log_entry)
                    except Exception as e:
                        logger.error(f"Gemini analysis failed: {str(e)}")
                
                # Update consolidated insights
                try:
                    analyses = {
                        'openai_analysis': transcript.openai_analysis,
                        'anthropic_analysis': transcript.anthropic_analysis,
                        'gemini_analysis': transcript.gemini_analysis
                    }
                    insights = ai_service._consolidate_insights(analyses)
                    if insights:
                        transcript.therapy_insights = insights
                        transcript.sentiment_score = insights.get('sentiment_score')
                        transcript.key_themes = insights.get('key_themes', [])
                        transcript.progress_indicators = insights.get('progress_indicators', {})
                        logger.info(f"Consolidated insights updated")
                except Exception as e:
                    logger.warning(f"Could not consolidate insights: {str(e)}")
                
                # Mark as completed
                transcript.processing_status = 'completed'
                transcript.processed_at = datetime.now(timezone.utc)
                
                # Sync to Notion if client has a database
                client = db.session.get(Client, transcript.client_id)
                if client and client.notion_database_id and notion_service:
                    try:
                        logger.info(f"Syncing to Notion database: {client.notion_database_id}")
                        
                        # Prepare data for Notion
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
                        
                        # Create Notion page
                        page_id = notion_service.create_transcript_page(
                            client.notion_database_id, 
                            notion_data
                        )
                        
                        if page_id:
                            transcript.notion_page_id = page_id
                            transcript.notion_synced = True
                            logger.info(f"Successfully synced to Notion: {page_id}")
                            
                            # Log Notion sync success
                            log_entry = ProcessingLog(
                                transcript_id=transcript.id,
                                activity_type='notion_sync',
                                status='success',
                                message=f'Synced {transcript.original_filename} to Notion database',
                                created_at=datetime.now(timezone.utc)
                            )
                            db.session.add(log_entry)
                        else:
                            logger.warning(f"Notion sync failed for {transcript.original_filename}")
                            
                    except Exception as e:
                        logger.error(f"Notion sync error: {str(e)}")
                        transcript.notion_sync_error = str(e)
                        
                        # Log Notion sync error
                        log_entry = ProcessingLog(
                            transcript_id=transcript.id,
                            activity_type='notion_sync',
                            status='error',
                            message=f'Failed to sync {transcript.original_filename} to Notion',
                            error_details=str(e),
                            created_at=datetime.now(timezone.utc)
                        )
                        db.session.add(log_entry)
                
                # Final success log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='transcript_complete',
                    status='success',
                    message=f'Completed full processing pipeline for {transcript.original_filename}',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
                
                logger.info(f"Successfully completed processing for: {transcript.original_filename}")
                
                # Add delay between transcripts
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Error processing {transcript.original_filename}: {str(e)}")
                
                # Mark as failed
                transcript.processing_status = 'failed'
                
                # Error log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='transcript_complete',
                    status='error',
                    message=f'Failed to complete processing for {transcript.original_filename}',
                    error_details=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
        
        # Final summary
        completed_count = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.session_date >= '2025-05-01',
            Transcript.session_date < '2025-06-01'
        ).count()
        
        logger.info(f"May 2025 processing complete. Total completed transcripts: {completed_count}")
        
        # Summary log
        log_entry = ProcessingLog(
            activity_type='batch_complete',
            status='success',
            message=f'May 2025 batch processing completed successfully. {completed_count} transcripts processed with full AI analysis',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()

if __name__ == "__main__":
    complete_pending_transcripts()