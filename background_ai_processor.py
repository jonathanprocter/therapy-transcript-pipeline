"""
Background AI processor that runs efficiently without timeouts
Processes transcripts in small batches with proper error handling
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript, ProcessingLog
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def process_single_batch():
    """Process a single batch of 3 transcripts"""
    import anthropic
    import google.generativeai as genai
    
    # Initialize clients
    anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    with app.app_context():
        from sqlalchemy import text
        
        # Get 3 transcripts missing analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            AND (
                (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
                OR 
                (t.gemini_analysis IS NULL OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000)
            )
            ORDER BY t.id
            LIMIT 3
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        if not transcripts:
            logger.info("No transcripts need processing")
            return 0
        
        processed = 0
        
        for row in transcripts:
            transcript_id, filename, client_name = row
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                continue
            
            logger.info(f"Processing: {client_name} - {filename}")
            
            # Anthropic Analysis
            if not transcript.anthropic_analysis or len(str(transcript.anthropic_analysis)) < 1000:
                try:
                    response = anthropic_client.messages.create(
                        model=Config.ANTHROPIC_MODEL,
                        max_tokens=4000,
                        temperature=0.3,
                        messages=[
                            {"role": "user", "content": f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}"}
                        ]
                    )
                    
                    analysis = response.content[0].text.strip()
                    if len(analysis) > 500:
                        transcript.anthropic_analysis = analysis
                        logger.info(f"  ✓ Anthropic complete")
                        
                except Exception as e:
                    logger.error(f"  Anthropic failed: {str(e)[:50]}")
                
                time.sleep(3)
            
            # Gemini Analysis
            if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
                try:
                    response = gemini_model.generate_content(
                        f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}",
                        generation_config={'max_output_tokens': 4000, 'temperature': 0.3}
                    )
                    
                    analysis = response.text.strip()
                    if len(analysis) > 500:
                        transcript.gemini_analysis = analysis
                        logger.info(f"  ✓ Gemini complete")
                        
                except Exception as e:
                    logger.error(f"  Gemini failed: {str(e)[:50]}")
                
                time.sleep(3)
            
            # Update status if complete
            openai_complete = transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000
            anthropic_complete = transcript.anthropic_analysis and len(str(transcript.anthropic_analysis)) > 1000
            gemini_complete = transcript.gemini_analysis and len(str(transcript.gemini_analysis)) > 1000
            
            if openai_complete and anthropic_complete and gemini_complete:
                transcript.processing_status = 'completed'
            
            db.session.commit()
            processed += 1
        
        return processed

def run_background_processor():
    """Run the background processor for multiple batches"""
    logger.info("Starting background AI processor")
    
    for batch in range(5):  # Process 5 batches
        processed = process_single_batch()
        if processed == 0:
            logger.info(f"Batch {batch + 1}: No more transcripts to process")
            break
        else:
            logger.info(f"Batch {batch + 1}: Processed {processed} transcripts")
            time.sleep(10)  # Wait between batches
    
    # Final status
    with app.app_context():
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                COUNT(CASE WHEN gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done
            FROM transcript 
            WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        total, anthropic_done, gemini_done = row
        
        logger.info(f"FINAL STATUS: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")

if __name__ == "__main__":
    run_background_processor()