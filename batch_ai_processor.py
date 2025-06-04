"""
Batch AI processor for completing missing Anthropic and Gemini analysis
Processes transcripts efficiently with proper rate limiting
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

def process_anthropic_batch():
    """Process a batch of transcripts for Anthropic analysis"""
    import anthropic
    
    anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    with app.app_context():
        from sqlalchemy import text
        
        # Get 10 transcripts missing Anthropic analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            AND (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
            ORDER BY t.id
            LIMIT 10
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        if not transcripts:
            logger.info("No transcripts need Anthropic analysis")
            return 0
        
        logger.info(f"Processing {len(transcripts)} transcripts for Anthropic analysis")
        processed = 0
        
        for row in transcripts:
            transcript_id, filename, client_name = row
            logger.info(f"Anthropic: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                continue
            
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
                    db.session.commit()
                    processed += 1
                    logger.info(f"  ✓ Complete ({len(analysis)} chars)")
                    
            except Exception as e:
                logger.error(f"  Failed: {str(e)[:100]}")
            
            time.sleep(3)  # Rate limiting
        
        logger.info(f"Anthropic batch complete: {processed}/{len(transcripts)}")
        return processed

def process_gemini_batch():
    """Process a batch of transcripts for Gemini analysis"""
    import google.generativeai as genai
    
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    
    with app.app_context():
        from sqlalchemy import text
        
        # Get 10 transcripts missing Gemini analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            AND (t.gemini_analysis IS NULL OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000)
            ORDER BY t.id
            LIMIT 10
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        if not transcripts:
            logger.info("No transcripts need Gemini analysis")
            return 0
        
        logger.info(f"Processing {len(transcripts)} transcripts for Gemini analysis")
        processed = 0
        
        for row in transcripts:
            transcript_id, filename, client_name = row
            logger.info(f"Gemini: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                continue
            
            try:
                response = gemini_model.generate_content(
                    f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}",
                    generation_config={
                        'max_output_tokens': 4000,
                        'temperature': 0.3
                    }
                )
                
                analysis = response.text.strip()
                if len(analysis) > 500:
                    transcript.gemini_analysis = analysis
                    db.session.commit()
                    processed += 1
                    logger.info(f"  ✓ Complete ({len(analysis)} chars)")
                    
            except Exception as e:
                logger.error(f"  Failed: {str(e)[:100]}")
            
            time.sleep(3)  # Rate limiting
        
        logger.info(f"Gemini batch complete: {processed}/{len(transcripts)}")
        return processed

def update_completion_status():
    """Update processing status for completed transcripts"""
    with app.app_context():
        from sqlalchemy import text
        
        # Update status for transcripts with all analyses
        query = text("""
            UPDATE transcript 
            SET processing_status = 'completed'
            WHERE processing_status != 'completed'
            AND openai_analysis IS NOT NULL 
            AND CHAR_LENGTH(CAST(openai_analysis AS TEXT)) > 1000
            AND anthropic_analysis IS NOT NULL 
            AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000
            AND gemini_analysis IS NOT NULL 
            AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000
        """)
        
        result = db.session.execute(query)
        updated = result.rowcount
        db.session.commit()
        
        if updated > 0:
            logger.info(f"Updated status for {updated} completed transcripts")
        
        return updated

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
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as status_complete
            FROM transcript 
            WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        
        total, openai_done, anthropic_done, gemini_done, status_complete = row
        
        logger.info("CURRENT STATUS:")
        logger.info(f"Total: {total}")
        logger.info(f"OpenAI: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
        logger.info(f"Anthropic: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
        logger.info(f"Gemini: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
        logger.info(f"Complete: {status_complete}/{total} ({status_complete/total*100:.1f}%)")
        
        return {
            'total': total,
            'openai_done': openai_done,
            'anthropic_done': anthropic_done,
            'gemini_done': gemini_done,
            'status_complete': status_complete
        }

def main():
    """Main processing function"""
    logger.info("Starting batch AI processing")
    
    # Process Anthropic analysis
    anthropic_processed = process_anthropic_batch()
    time.sleep(5)  # Cool down
    
    # Process Gemini analysis
    gemini_processed = process_gemini_batch()
    time.sleep(5)  # Cool down
    
    # Update completion status
    updated = update_completion_status()
    
    # Final status
    status = get_completion_status()
    
    logger.info(f"Session complete: Anthropic +{anthropic_processed}, Gemini +{gemini_processed}, Status updated: {updated}")

if __name__ == "__main__":
    main()