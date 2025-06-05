"""
Final AI processing completion for remaining transcripts
Focuses on completing Anthropic and Gemini analyses efficiently
"""

import json
import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_remaining_analyses():
    """Process remaining AI analyses in small efficient batches"""
    with app.app_context():
        ai_service = AIService()
        
        # Get current status
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        anthropic_missing = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(5).all()
        
        gemini_missing = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(5).all()
        
        logger.info(f"Processing batch: {len(anthropic_missing)} Anthropic, {len(gemini_missing)} Gemini")
        
        # Process Anthropic batch
        for transcript in anthropic_missing:
            try:
                logger.info(f"Anthropic: {transcript.original_filename[:50]}...")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info("✓ Completed")
                    time.sleep(3)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error: {str(e)[:100]}")
                db.session.rollback()
        
        # Process Gemini batch
        for transcript in gemini_missing:
            try:
                logger.info(f"Gemini: {transcript.original_filename[:50]}...")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info("✓ Completed")
                    time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error: {str(e)[:100]}")
                db.session.rollback()
        
        # Final status
        final_anthropic = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        final_gemini = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        logger.info(f"Status: Anthropic {final_anthropic}/{total}, Gemini {final_gemini}/{total}")

if __name__ == "__main__":
    process_remaining_analyses()