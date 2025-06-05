"""
Quick AI completion with optimized processing
"""

import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_next_analysis():
    """Complete the next available analysis"""
    with app.app_context():
        ai_service = AIService()
        
        # Try Anthropic first (more remaining)
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        if transcript:
            try:
                logger.info(f"Anthropic: {transcript.original_filename[:40]}")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info("Anthropic completed")
                    return True
            except Exception as e:
                logger.error(f"Anthropic error: {str(e)[:80]}")
                db.session.rollback()
        
        # Try Gemini
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if transcript:
            try:
                logger.info(f"Gemini: {transcript.original_filename[:40]}")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info("Gemini completed")
                    return True
            except Exception as e:
                logger.error(f"Gemini error: {str(e)[:80]}")
                db.session.rollback()
        
        return False

def run_quick_completion():
    """Run quick completion session"""
    logger.info("Starting quick AI completion")
    
    completed = 0
    for i in range(4):  # Process 4 analyses
        if complete_next_analysis():
            completed += 1
            time.sleep(2)
        else:
            break
    
    # Final status
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
        
        logger.info(f"Session completed: {completed} analyses")
        logger.info(f"Current: Anthropic {anthropic}/{total}, Gemini {gemini}/{total}")

if __name__ == "__main__":
    run_quick_completion()