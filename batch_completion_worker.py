"""
Background worker for completing remaining AI analyses
Processes transcripts efficiently without blocking main application
"""

import json
import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_single_anthropic():
    """Complete one Anthropic analysis"""
    with app.app_context():
        ai_service = AIService()
        
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        if transcript:
            try:
                logger.info(f"Processing: {transcript.original_filename}")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info("Anthropic analysis completed successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"Anthropic error: {e}")
                db.session.rollback()
        
        return False

def complete_single_gemini():
    """Complete one Gemini analysis"""
    with app.app_context():
        ai_service = AIService()
        
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if transcript:
            try:
                logger.info(f"Processing: {transcript.original_filename}")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info("Gemini analysis completed successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"Gemini error: {e}")
                db.session.rollback()
        
        return False

def get_progress_status():
    """Get current progress status"""
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
    """Run a small batch of completions"""
    logger.info("Starting completion batch")
    
    # Complete one Anthropic
    if complete_single_anthropic():
        time.sleep(3)  # Rate limiting
    
    # Complete one Gemini
    if complete_single_gemini():
        time.sleep(2)  # Rate limiting
    
    # Show progress
    total, anthropic, gemini = get_progress_status()
    logger.info(f"Progress: Anthropic {anthropic}/{total}, Gemini {gemini}/{total}")

if __name__ == "__main__":
    run_completion_batch()