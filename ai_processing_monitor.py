"""
AI Processing Monitor - Real-time tracking of Anthropic and Gemini completion
"""

import logging
import time
import json
from datetime import datetime
from app import app, db
from models import Transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_detailed_progress():
    """Get detailed progress statistics"""
    with app.app_context():
        total = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed'
        ).count()
        
        # OpenAI stats
        openai_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.openai_analysis.isnot(None)
        ).count()
        
        # Anthropic stats
        anthropic_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        
        # Gemini stats
        gemini_complete = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        # Notion sync stats
        notion_synced = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.notion_synced == True
        ).count()
        
        return {
            'total': total,
            'openai': {'complete': openai_complete, 'percent': round(openai_complete/total*100, 1)},
            'anthropic': {'complete': anthropic_complete, 'percent': round(anthropic_complete/total*100, 1)},
            'gemini': {'complete': gemini_complete, 'percent': round(gemini_complete/total*100, 1)},
            'notion': {'synced': notion_synced, 'percent': round(notion_synced/total*100, 1)}
        }

def get_recent_completions():
    """Get recently completed analyses"""
    with app.app_context():
        # Get transcripts updated in last hour
        recent_anthropic = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.anthropic_analysis.isnot(None),
            Transcript.updated_at >= datetime.utcnow().replace(hour=datetime.utcnow().hour-1)
        ).count()
        
        recent_gemini = db.session.query(Transcript).filter(
            Transcript.processing_status == 'completed',
            Transcript.gemini_analysis.isnot(None),
            Transcript.updated_at >= datetime.utcnow().replace(hour=datetime.utcnow().hour-1)
        ).count()
        
        return recent_anthropic, recent_gemini

def monitor_progress():
    """Monitor and display progress"""
    logger.info("AI Processing Monitor - Real-time Progress Tracking")
    logger.info("=" * 60)
    
    progress = get_detailed_progress()
    recent_anthropic, recent_gemini = get_recent_completions()
    
    # Display current status
    logger.info(f"TRANSCRIPT PROCESSING STATUS:")
    logger.info(f"  Total Transcripts: {progress['total']}")
    logger.info(f"  Notion Sync: {progress['notion']['synced']}/{progress['total']} ({progress['notion']['percent']}%)")
    logger.info("")
    
    logger.info(f"AI ANALYSIS COMPLETION:")
    logger.info(f"  OpenAI:    {progress['openai']['complete']:>2}/{progress['total']} ({progress['openai']['percent']:>5.1f}%)")
    logger.info(f"  Anthropic: {progress['anthropic']['complete']:>2}/{progress['total']} ({progress['anthropic']['percent']:>5.1f}%)")
    logger.info(f"  Gemini:    {progress['gemini']['complete']:>2}/{progress['total']} ({progress['gemini']['percent']:>5.1f}%)")
    logger.info("")
    
    # Remaining work
    anthropic_remaining = progress['total'] - progress['anthropic']['complete']
    gemini_remaining = progress['total'] - progress['gemini']['complete']
    
    logger.info(f"REMAINING ANALYSES:")
    logger.info(f"  Anthropic: {anthropic_remaining} transcripts")
    logger.info(f"  Gemini:    {gemini_remaining} transcripts")
    logger.info("")
    
    # Recent activity
    logger.info(f"RECENT ACTIVITY (Last Hour):")
    logger.info(f"  Anthropic completions: {recent_anthropic}")
    logger.info(f"  Gemini completions:    {recent_gemini}")
    logger.info("")
    
    # Processing efficiency estimate
    total_remaining = anthropic_remaining + gemini_remaining
    if total_remaining > 0:
        estimated_time = total_remaining * 2.5  # Assuming 2.5 minutes per analysis
        logger.info(f"ESTIMATED COMPLETION:")
        logger.info(f"  Remaining analyses: {total_remaining}")
        logger.info(f"  Estimated time: {estimated_time:.0f} minutes")
    else:
        logger.info(f"ALL ANALYSES COMPLETE!")
    
    logger.info("=" * 60)
    
    return progress

def continuous_monitoring(duration_minutes=30):
    """Run continuous monitoring for specified duration"""
    logger.info(f"Starting continuous monitoring for {duration_minutes} minutes")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    initial_progress = monitor_progress()
    
    while time.time() < end_time:
        time.sleep(120)  # Check every 2 minutes
        
        current_progress = get_detailed_progress()
        
        # Check for changes
        if (current_progress['anthropic']['complete'] != initial_progress['anthropic']['complete'] or
            current_progress['gemini']['complete'] != initial_progress['gemini']['complete']):
            
            logger.info(f"PROGRESS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
            anthropic_gained = current_progress['anthropic']['complete'] - initial_progress['anthropic']['complete']
            gemini_gained = current_progress['gemini']['complete'] - initial_progress['gemini']['complete']
            
            if anthropic_gained > 0:
                logger.info(f"  Anthropic: +{anthropic_gained} ({current_progress['anthropic']['complete']}/{current_progress['total']})")
            if gemini_gained > 0:
                logger.info(f"  Gemini: +{gemini_gained} ({current_progress['gemini']['complete']}/{current_progress['total']})")
            
            initial_progress = current_progress
    
    # Final summary
    final_progress = monitor_progress()
    logger.info("Monitoring session completed")

if __name__ == "__main__":
    # Run single progress check
    monitor_progress()
    
    # Optionally run continuous monitoring
    # continuous_monitoring(30)