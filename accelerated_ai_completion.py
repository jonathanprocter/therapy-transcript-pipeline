"""
Accelerated AI completion with intelligent prioritization
Completes remaining Anthropic and Gemini analyses efficiently
"""

import json
import logging
import time
from datetime import datetime
from app import app, db
from models import Transcript, Client
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prioritize_transcripts():
    """Intelligently prioritize transcripts for processing"""
    with app.app_context():
        # Priority 1: Recent transcripts without any AI analysis
        recent_incomplete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None),
            Transcript.gemini_analysis.is_(None),
            Transcript.session_date >= '2025-01-01'
        ).order_by(Transcript.session_date.desc()).limit(3).all()
        
        # Priority 2: Transcripts missing Anthropic analysis
        anthropic_missing = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.is_(None)
        ).limit(5).all()
        
        # Priority 3: Transcripts missing Gemini analysis
        gemini_missing = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.is_(None)
        ).limit(5).all()
        
        return recent_incomplete, anthropic_missing, gemini_missing

def process_anthropic_batch(transcripts):
    """Process Anthropic analyses with optimized error handling"""
    with app.app_context():
        ai_service = AIService()
        completed = 0
        
        for transcript in transcripts:
            try:
                if not transcript.anthropic_analysis:
                    logger.info(f"Anthropic: {transcript.original_filename[:40]}...")
                    analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                    
                    if analysis:
                        transcript.anthropic_analysis = analysis
                        db.session.commit()
                        completed += 1
                        logger.info(f"✓ Completed ({completed})")
                        time.sleep(1)  # Reduced rate limiting
                    
            except Exception as e:
                logger.error(f"Error: {str(e)[:50]}")
                db.session.rollback()
                time.sleep(2)
        
        return completed

def process_gemini_batch(transcripts):
    """Process Gemini analyses with optimized error handling"""
    with app.app_context():
        ai_service = AIService()
        completed = 0
        
        for transcript in transcripts:
            try:
                if not transcript.gemini_analysis:
                    logger.info(f"Gemini: {transcript.original_filename[:40]}...")
                    analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                    
                    if analysis:
                        transcript.gemini_analysis = analysis
                        db.session.commit()
                        completed += 1
                        logger.info(f"✓ Completed ({completed})")
                        time.sleep(0.5)  # Reduced rate limiting
                    
            except Exception as e:
                logger.error(f"Error: {str(e)[:50]}")
                db.session.rollback()
                time.sleep(1)
        
        return completed

def run_accelerated_completion():
    """Run accelerated AI completion with intelligent prioritization"""
    logger.info("Starting accelerated AI completion")
    
    recent, anthropic_list, gemini_list = prioritize_transcripts()
    
    # Process recent incomplete first
    if recent:
        logger.info(f"Processing {len(recent)} recent incomplete transcripts")
        anthropic_completed = process_anthropic_batch(recent)
        gemini_completed = process_gemini_batch(recent)
    
    # Process remaining Anthropic
    remaining_anthropic = [t for t in anthropic_list if t not in recent][:3]
    if remaining_anthropic:
        logger.info(f"Processing {len(remaining_anthropic)} Anthropic analyses")
        anthropic_completed = process_anthropic_batch(remaining_anthropic)
    
    # Process remaining Gemini
    remaining_gemini = [t for t in gemini_list if t not in recent][:3]
    if remaining_gemini:
        logger.info(f"Processing {len(remaining_gemini)} Gemini analyses")
        gemini_completed = process_gemini_batch(remaining_gemini)
    
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
        
        logger.info(f"Final Status: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")

if __name__ == "__main__":
    run_accelerated_completion()