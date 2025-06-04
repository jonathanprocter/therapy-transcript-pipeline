"""
Efficient AI completion - minimal single transcript processing
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def process_one_anthropic():
    """Process one transcript for Anthropic analysis"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        with app.app_context():
            from sqlalchemy import text
            
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name
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
            
            transcript_id, filename, client_name = row
            logger.info(f"Processing Anthropic: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript or not transcript.raw_content:
                return False
            
            # Create a focused clinical prompt
            focused_prompt = f"""You are an expert clinical therapist. Analyze this therapy session transcript and create a comprehensive clinical progress note following professional standards.

Create sections for:
1. SUBJECTIVE - Client's reported experiences and concerns
2. OBJECTIVE - Observed behaviors and demeanor  
3. ASSESSMENT - Clinical evaluation and patterns
4. PLAN - Treatment recommendations and interventions
5. KEY INSIGHTS - Most significant therapeutic observations

Make the analysis detailed and clinically sophisticated, approximately 2000-3000 words.

Transcript:
{transcript.raw_content}"""
            
            response = client.messages.create(
                model=Config.ANTHROPIC_MODEL,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": focused_prompt}]
            )
            
            analysis = response.content[0].text.strip()
            if len(analysis) > 500:
                transcript.anthropic_analysis = analysis
                db.session.commit()
                logger.info(f"✓ Anthropic complete ({len(analysis)} chars)")
                return True
            else:
                logger.warning(f"Analysis too short: {len(analysis)} chars")
                return False
                
    except Exception as e:
        logger.error(f"Anthropic failed: {str(e)[:200]}")
        return False

def process_one_gemini():
    """Process one transcript for Gemini analysis"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with app.app_context():
            from sqlalchemy import text
            
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name
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
            
            transcript_id, filename, client_name = row
            logger.info(f"Processing Gemini: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript or not transcript.raw_content:
                return False
            
            # Create a focused clinical prompt
            focused_prompt = f"""You are an expert clinical therapist. Analyze this therapy session transcript and create a comprehensive clinical progress note following professional standards.

Create sections for:
1. SUBJECTIVE - Client's reported experiences and concerns
2. OBJECTIVE - Observed behaviors and demeanor  
3. ASSESSMENT - Clinical evaluation and patterns
4. PLAN - Treatment recommendations and interventions
5. KEY INSIGHTS - Most significant therapeutic observations

Make the analysis detailed and clinically sophisticated, approximately 2000-3000 words.

Transcript:
{transcript.raw_content}"""
            
            response = model.generate_content(
                focused_prompt,
                generation_config={'max_output_tokens': 4000, 'temperature': 0.3}
            )
            
            analysis = response.text.strip()
            if len(analysis) > 500:
                transcript.gemini_analysis = analysis
                db.session.commit()
                logger.info(f"✓ Gemini complete ({len(analysis)} chars)")
                return True
            else:
                logger.warning(f"Analysis too short: {len(analysis)} chars")
                return False
                
    except Exception as e:
        logger.error(f"Gemini failed: {str(e)[:200]}")
        return False

def get_progress():
    """Get current progress"""
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
        
        logger.info(f"Progress: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}")
        return total, anthropic_done, gemini_done

def main():
    """Main processing function"""
    logger.info("Starting efficient AI completion")
    
    total, anthropic_done, gemini_done = get_progress()
    
    # Process one of each if needed
    if anthropic_done < total:
        process_one_anthropic()
        time.sleep(2)
    
    if gemini_done < total:
        process_one_gemini()
        time.sleep(2)
    
    # Final progress
    get_progress()

if __name__ == "__main__":
    main()