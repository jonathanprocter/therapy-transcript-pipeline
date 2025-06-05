"""
Background AI processor that runs efficiently without timeouts
Processes transcripts in small batches with proper error handling
"""

import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_single_batch():
    """Process a single batch of 3 transcripts"""
    with app.app_context():
        # Get 1 Anthropic and 1 Gemini transcript
        anthropic_transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        gemini_transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if not anthropic_transcript and not gemini_transcript:
            return 0, "No transcripts available for processing"
        
        ai_service = AIService()
        completed = 0
        
        # Process Anthropic
        if anthropic_transcript:
            try:
                logger.info(f"Processing Anthropic: {anthropic_transcript.original_filename[:40]}")
                analysis = ai_service._analyze_with_anthropic(anthropic_transcript.raw_content)
                if analysis:
                    anthropic_transcript.anthropic_analysis = analysis
                    db.session.commit()
                    completed += 1
                    logger.info("Anthropic completed")
            except Exception as e:
                logger.error(f"Anthropic error: {str(e)[:50]}")
                db.session.rollback()
        
        time.sleep(3)  # Rate limiting
        
        # Process Gemini
        if gemini_transcript:
            try:
                logger.info(f"Processing Gemini: {gemini_transcript.original_filename[:40]}")
                analysis = ai_service._analyze_with_gemini(gemini_transcript.raw_content)
                if analysis:
                    gemini_transcript.gemini_analysis = analysis
                    db.session.commit()
                    completed += 1
                    logger.info("Gemini completed")
            except Exception as e:
                logger.error(f"Gemini error: {str(e)[:50]}")
                db.session.rollback()
        
        # Get current status
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        anthropic_done = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        gemini_done = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        status = f"Current: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}"
        return completed, status

def run_background_processor():
    """Run the background processor for multiple batches"""
    logger.info("Starting background AI processor")
    
    total_completed = 0
    max_batches = 5
    
    for batch_num in range(max_batches):
        logger.info(f"Processing batch {batch_num + 1}/{max_batches}")
        
        completed, status = process_single_batch()
        total_completed += completed
        
        logger.info(f"Batch {batch_num + 1} completed: +{completed} analyses")
        logger.info(status)
        
        if completed == 0:
            logger.info("No more transcripts to process")
            break
        
        time.sleep(5)  # Rest between batches
    
    logger.info(f"Background processing completed: {total_completed} total analyses processed")

if __name__ == "__main__":
    run_background_processor()