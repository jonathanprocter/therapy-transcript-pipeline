"""
Gradual AI processor that completes analysis without timing out
Processes one transcript at a time with proper error handling
"""
import os
import sys
import time
import logging
from datetime import datetime

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_single_transcript():
    """Process one transcript that needs AI analysis"""
    try:
        import anthropic
        import google.generativeai as genai
        
        # Initialize AI clients
        anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        with app.app_context():
            from sqlalchemy import text
            
            # Find one transcript needing analysis
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name, t.raw_content
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                AND (
                    t.anthropic_analysis IS NULL 
                    OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000
                    OR t.gemini_analysis IS NULL 
                    OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000
                )
                ORDER BY t.id
                LIMIT 1
            """)
            
            result = db.session.execute(query)
            row = result.fetchone()
            
            if not row:
                logger.info("✓ All transcripts have complete AI analysis")
                return False
            
            transcript_id, filename, client_name, content = row
            logger.info(f"Processing: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                return False
            
            progress = []
            
            # Complete Anthropic analysis if missing
            if not transcript.anthropic_analysis or len(str(transcript.anthropic_analysis)) < 1000:
                try:
                    logger.info("Starting Anthropic analysis...")
                    response = anthropic_client.messages.create(
                        model=Config.ANTHROPIC_MODEL,
                        max_tokens=4000,
                        temperature=0.3,
                        messages=[{"role": "user", "content": f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{content}"}]
                    )
                    
                    analysis = response.content[0].text.strip()
                    if len(analysis) > 500:
                        transcript.anthropic_analysis = analysis
                        progress.append(f"Anthropic: {len(analysis)} chars")
                        logger.info(f"✓ Anthropic complete: {len(analysis)} chars")
                    else:
                        logger.warning(f"Anthropic analysis too short: {len(analysis)} chars")
                        
                except Exception as e:
                    logger.error(f"Anthropic failed: {str(e)[:100]}")
            else:
                progress.append("Anthropic: already complete")
            
            # Complete Gemini analysis if missing
            if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
                try:
                    logger.info("Starting Gemini analysis...")
                    response = gemini_model.generate_content(
                        f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{content}",
                        generation_config={'max_output_tokens': 4000, 'temperature': 0.3}
                    )
                    
                    analysis = response.text.strip()
                    if len(analysis) > 500:
                        transcript.gemini_analysis = analysis
                        progress.append(f"Gemini: {len(analysis)} chars")
                        logger.info(f"✓ Gemini complete: {len(analysis)} chars")
                    else:
                        logger.warning(f"Gemini analysis too short: {len(analysis)} chars")
                        
                except Exception as e:
                    logger.error(f"Gemini failed: {str(e)[:100]}")
            else:
                progress.append("Gemini: already complete")
            
            # Update completion status
            openai_complete = transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000
            anthropic_complete = transcript.anthropic_analysis and len(str(transcript.anthropic_analysis)) > 1000
            gemini_complete = transcript.gemini_analysis and len(str(transcript.gemini_analysis)) > 1000
            
            if openai_complete and anthropic_complete and gemini_complete:
                transcript.processing_status = 'completed'
                progress.append("Status: fully completed")
                logger.info("✓ All 3 AI providers complete")
            
            db.session.commit()
            logger.info(f"Progress: {', '.join(progress)}")
            return True
            
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return False

def get_completion_status():
    """Get current completion status"""
    with app.app_context():
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_done,
                COUNT(CASE WHEN anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                COUNT(CASE WHEN gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed
            FROM transcript 
            WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        total, openai_done, anthropic_done, gemini_done, completed = row
        
        logger.info(f"STATUS: Total={total}, OpenAI={openai_done}, Anthropic={anthropic_done}, Gemini={gemini_done}, Completed={completed}")
        return total, openai_done, anthropic_done, gemini_done, completed

def main():
    """Main processing function"""
    logger.info("Starting gradual AI processor")
    
    # Show initial status
    get_completion_status()
    
    # Process multiple transcripts with delays
    for i in range(5):  # Process up to 5 transcripts
        logger.info(f"\n=== Batch {i+1} ===")
        success = process_single_transcript()
        
        if not success:
            logger.info("No more transcripts to process")
            break
        
        # Show progress
        get_completion_status()
        
        # Brief delay between transcripts
        if i < 4:  # Don't delay after last transcript
            logger.info("Waiting 5 seconds before next transcript...")
            time.sleep(5)
    
    logger.info("\nGradual processing session complete")

if __name__ == "__main__":
    main()