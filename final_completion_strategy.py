"""
Final targeted completion strategy for remaining AI analyses
Efficiently completes Anthropic and Gemini processing with optimized approach
"""

import json
import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_single_analysis():
    """Complete one analysis efficiently"""
    with app.app_context():
        ai_service = AIService()
        
        # Try Anthropic first (more needed)
        anthropic_transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        if anthropic_transcript:
            try:
                logger.info(f"Anthropic: {anthropic_transcript.original_filename[:30]}...")
                analysis = ai_service._analyze_with_anthropic(anthropic_transcript.raw_content)
                
                if analysis:
                    anthropic_transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info("Anthropic completed successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"Anthropic error: {str(e)[:50]}")
                db.session.rollback()
        
        # Try Gemini if no Anthropic available
        gemini_transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if gemini_transcript:
            try:
                logger.info(f"Gemini: {gemini_transcript.original_filename[:30]}...")
                analysis = ai_service._analyze_with_gemini(gemini_transcript.raw_content)
                
                if analysis:
                    gemini_transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info("Gemini completed successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"Gemini error: {str(e)[:50]}")
                db.session.rollback()
        
        return False

def get_completion_progress():
    """Get current completion progress"""
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

def run_completion_batch():
    """Run completion for 3 analyses"""
    logger.info("Starting completion batch")
    completed = 0
    
    for i in range(3):
        if complete_single_analysis():
            completed += 1
            time.sleep(2)  # Rate limiting
        else:
            break
    
    total, anthropic, gemini = get_completion_progress()
    logger.info(f"Batch complete: {completed} processed")
    logger.info(f"Status: Anthropic {anthropic}/{total}, Gemini {gemini}/{total}")

if __name__ == "__main__":
    run_completion_batch()