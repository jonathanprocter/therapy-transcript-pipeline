"""
Intelligent transcript prioritization algorithm
Prioritizes transcripts based on multiple factors for optimal processing
"""

import json
import logging
from datetime import datetime, timedelta
from app import app, db
from models import Transcript, Client
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentPrioritizer:
    def __init__(self):
        self.priority_weights = {
            'recency': 0.3,
            'client_importance': 0.2,
            'completion_status': 0.3,
            'processing_efficiency': 0.2
        }
    
    def calculate_priority_score(self, transcript):
        """Calculate priority score for a transcript"""
        score = 0
        
        # Recency factor (newer = higher priority)
        if transcript.session_date:
            days_old = (datetime.now() - transcript.session_date).days
            recency_score = max(0, 1 - (days_old / 30))  # Full score for recent, decay over 30 days
            score += recency_score * self.priority_weights['recency']
        
        # Client importance (based on transcript count)
        with app.app_context():
            client_transcript_count = db.session.query(Transcript).filter(
                Transcript.client_id == transcript.client_id
            ).count()
            importance_score = min(1, client_transcript_count / 10)  # More transcripts = higher importance
            score += importance_score * self.priority_weights['client_importance']
        
        # Completion status (missing more analyses = higher priority)
        analyses_present = 0
        if transcript.openai_analysis: analyses_present += 1
        if transcript.anthropic_analysis: analyses_present += 1
        if transcript.gemini_analysis: analyses_present += 1
        
        completion_score = 1 - (analyses_present / 3)  # Missing analyses increase priority
        score += completion_score * self.priority_weights['completion_status']
        
        # Processing efficiency (shorter transcripts first for quick wins)
        if transcript.raw_content:
            content_length = len(transcript.raw_content)
            efficiency_score = max(0, 1 - (content_length / 10000))  # Shorter = more efficient
            score += efficiency_score * self.priority_weights['processing_efficiency']
        
        return score

    def get_prioritized_transcripts(self, limit=10):
        """Get transcripts prioritized by intelligent algorithm"""
        with app.app_context():
            # Get all incomplete transcripts
            transcripts = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                db.or_(
                    Transcript.anthropic_analysis.is_(None),
                    Transcript.gemini_analysis.is_(None)
                )
            ).all()
            
            # Calculate priority scores
            transcript_scores = []
            for transcript in transcripts:
                score = self.calculate_priority_score(transcript)
                transcript_scores.append((transcript, score))
            
            # Sort by priority score (highest first)
            transcript_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top prioritized transcripts
            return [t[0] for t in transcript_scores[:limit]]

def run_prioritized_processing():
    """Run AI processing with intelligent prioritization"""
    prioritizer = IntelligentPrioritizer()
    ai_service = AIService()
    
    with app.app_context():
        # Get prioritized transcripts
        priority_transcripts = prioritizer.get_prioritized_transcripts(5)
        
        logger.info(f"Processing {len(priority_transcripts)} prioritized transcripts")
        
        for i, transcript in enumerate(priority_transcripts, 1):
            logger.info(f"Priority {i}: {transcript.original_filename}")
            
            try:
                # Process missing Anthropic analysis
                if not transcript.anthropic_analysis:
                    logger.info("Generating Anthropic analysis...")
                    analysis = ai_service._analyze_with_anthropic(transcript.raw_content)
                    if analysis:
                        transcript.anthropic_analysis = analysis
                        db.session.commit()
                        logger.info("Anthropic analysis completed")
                
                # Process missing Gemini analysis
                if not transcript.gemini_analysis:
                    logger.info("Generating Gemini analysis...")
                    analysis = ai_service._analyze_with_gemini(transcript.raw_content)
                    if analysis:
                        transcript.gemini_analysis = analysis
                        db.session.commit()
                        logger.info("Gemini analysis completed")
                
            except Exception as e:
                logger.error(f"Error processing {transcript.original_filename}: {e}")
                db.session.rollback()
                continue
        
        # Final status update
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        anthropic_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        gemini_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        logger.info(f"Updated Status: Anthropic {anthropic_complete}/{total}, Gemini {gemini_complete}/{total}")

if __name__ == "__main__":
    run_prioritized_processing()