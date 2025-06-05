"""
Accelerated AI completion with optimized processing
"""

import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_batch_analyses():
    """Process multiple analyses efficiently"""
    with app.app_context():
        ai_service = AIService()
        completed = 0
        
        # Get transcripts needing analysis
        transcripts = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            db.or_(
                Transcript.anthropic_analysis.is_(None),
                Transcript.gemini_analysis.is_(None)
            )
        ).limit(5).all()
        
        for transcript in transcripts:
            try:
                # Process Anthropic if missing
                if not transcript.anthropic_analysis:
                    logger.info(f"Anthropic: {transcript.original_filename[:30]}...")
                    analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                    if analysis:
                        transcript.anthropic_analysis = analysis
                        db.session.commit()
                        completed += 1
                        time.sleep(1)
                
                # Process Gemini if missing
                if not transcript.gemini_analysis:
                    logger.info(f"Gemini: {transcript.original_filename[:30]}...")
                    analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                    if analysis:
                        transcript.gemini_analysis = analysis
                        db.session.commit()
                        completed += 1
                        time.sleep(1)
                        
            except Exception as e:
                logger.error(f"Error: {str(e)[:50]}")
                db.session.rollback()
                continue
        
        # Status update
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
        
        logger.info(f"Completed {completed} analyses")
        logger.info(f"Status: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")

if __name__ == "__main__":
    process_batch_analyses()