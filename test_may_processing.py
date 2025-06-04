#!/usr/bin/env python3
"""
Test processing of a few May 2025 transcripts to verify the system works
"""
import os
import sys
import logging
from datetime import datetime, timezone
import time

# Add project root to path
sys.path.append('.')

from app import app, db
from models import Transcript, ProcessingLog

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_process_may_transcripts():
    """Process a small batch of May 2025 transcripts for testing"""
    
    with app.app_context():
        # Get 5 May 2025 transcripts that only have OpenAI analysis
        test_transcripts = db.session.query(Transcript).filter(
            Transcript.session_date >= '2025-05-01',
            Transcript.session_date < '2025-06-01',
            Transcript.processing_status == 'completed',
            Transcript.openai_analysis.isnot(None),
            Transcript.anthropic_analysis.is_(None)
        ).limit(5).all()
        
        logger.info(f"Found {len(test_transcripts)} test transcripts to process")
        
        from services.ai_service import AIService
        ai_service = AIService()
        
        processed_count = 0
        
        for transcript in test_transcripts:
            try:
                logger.info(f"Processing: {transcript.original_filename}")
                
                # Add log entry for start
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='ai_analysis',
                    status='info',
                    message=f'Starting AI analysis completion for: {transcript.original_filename}',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
                
                # Add Anthropic analysis
                if ai_service.anthropic_client:
                    logger.info(f"Adding Anthropic analysis...")
                    anthropic_result = ai_service._analyze_with_anthropic(transcript.raw_content)
                    if anthropic_result:
                        transcript.anthropic_analysis = anthropic_result
                        logger.info(f"Anthropic analysis completed")
                
                # Add Gemini analysis
                if ai_service.gemini_client:
                    logger.info(f"Adding Gemini analysis...")
                    gemini_result = ai_service._analyze_with_gemini(transcript.raw_content)
                    if gemini_result:
                        transcript.gemini_analysis = gemini_result
                        logger.info(f"Gemini analysis completed")
                
                # Update insights
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
                except Exception as e:
                    logger.warning(f"Could not consolidate insights: {str(e)}")
                
                # Update timestamp
                transcript.processed_at = datetime.now(timezone.utc)
                
                # Success log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='ai_analysis',
                    status='success',
                    message=f'Completed comprehensive AI analysis for: {transcript.original_filename}',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
                
                processed_count += 1
                logger.info(f"Successfully processed {transcript.original_filename} ({processed_count}/5)")
                
                # Delay between processing
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing {transcript.original_filename}: {str(e)}")
                
                # Error log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='ai_analysis',
                    status='error',
                    message=f'Failed to complete AI analysis for: {transcript.original_filename}',
                    error_details=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                db.session.commit()
                continue
        
        # Final summary log
        log_entry = ProcessingLog(
            activity_type='batch_test',
            status='success',
            message=f'Test batch processing complete: {processed_count} May 2025 transcripts processed with full AI analysis',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()
        
        logger.info(f"Test processing complete: {processed_count} transcripts processed")

if __name__ == "__main__":
    test_process_may_transcripts()