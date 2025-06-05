"""
Efficient batch processor for completing remaining AI analyses
Optimized for reliable progress with intelligent error handling
"""

import logging
import time
import random
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_anthropic_batch():
    """Process a batch of Anthropic analyses"""
    with app.app_context():
        transcripts = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(3).all()
        
        if not transcripts:
            return 0
        
        ai_service = AIService()
        completed = 0
        
        for transcript in transcripts:
            try:
                logger.info(f"Anthropic: {transcript.original_filename[:45]}")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    completed += 1
                    logger.info("Anthropic analysis completed")
                    time.sleep(random.uniform(2, 4))
                    
            except Exception as e:
                logger.error(f"Anthropic error: {str(e)[:100]}")
                db.session.rollback()
                continue
        
        return completed

def process_gemini_batch():
    """Process a batch of Gemini analyses"""
    with app.app_context():
        transcripts = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(3).all()
        
        if not transcripts:
            return 0
        
        ai_service = AIService()
        completed = 0
        
        for transcript in transcripts:
            try:
                logger.info(f"Gemini: {transcript.original_filename[:45]}")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    completed += 1
                    logger.info("Gemini analysis completed")
                    time.sleep(random.uniform(2, 4))
                    
            except Exception as e:
                logger.error(f"Gemini error: {str(e)[:100]}")
                db.session.rollback()
                continue
        
        return completed

def get_progress_summary():
    """Get current progress summary"""
    with app.app_context():
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        anthropic = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        gemini = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        return total, anthropic, gemini

def run_efficient_processing():
    """Run efficient batch processing session"""
    logger.info("Starting efficient batch processing")
    
    initial_total, initial_anthropic, initial_gemini = get_progress_summary()
    logger.info(f"Starting: Anthropic {initial_anthropic}/{initial_total}, Gemini {initial_gemini}/{initial_total}")
    
    session_completed = 0
    max_batches = 4  # Process up to 4 batches
    
    for batch in range(max_batches):
        logger.info(f"Processing batch {batch + 1}/{max_batches}")
        
        # Process Anthropic batch
        anthropic_completed = process_anthropic_batch()
        session_completed += anthropic_completed
        
        if anthropic_completed > 0:
            time.sleep(5)  # Rest between providers
        
        # Process Gemini batch
        gemini_completed = process_gemini_batch()
        session_completed += gemini_completed
        
        if gemini_completed == 0 and anthropic_completed == 0:
            logger.info("No more analyses available")
            break
        
        # Progress update
        current_total, current_anthropic, current_gemini = get_progress_summary()
        logger.info(f"Batch {batch + 1} complete: +{anthropic_completed} Anthropic, +{gemini_completed} Gemini")
        logger.info(f"Current: Anthropic {current_anthropic}/{current_total}, Gemini {current_gemini}/{current_total}")
        
        time.sleep(8)  # Rest between batches
    
    # Final summary
    final_total, final_anthropic, final_gemini = get_progress_summary()
    anthropic_gained = final_anthropic - initial_anthropic
    gemini_gained = final_gemini - initial_gemini
    
    logger.info("Batch processing session completed")
    logger.info(f"Session results:")
    logger.info(f"  Anthropic: +{anthropic_gained} ({final_anthropic}/{final_total})")
    logger.info(f"  Gemini: +{gemini_gained} ({final_gemini}/{final_total})")
    logger.info(f"  Total processed: {session_completed} analyses")

if __name__ == "__main__":
    run_efficient_processing()