"""
Complete AI processing gap for remaining Anthropic and Gemini analyses
Direct database approach with proper Flask context management
"""

import json
import logging
from app import app, db
from models import Transcript
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_ai_analyses():
    """Complete missing AI analyses for all transcripts"""
    with app.app_context():
        ai_service = AIService()
        
        # Get completion status
        total_transcripts = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        anthropic_missing = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).count()
        
        gemini_missing = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).count()
        
        logger.info(f"Status: {total_transcripts} total, {anthropic_missing} missing Anthropic, {gemini_missing} missing Gemini")
        
        # Process Anthropic analyses
        if anthropic_missing > 0:
            logger.info("Processing missing Anthropic analyses...")
            
            transcripts = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.anthropic_analysis.is_(None)
            ).limit(5).all()
            
            for transcript in transcripts:
                try:
                    logger.info(f"Anthropic analysis: {transcript.original_filename}")
                    analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                    
                    if analysis:
                        transcript.anthropic_analysis = json.dumps(analysis) if isinstance(analysis, dict) else analysis
                        db.session.commit()
                        logger.info(f"✓ Completed: {transcript.original_filename}")
                    
                except Exception as e:
                    logger.error(f"Error with {transcript.original_filename}: {e}")
                    db.session.rollback()
        
        # Process Gemini analyses
        if gemini_missing > 0:
            logger.info("Processing missing Gemini analyses...")
            
            transcripts = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.gemini_analysis.is_(None)
            ).limit(5).all()
            
            for transcript in transcripts:
                try:
                    logger.info(f"Gemini analysis: {transcript.original_filename}")
                    analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                    
                    if analysis:
                        transcript.gemini_analysis = json.dumps(analysis) if isinstance(analysis, dict) else analysis
                        db.session.commit()
                        logger.info(f"✓ Completed: {transcript.original_filename}")
                    
                except Exception as e:
                    logger.error(f"Error with {transcript.original_filename}: {e}")
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
        
        logger.info(f"Final status: Anthropic {final_anthropic}/{total_transcripts}, Gemini {final_gemini}/{total_transcripts}")

if __name__ == "__main__":
    complete_ai_analyses()