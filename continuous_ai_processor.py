"""
Continuous AI processor for completing remaining analyses
Optimized for consistent progress with proper error handling
"""

import logging
import time
import random
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_single_analysis():
    """Process one analysis with intelligent provider selection"""
    with app.app_context():
        # Get counts to determine priority
        anthropic_count = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).count()
        
        gemini_count = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).count()
        
        # Prioritize Anthropic (more missing)
        if anthropic_count > 0:
            transcript = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.anthropic_analysis.is_(None)
            ).first()
            
            if transcript:
                return process_transcript_analysis(transcript, 'anthropic')
        
        # Process Gemini if available
        if gemini_count > 0:
            transcript = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.gemini_analysis.is_(None)
            ).first()
            
            if transcript:
                return process_transcript_analysis(transcript, 'gemini')
        
        return None

def process_transcript_analysis(transcript, provider):
    """Process analysis for specific transcript and provider"""
    try:
        ai_service = AIService()
        filename = transcript.original_filename[:35] + "..." if len(transcript.original_filename) > 35 else transcript.original_filename
        
        if provider == 'anthropic':
            logger.info(f"Processing Anthropic: {filename}")
            analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
            if analysis:
                transcript.anthropic_analysis = analysis
                db.session.commit()
                logger.info(f"Anthropic completed: {filename}")
                return True
                
        elif provider == 'gemini':
            logger.info(f"Processing Gemini: {filename}")
            analysis = ai_service._analyze_with_gemini(transcript.raw_content)
            if analysis:
                transcript.gemini_analysis = analysis
                db.session.commit()
                logger.info(f"Gemini completed: {filename}")
                return True
        
    except Exception as e:
        logger.error(f"{provider} error: {str(e)[:60]}...")
        db.session.rollback()
    
    return False

def get_completion_stats():
    """Get current completion statistics"""
    with app.app_context():
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
        
        return total, anthropic_done, gemini_done

def run_continuous_processing():
    """Run continuous processing session"""
    logger.info("Starting continuous AI processing")
    
    # Initial status
    total, anthropic_done, gemini_done = get_completion_stats()
    logger.info(f"Starting status: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")
    
    completed = 0
    max_iterations = 8  # Process up to 8 analyses
    
    for i in range(max_iterations):
        result = process_single_analysis()
        
        if result:
            completed += 1
            # Variable delay for rate limiting
            delay = random.uniform(1.5, 3.0)
            time.sleep(delay)
        else:
            logger.info("No more analyses to process")
            break
        
        # Progress update every 3 completions
        if completed % 3 == 0:
            total, anthropic_done, gemini_done = get_completion_stats()
            logger.info(f"Progress: {completed} completed this session")
            logger.info(f"Current: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")
    
    # Final status
    total, anthropic_done, gemini_done = get_completion_stats()
    logger.info(f"Session completed: {completed} analyses processed")
    logger.info(f"Final status: Anthropic {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
    logger.info(f"Final status: Gemini {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")

if __name__ == "__main__":
    run_continuous_processing()