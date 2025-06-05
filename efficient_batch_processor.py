"""
Efficient batch processor for completing remaining AI analyses
Processes transcripts in small batches with proper error handling and rate limiting
"""

import os
import sys
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import app, db
from models import Transcript, Client
from services.ai_service import AIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EfficientBatchProcessor:
    def __init__(self):
        self.ai_service = AIService()
        
    def get_incomplete_transcripts(self, batch_size=5):
        """Get transcripts missing AI analysis"""
        with app.app_context():
            # Get transcripts missing Anthropic analysis
            anthropic_incomplete = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.anthropic_analysis.is_(None)
            ).limit(batch_size).all()
            
            # Get transcripts missing Gemini analysis  
            gemini_incomplete = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.gemini_analysis.is_(None)
            ).limit(batch_size).all()
            
            return anthropic_incomplete, gemini_incomplete
    
    def process_anthropic_batch(self, transcripts):
        """Process a batch for Anthropic analysis"""
        with app.app_context():
            for transcript in transcripts:
                try:
                    if not transcript.anthropic_analysis:
                        logger.info(f"Processing Anthropic: {transcript.filename}")
                        
                        # Generate analysis
                        analysis = self.ai_service._analyze_with_anthropic(transcript.raw_text)
                        
                        if analysis:
                            transcript.anthropic_analysis = analysis
                            db.session.commit()
                            logger.info(f"Completed Anthropic analysis for {transcript.filename}")
                            
                            # Rate limiting
                            time.sleep(2)
                        else:
                            logger.warning(f"No analysis generated for {transcript.filename}")
                            
                except Exception as e:
                    logger.error(f"Error processing {transcript.filename} with Anthropic: {e}")
                    db.session.rollback()
                    continue
    
    def process_gemini_batch(self, transcripts):
        """Process a batch for Gemini analysis"""
        with app.app_context():
            for transcript in transcripts:
                try:
                    if not transcript.gemini_analysis:
                        logger.info(f"Processing Gemini: {transcript.filename}")
                        
                        # Generate analysis
                        analysis = self.ai_service._analyze_with_gemini(transcript.raw_text)
                        
                        if analysis:
                            transcript.gemini_analysis = analysis
                            db.session.commit()
                            logger.info(f"Completed Gemini analysis for {transcript.filename}")
                            
                            # Rate limiting
                            time.sleep(1)
                        else:
                            logger.warning(f"No analysis generated for {transcript.filename}")
                            
                except Exception as e:
                    logger.error(f"Error processing {transcript.filename} with Gemini: {e}")
                    db.session.rollback()
                    continue
    
    def get_completion_status(self):
        """Get current completion status"""
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
            
            return {
                'total': total,
                'openai': openai_complete,
                'anthropic': anthropic_complete,
                'gemini': gemini_complete
            }
    
    def run_single_batch(self):
        """Run a single batch of processing"""
        logger.info("Starting single batch processing")
        
        # Get status before processing
        status_before = self.get_completion_status()
        logger.info(f"Before: OpenAI: {status_before['openai']}/{status_before['total']}, "
                   f"Anthropic: {status_before['anthropic']}/{status_before['total']}, "
                   f"Gemini: {status_before['gemini']}/{status_before['total']}")
        
        # Get incomplete transcripts
        anthropic_batch, gemini_batch = self.get_incomplete_transcripts(batch_size=3)
        
        # Process Anthropic batch
        if anthropic_batch:
            logger.info(f"Processing {len(anthropic_batch)} transcripts for Anthropic")
            self.process_anthropic_batch(anthropic_batch)
        
        # Process Gemini batch
        if gemini_batch:
            logger.info(f"Processing {len(gemini_batch)} transcripts for Gemini")
            self.process_gemini_batch(gemini_batch)
        
        # Get status after processing
        status_after = self.get_completion_status()
        logger.info(f"After: OpenAI: {status_after['openai']}/{status_after['total']}, "
                   f"Anthropic: {status_after['anthropic']}/{status_after['total']}, "
                   f"Gemini: {status_after['gemini']}/{status_after['total']}")
        
        progress_made = (
            (status_after['anthropic'] > status_before['anthropic']) or 
            (status_after['gemini'] > status_before['gemini'])
        )
        
        return progress_made, status_after

def main():
    """Main execution function"""
    processor = EfficientBatchProcessor()
    
    # Run a single batch
    progress_made, final_status = processor.run_single_batch()
    
    if progress_made:
        logger.info("✓ Batch processing completed successfully")
    else:
        logger.info("→ No incomplete transcripts found or processing complete")
    
    logger.info(f"Final Status - Total: {final_status['total']}, "
               f"OpenAI: {final_status['openai']}, "
               f"Anthropic: {final_status['anthropic']}, "
               f"Gemini: {final_status['gemini']}")

if __name__ == "__main__":
    main()