#!/usr/bin/env python3
"""
Complete AI processing for all remaining transcripts
Efficiently processes missing Anthropic and Gemini analyses
"""

import sys
import time
import logging
from app import app, db
from models import Transcript
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_remaining_analyses():
    """Process remaining Anthropic and Gemini analyses efficiently"""
    
    with app.app_context():
        ai_service = AIService()
        
        # Get status
        total = db.session.query(Transcript).count()
        anthropic_missing = db.session.query(Transcript).filter(
            Transcript.anthropic_analysis.is_(None)
        ).all()
        gemini_missing = db.session.query(Transcript).filter(
            Transcript.gemini_analysis.is_(None)
        ).all()
        
        logger.info(f"Total transcripts: {total}")
        logger.info(f"Missing Anthropic: {len(anthropic_missing)}")
        logger.info(f"Missing Gemini: {len(gemini_missing)}")
        
        # Process Anthropic analyses in batches
        logger.info("Starting Anthropic processing...")
        batch_size = 5
        for i in range(0, len(anthropic_missing), batch_size):
            batch = anthropic_missing[i:i+batch_size]
            logger.info(f"Processing Anthropic batch {i//batch_size + 1}/{(len(anthropic_missing) + batch_size - 1)//batch_size}")
            
            for transcript in batch:
                try:
                    logger.info(f"Anthropic: {transcript.original_filename}")
                    analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                    if analysis:
                        transcript.anthropic_analysis = analysis
                        db.session.commit()
                        logger.info(f"✓ Completed: {transcript.original_filename}")
                    else:
                        logger.error(f"✗ Failed: {transcript.original_filename}")
                except Exception as e:
                    logger.error(f"Error processing {transcript.original_filename}: {e}")
                    db.session.rollback()
                    continue
                
                # Rate limiting pause
                time.sleep(2)
            
            # Longer pause between batches
            if i + batch_size < len(anthropic_missing):
                logger.info("Pausing between batches...")
                time.sleep(10)
        
        # Process Gemini analyses in batches
        logger.info("Starting Gemini processing...")
        for i in range(0, len(gemini_missing), batch_size):
            batch = gemini_missing[i:i+batch_size]
            logger.info(f"Processing Gemini batch {i//batch_size + 1}/{(len(gemini_missing) + batch_size - 1)//batch_size}")
            
            for transcript in batch:
                try:
                    logger.info(f"Gemini: {transcript.original_filename}")
                    analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                    if analysis:
                        transcript.gemini_analysis = analysis
                        db.session.commit()
                        logger.info(f"✓ Completed: {transcript.original_filename}")
                    else:
                        logger.error(f"✗ Failed: {transcript.original_filename}")
                except Exception as e:
                    logger.error(f"Error processing {transcript.original_filename}: {e}")
                    db.session.rollback()
                    continue
                
                # Rate limiting pause
                time.sleep(2)
            
            # Longer pause between batches
            if i + batch_size < len(gemini_missing):
                logger.info("Pausing between batches...")
                time.sleep(10)
        
        # Final status report
        anthropic_complete = db.session.query(Transcript).filter(
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        gemini_complete = db.session.query(Transcript).filter(
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        logger.info(f"\nFinal Status:")
        logger.info(f"Anthropic complete: {anthropic_complete}/{total} ({anthropic_complete/total*100:.1f}%)")
        logger.info(f"Gemini complete: {gemini_complete}/{total} ({gemini_complete/total*100:.1f}%)")
        logger.info("AI processing completed!")

if __name__ == "__main__":
    try:
        process_remaining_analyses()
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)