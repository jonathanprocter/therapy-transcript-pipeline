"""
Gradual AI processor with enhanced reliability and progress tracking
"""

import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_next_anthropic():
    """Complete next Anthropic analysis"""
    with app.app_context():
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        if not transcript:
            return False
            
        try:
            ai_service = AIService()
            logger.info(f"Anthropic: {transcript.original_filename[:40]}")
            
            analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
            if analysis:
                transcript.anthropic_analysis = analysis
                db.session.commit()
                logger.info("Anthropic analysis completed")
                return True
                
        except Exception as e:
            logger.error(f"Anthropic error: {str(e)[:80]}")
            db.session.rollback()
            
        return False

def complete_next_gemini():
    """Complete next Gemini analysis"""
    with app.app_context():
        transcript = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if not transcript:
            return False
            
        try:
            ai_service = AIService()
            logger.info(f"Gemini: {transcript.original_filename[:40]}")
            
            analysis = ai_service._analyze_with_gemini(transcript.raw_content)
            if analysis:
                transcript.gemini_analysis = analysis
                db.session.commit()
                logger.info("Gemini analysis completed")
                return True
                
        except Exception as e:
            logger.error(f"Gemini error: {str(e)[:80]}")
            db.session.rollback()
            
        return False

def get_current_progress():
    """Get current completion progress"""
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

def run_gradual_processing():
    """Run gradual processing with progress updates"""
    logger.info("Starting gradual AI processing")
    
    total, anthropic_start, gemini_start = get_current_progress()
    logger.info(f"Initial: Anthropic {anthropic_start}/{total}, Gemini {gemini_start}/{total}")
    
    completed = 0
    max_analyses = 6  # Process 6 analyses this session
    
    for i in range(max_analyses):
        # Alternate between Anthropic and Gemini
        if i % 2 == 0:
            success = complete_next_anthropic()
        else:
            success = complete_next_gemini()
        
        if success:
            completed += 1
            time.sleep(3)  # Rate limiting
        else:
            logger.info("No more analyses available for this provider")
        
        # Progress update every 2 completions
        if completed > 0 and completed % 2 == 0:
            total, anthropic_current, gemini_current = get_current_progress()
            logger.info(f"Progress: {completed} completed")
            logger.info(f"Current: Anthropic {anthropic_current}/{total}, Gemini {gemini_current}/{total}")
    
    # Final summary
    total, anthropic_final, gemini_final = get_current_progress()
    anthropic_gained = anthropic_final - anthropic_start
    gemini_gained = gemini_final - gemini_start
    
    logger.info(f"Session summary:")
    logger.info(f"  Anthropic: +{anthropic_gained} ({anthropic_final}/{total})")
    logger.info(f"  Gemini: +{gemini_gained} ({gemini_final}/{total})")
    logger.info(f"  Total progress: {completed} analyses")

if __name__ == "__main__":
    run_gradual_processing()