"""
Systematic AI completion with optimized error handling and progress tracking
"""

import logging
import time
import sys
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_single_transcript(transcript_id, provider):
    """Complete analysis for a single transcript with specific provider"""
    with app.app_context():
        try:
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                return False
            
            ai_service = AIService()
            
            if provider == 'anthropic' and not transcript.anthropic_analysis:
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info(f"Anthropic completed: {transcript.original_filename[:40]}")
                    return True
                    
            elif provider == 'gemini' and not transcript.gemini_analysis:
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info(f"Gemini completed: {transcript.original_filename[:40]}")
                    return True
                    
        except Exception as e:
            logger.error(f"{provider} error for transcript {transcript_id}: {str(e)[:80]}")
            db.session.rollback()
            
        return False

def get_incomplete_transcripts():
    """Get transcript IDs that need analysis"""
    with app.app_context():
        anthropic_missing = db.session.query(Transcript.id).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(10).all()
        
        gemini_missing = db.session.query(Transcript.id).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(10).all()
        
        return ([t.id for t in anthropic_missing], [t.id for t in gemini_missing])

def run_systematic_completion():
    """Run systematic completion with progress tracking"""
    logger.info("Starting systematic AI completion")
    
    anthropic_ids, gemini_ids = get_incomplete_transcripts()
    total_processed = 0
    
    # Process Anthropic analyses
    logger.info(f"Processing {len(anthropic_ids)} Anthropic analyses")
    for i, transcript_id in enumerate(anthropic_ids, 1):
        if complete_single_transcript(transcript_id, 'anthropic'):
            total_processed += 1
        time.sleep(2)  # Rate limiting
        logger.info(f"Anthropic progress: {i}/{len(anthropic_ids)}")
        
        # Early exit after reasonable batch
        if i >= 5:
            break
    
    # Process Gemini analyses
    logger.info(f"Processing {len(gemini_ids)} Gemini analyses")
    for i, transcript_id in enumerate(gemini_ids, 1):
        if complete_single_transcript(transcript_id, 'gemini'):
            total_processed += 1
        time.sleep(2)  # Rate limiting
        logger.info(f"Gemini progress: {i}/{len(gemini_ids)}")
        
        # Early exit after reasonable batch
        if i >= 5:
            break
    
    # Final status report
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
        
        logger.info(f"Session completed: {total_processed} new analyses")
        logger.info(f"Current status:")
        logger.info(f"  Anthropic: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
        logger.info(f"  Gemini: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")

if __name__ == "__main__":
    run_systematic_completion()