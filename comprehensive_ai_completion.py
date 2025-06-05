"""
Comprehensive AI completion and duplicate cleanup system
Removes duplicate files and completes remaining AI analyses
"""

import json
import logging
from app import app, db
from models import Transcript, Client
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_duplicate_files():
    """Remove duplicate files with (1) suffix"""
    with app.app_context():
        logger.info("Checking for duplicate files...")
        
        # Find files with (1) suffix
        duplicate_files = db.session.query(Transcript).filter(
            Transcript.original_filename.like('%(%')).all()
        
        logger.info(f"Found {len(duplicate_files)} potential duplicate files")
        
        for transcript in duplicate_files:
            # Check if original version exists
            base_filename = transcript.original_filename.replace(' (1)', '')
            original = db.session.query(Transcript).filter(
                Transcript.client_id == transcript.client_id,
                Transcript.original_filename == base_filename
            ).first()
            
            if original:
                logger.info(f"Removing duplicate: {transcript.original_filename}")
                db.session.delete(transcript)
            else:
                # Rename to remove (1) suffix
                logger.info(f"Renaming: {transcript.original_filename} -> {base_filename}")
                transcript.original_filename = base_filename
        
        db.session.commit()
        logger.info("Duplicate cleanup completed")

def complete_anthropic_analyses():
    """Complete missing Anthropic analyses"""
    with app.app_context():
        ai_service = AIService()
        
        incomplete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(10).all()
        
        logger.info(f"Processing {len(incomplete)} transcripts for Anthropic analysis")
        
        for transcript in incomplete:
            try:
                logger.info(f"Anthropic: {transcript.original_filename}")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    logger.info(f"✓ Completed: {transcript.original_filename}")
                
            except Exception as e:
                logger.error(f"Error: {e}")
                db.session.rollback()

def complete_gemini_analyses():
    """Complete missing Gemini analyses"""
    with app.app_context():
        ai_service = AIService()
        
        incomplete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(10).all()
        
        logger.info(f"Processing {len(incomplete)} transcripts for Gemini analysis")
        
        for transcript in incomplete:
            try:
                logger.info(f"Gemini: {transcript.original_filename}")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    logger.info(f"✓ Completed: {transcript.original_filename}")
                
            except Exception as e:
                logger.error(f"Error: {e}")
                db.session.rollback()

def get_final_status():
    """Get final completion status"""
    with app.app_context():
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        openai = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.openai_analysis.isnot(None)
        ).count()
        
        anthropic = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        gemini = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        logger.info(f"Final Status: {total} total transcripts")
        logger.info(f"OpenAI: {openai}/{total} ({openai/total*100:.1f}%)")
        logger.info(f"Anthropic: {anthropic}/{total} ({anthropic/total*100:.1f}%)")
        logger.info(f"Gemini: {gemini}/{total} ({gemini/total*100:.1f}%)")

def main():
    """Run comprehensive completion process"""
    logger.info("Starting comprehensive AI completion and cleanup")
    
    # Step 1: Remove duplicates
    remove_duplicate_files()
    
    # Step 2: Complete Anthropic analyses
    complete_anthropic_analyses()
    
    # Step 3: Complete Gemini analyses
    complete_gemini_analyses()
    
    # Step 4: Show final status
    get_final_status()
    
    logger.info("Comprehensive completion process finished")

if __name__ == "__main__":
    main()