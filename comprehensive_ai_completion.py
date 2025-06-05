"""
Comprehensive AI completion and duplicate cleanup system
Removes duplicate files and completes remaining AI analyses
"""

import logging
import time
from app import app, db
from models import Transcript
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_duplicate_files():
    """Remove duplicate files with (1) suffix"""
    with app.app_context():
        duplicates = db.session.query(Transcript).filter(
            Transcript.original_filename.like('%(1)%')
        ).all()
        
        logger.info(f"Found {len(duplicates)} duplicate files to remove")
        for duplicate in duplicates:
            logger.info(f"Removing duplicate: {duplicate.original_filename}")
            db.session.delete(duplicate)
        
        db.session.commit()
        logger.info(f"Removed {len(duplicates)} duplicate files")
        return len(duplicates)

def complete_anthropic_analyses():
    """Complete missing Anthropic analyses"""
    with app.app_context():
        ai_service = AIService()
        
        missing_anthropic = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(5).all()
        
        completed = 0
        for transcript in missing_anthropic:
            try:
                logger.info(f"Anthropic: {transcript.original_filename[:50]}")
                analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                
                if analysis:
                    transcript.anthropic_analysis = analysis
                    db.session.commit()
                    completed += 1
                    logger.info("Anthropic analysis completed")
                    time.sleep(3)
                    
            except Exception as e:
                logger.error(f"Anthropic error: {str(e)[:100]}")
                db.session.rollback()
                continue
        
        return completed

def complete_gemini_analyses():
    """Complete missing Gemini analyses"""
    with app.app_context():
        ai_service = AIService()
        
        missing_gemini = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(5).all()
        
        completed = 0
        for transcript in missing_gemini:
            try:
                logger.info(f"Gemini: {transcript.original_filename[:50]}")
                analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                
                if analysis:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    completed += 1
                    logger.info("Gemini analysis completed")
                    time.sleep(3)
                    
            except Exception as e:
                logger.error(f"Gemini error: {str(e)[:100]}")
                db.session.rollback()
                continue
        
        return completed

def get_final_status():
    """Get final completion status"""
    with app.app_context():
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        openai_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.openai_analysis.isnot(None)
        ).count()
        
        anthropic_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        gemini_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        notion_synced = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.notion_synced == True
        ).count()
        
        return {
            'total': total,
            'openai': openai_complete,
            'anthropic': anthropic_complete, 
            'gemini': gemini_complete,
            'notion': notion_synced
        }

def main():
    """Run comprehensive completion process"""
    logger.info("Starting comprehensive AI completion process")
    
    # Remove duplicates first
    duplicates_removed = remove_duplicate_files()
    
    # Get initial status
    initial_status = get_final_status()
    logger.info(f"Initial status after cleanup:")
    logger.info(f"  Total: {initial_status['total']} transcripts")
    logger.info(f"  OpenAI: {initial_status['openai']}/{initial_status['total']}")
    logger.info(f"  Anthropic: {initial_status['anthropic']}/{initial_status['total']}")
    logger.info(f"  Gemini: {initial_status['gemini']}/{initial_status['total']}")
    logger.info(f"  Notion: {initial_status['notion']}/{initial_status['total']}")
    
    # Complete Anthropic analyses
    logger.info("Processing Anthropic analyses...")
    anthropic_completed = complete_anthropic_analyses()
    
    time.sleep(5)
    
    # Complete Gemini analyses
    logger.info("Processing Gemini analyses...")
    gemini_completed = complete_gemini_analyses()
    
    # Final status
    final_status = get_final_status()
    logger.info("Comprehensive completion process finished")
    logger.info(f"Session results:")
    logger.info(f"  Duplicates removed: {duplicates_removed}")
    logger.info(f"  Anthropic completed: +{anthropic_completed}")
    logger.info(f"  Gemini completed: +{gemini_completed}")
    logger.info(f"Final status:")
    logger.info(f"  Total: {final_status['total']} transcripts")
    logger.info(f"  OpenAI: {final_status['openai']}/{final_status['total']} ({final_status['openai']/final_status['total']*100:.1f}%)")
    logger.info(f"  Anthropic: {final_status['anthropic']}/{final_status['total']} ({final_status['anthropic']/final_status['total']*100:.1f}%)")
    logger.info(f"  Gemini: {final_status['gemini']}/{final_status['total']} ({final_status['gemini']/final_status['total']*100:.1f}%)")
    logger.info(f"  Notion: {final_status['notion']}/{final_status['total']} ({final_status['notion']/final_status['total']*100:.1f}%)")

if __name__ == "__main__":
    main()