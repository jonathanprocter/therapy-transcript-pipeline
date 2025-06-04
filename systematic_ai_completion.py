"""
Systematic AI completion - process transcripts one at a time
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

def process_single_anthropic():
    """Process one transcript for Anthropic analysis"""
    import anthropic
    
    anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    with app.app_context():
        from sqlalchemy import text
        
        # Get one transcript missing Anthropic analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name, CHAR_LENGTH(t.raw_content) as content_len
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            AND (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
            ORDER BY t.id
            LIMIT 1
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        
        if not row:
            logger.info("No transcripts need Anthropic analysis")
            return False
        
        transcript_id, filename, client_name, content_len = row
        logger.info(f"Anthropic: {client_name} - {filename} ({content_len} chars)")
        
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            return False
        
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
                logger.info(f"✓ Complete ({len(analysis)} chars)")
                return True
            else:
                logger.warning(f"Analysis too short: {len(analysis)} chars")
                return False
                
        except Exception as e:
            logger.error(f"Failed: {str(e)[:100]}")
            return False

def process_single_gemini():
    """Process one transcript for Gemini analysis"""
    import google.generativeai as genai
    
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    with app.app_context():
        from sqlalchemy import text
        
        # Get one transcript missing Gemini analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name, CHAR_LENGTH(t.raw_content) as content_len
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            AND (t.gemini_analysis IS NULL OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000)
            ORDER BY t.id
            LIMIT 1
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        
        if not row:
            logger.info("No transcripts need Gemini analysis")
            return False
        
        transcript_id, filename, client_name, content_len = row
        logger.info(f"Gemini: {client_name} - {filename} ({content_len} chars)")
        
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            return False
        
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
                logger.info(f"✓ Complete ({len(analysis)} chars)")
                return True
            else:
                logger.warning(f"Analysis too short: {len(analysis)} chars")
                return False
                
        except Exception as e:
            logger.error(f"Failed: {str(e)[:100]}")
            return False

def get_status():
    """Get current completion status"""
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
        return total, anthropic_done, gemini_done

def main():
    """Main processing function"""
    logger.info("Starting systematic AI processing")
    
    total, anthropic_done, gemini_done = get_status()
    logger.info(f"Initial status: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")
    
    # Process one Anthropic if needed
    if anthropic_done < total:
        success = process_single_anthropic()
        if success:
            time.sleep(2)
    
    # Process one Gemini if needed
    if gemini_done < total:
        success = process_single_gemini()
        if success:
            time.sleep(2)
    
    # Final status
    total, anthropic_done, gemini_done = get_status()
    logger.info(f"Final status: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")

if __name__ == "__main__":
    main()