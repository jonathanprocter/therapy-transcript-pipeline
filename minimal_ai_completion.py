"""
Minimal AI completion - Process one analysis at a time efficiently
"""

import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_next_analysis():
    """Complete one analysis efficiently"""
    with app.app_context():
        ai_service = AIService()
        
        # Try Anthropic first (81 remaining)
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        if transcript:
            try:
                logger.info(f"Processing Anthropic for: {transcript.original_filename[:40]}")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info("Anthropic analysis completed successfully")
                    return "anthropic"
                    
            except Exception as e:
                logger.error(f"Anthropic error: {str(e)[:100]}")
                db.session.rollback()
        
        # Try Gemini if no Anthropic available (83 remaining)
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if transcript:
            try:
                logger.info(f"Processing Gemini for: {transcript.original_filename[:40]}")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info("Gemini analysis completed successfully")
                    return "gemini"
                    
            except Exception as e:
                logger.error(f"Gemini error: {str(e)[:100]}")
                db.session.rollback()
        
        return None

def show_progress():
    """Show current progress"""
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
        
        logger.info(f"Current: Anthropic {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
        logger.info(f"Current: Gemini {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")

def run_completion():
    """Run completion process"""
    logger.info("Starting minimal AI completion")
    show_progress()
    
    completed = 0
    for i in range(3):  # Process 3 analyses
        result = complete_next_analysis()
        if result:
            completed += 1
            time.sleep(2)  # Rate limiting
        else:
            break
    
    logger.info(f"Completed {completed} analyses in this session")
    show_progress()

if __name__ == "__main__":
    run_completion()