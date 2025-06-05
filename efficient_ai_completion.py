"""
Efficient AI completion with parallel processing and smart batching
"""

import json
import logging
import time
import concurrent.futures
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_anthropic_analysis(transcript_id):
    """Process single Anthropic analysis"""
    with app.app_context():
        try:
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript or transcript.anthropic_analysis:
                return False
            
            ai_service = AIService()
            analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
            
            if analysis:
                transcript.anthropic_analysis = analysis
                db.session.commit()
                logger.info(f"Anthropic completed: {transcript.original_filename[:30]}")
                return True
                
        except Exception as e:
            logger.error(f"Anthropic error for {transcript_id}: {str(e)[:50]}")
            db.session.rollback()
        
        return False

def process_gemini_analysis(transcript_id):
    """Process single Gemini analysis"""
    with app.app_context():
        try:
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript or transcript.gemini_analysis:
                return False
            
            ai_service = AIService()
            analysis = ai_service._analyze_with_gemini(transcript.raw_content)
            
            if analysis:
                transcript.gemini_analysis = analysis
                db.session.commit()
                logger.info(f"Gemini completed: {transcript.original_filename[:30]}")
                return True
                
        except Exception as e:
            logger.error(f"Gemini error for {transcript_id}: {str(e)[:50]}")
            db.session.rollback()
        
        return False

def get_priority_transcripts(limit=5):
    """Get priority transcripts for processing"""
    with app.app_context():
        # Get transcripts missing Anthropic analysis (higher priority)
        anthropic_missing = db.session.query(Transcript.id).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(limit).all()
        
        # Get transcripts missing Gemini analysis
        gemini_missing = db.session.query(Transcript.id).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(limit).all()
        
        return ([t.id for t in anthropic_missing], [t.id for t in gemini_missing])

def run_efficient_batch():
    """Run efficient batch processing"""
    logger.info("Starting efficient AI completion")
    
    anthropic_ids, gemini_ids = get_priority_transcripts(3)
    completed = 0
    
    # Process Anthropic analyses
    if anthropic_ids:
        logger.info(f"Processing {len(anthropic_ids)} Anthropic analyses")
        for transcript_id in anthropic_ids:
            if process_anthropic_analysis(transcript_id):
                completed += 1
            time.sleep(1)  # Rate limiting
    
    # Process Gemini analyses
    if gemini_ids:
        logger.info(f"Processing {len(gemini_ids)} Gemini analyses")
        for transcript_id in gemini_ids:
            if process_gemini_analysis(transcript_id):
                completed += 1
            time.sleep(1)  # Rate limiting
    
    # Final status
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
        
        logger.info(f"Batch complete: {completed} new analyses")
        logger.info(f"Current status: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")

if __name__ == "__main__":
    run_efficient_batch()