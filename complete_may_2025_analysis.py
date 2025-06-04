#!/usr/bin/env python3
"""
Complete AI analysis for May 2025 transcripts that are missing Anthropic/Gemini analysis
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
from services.ai_service import AIService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class May2025Completer:
    def __init__(self):
        self.ai_service = AIService()
        
    def get_incomplete_may_transcripts(self):
        """Get May 2025 transcripts missing Anthropic or Gemini analysis"""
        with app.app_context():
            transcripts = db.session.query(Transcript).filter(
                Transcript.session_date >= '2025-05-01',
                Transcript.session_date < '2025-06-01',
                Transcript.processing_status == 'completed',
                Transcript.raw_content.isnot(None)
            ).filter(
                # Missing either Anthropic or Gemini analysis
                (Transcript.anthropic_analysis.is_(None)) | 
                (Transcript.gemini_analysis.is_(None))
            ).all()
            
            return transcripts
    
    def complete_analysis_for_transcript(self, transcript):
        """Complete missing AI analysis for a single transcript"""
        try:
            logger.info(f"Completing analysis for: {transcript.original_filename}")
            
            updated = False
            
            # Add Anthropic analysis if missing
            if not transcript.anthropic_analysis and self.ai_service.anthropic_client:
                logger.info(f"Adding Anthropic analysis for: {transcript.original_filename}")
                anthropic_result = self.ai_service._analyze_with_anthropic(transcript.raw_content)
                if anthropic_result:
                    transcript.anthropic_analysis = anthropic_result
                    updated = True
                    logger.info(f"Anthropic analysis completed for: {transcript.original_filename}")
                else:
                    logger.warning(f"Anthropic analysis failed for: {transcript.original_filename}")
            
            # Add Gemini analysis if missing
            if not transcript.gemini_analysis and self.ai_service.gemini_client:
                logger.info(f"Adding Gemini analysis for: {transcript.original_filename}")
                gemini_result = self.ai_service._analyze_with_gemini(transcript.raw_content)
                if gemini_result:
                    transcript.gemini_analysis = gemini_result
                    updated = True
                    logger.info(f"Gemini analysis completed for: {transcript.original_filename}")
                else:
                    logger.warning(f"Gemini analysis failed for: {transcript.original_filename}")
            
            # Update therapy insights if we added new analysis
            if updated:
                try:
                    # Generate consolidated insights from all available analyses
                    analyses = {
                        'openai_analysis': transcript.openai_analysis,
                        'anthropic_analysis': transcript.anthropic_analysis,
                        'gemini_analysis': transcript.gemini_analysis
                    }
                    insights = self.ai_service._consolidate_insights(analyses)
                    if insights:
                        transcript.therapy_insights = insights
                        transcript.sentiment_score = insights.get('sentiment_score')
                        transcript.key_themes = insights.get('key_themes', [])
                        transcript.progress_indicators = insights.get('progress_indicators', {})
                        logger.info(f"Updated therapy insights for: {transcript.original_filename}")
                except Exception as e:
                    logger.warning(f"Could not update insights for {transcript.original_filename}: {str(e)}")
                
                # Update timestamp
                transcript.processed_at = datetime.now(timezone.utc)
                
                # Log the completion
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    activity_type='ai_analysis',
                    status='success',
                    message=f'Completed missing AI analysis for May 2025 file: {transcript.original_filename}',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                
                return True
            else:
                logger.info(f"No updates needed for: {transcript.original_filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error completing analysis for {transcript.original_filename}: {str(e)}")
            
            # Log error
            log_entry = ProcessingLog(
                transcript_id=transcript.id,
                activity_type='ai_analysis',
                status='error',
                message=f'Failed to complete AI analysis for: {transcript.original_filename}',
                error_details=str(e),
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(log_entry)
            
            return False
    
    def run_completion(self):
        """Run the completion process for May 2025 transcripts"""
        logger.info("Starting May 2025 AI analysis completion")
        
        # Get incomplete transcripts
        incomplete_transcripts = self.get_incomplete_may_transcripts()
        logger.info(f"Found {len(incomplete_transcripts)} May 2025 transcripts needing completion")
        
        if not incomplete_transcripts:
            logger.info("All May 2025 transcripts already have complete AI analysis")
            return
        
        completed_count = 0
        error_count = 0
        
        with app.app_context():
            for i, transcript in enumerate(incomplete_transcripts, 1):
                logger.info(f"Processing {i}/{len(incomplete_transcripts)}: {transcript.original_filename}")
                
                try:
                    if self.complete_analysis_for_transcript(transcript):
                        completed_count += 1
                        db.session.commit()
                        logger.info(f"Successfully completed analysis for: {transcript.original_filename}")
                    else:
                        logger.info(f"No changes made for: {transcript.original_filename}")
                    
                    # Add delay between API calls to avoid rate limits
                    time.sleep(3)
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to process {transcript.original_filename}: {str(e)}")
                    db.session.rollback()
                    continue
        
        logger.info(f"May 2025 completion finished: {completed_count} completed, {error_count} errors")
        
        # Final summary log
        with app.app_context():
            log_entry = ProcessingLog(
                activity_type='batch_complete',
                status='success',
                message=f'May 2025 AI analysis completion: {completed_count} transcripts completed, {error_count} errors',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(log_entry)
            db.session.commit()

def main():
    """Main execution function"""
    completer = May2025Completer()
    completer.run_completion()

if __name__ == "__main__":
    main()