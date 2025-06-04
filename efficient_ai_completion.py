"""
Efficient AI completion for missing Anthropic and Gemini analysis
Processes transcripts in very small batches to avoid timeouts
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

def process_single_transcript(transcript_id):
    """Process a single transcript with Anthropic and Gemini analysis"""
    import anthropic
    import google.generativeai as genai
    
    # Initialize clients
    anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    
    with app.app_context():
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript or not transcript.raw_content:
            return False
        
        success_count = 0
        
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
                    success_count += 1
                    logger.info(f"  ✓ Anthropic complete ({len(analysis)} chars)")
                    
            except Exception as e:
                logger.error(f"  Anthropic failed: {str(e)[:50]}")
            
            time.sleep(3)
        else:
            success_count += 1
        
        # Gemini Analysis
        if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
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
                    success_count += 1
                    logger.info(f"  ✓ Gemini complete ({len(analysis)} chars)")
                    
            except Exception as e:
                logger.error(f"  Gemini failed: {str(e)[:50]}")
            
            time.sleep(3)
        else:
            success_count += 1
        
        # Check OpenAI
        if transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000:
            success_count += 1
        
        # Update status if all complete
        if success_count >= 3:
            transcript.processing_status = 'completed'
            
            log_entry = ProcessingLog(
                transcript_id=transcript.id,
                status='success',
                message=f"Completed comprehensive AI analysis with all 3 providers",
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(log_entry)
        
        db.session.commit()
        return success_count >= 2  # At least 2 of 3 providers

def process_batch():
    """Process a small batch of 5 transcripts"""
    with app.app_context():
        from sqlalchemy import text
        
        # Get 5 transcripts missing analysis
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
            LIMIT 5
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        if not transcripts:
            return 0
        
        logger.info(f"Processing batch of {len(transcripts)} transcripts")
        processed = 0
        
        for row in transcripts:
            transcript_id, filename, client_name = row
            logger.info(f"Processing: {client_name} - {filename}")
            
            if process_single_transcript(transcript_id):
                processed += 1
            
            time.sleep(2)  # Rate limiting between transcripts
        
        logger.info(f"Batch complete: {processed}/{len(transcripts)} successful")
        return processed

def main():
    """Main execution - process multiple small batches"""
    total_processed = 0
    
    for batch_num in range(1, 21):  # Process up to 20 batches (100 transcripts)
        logger.info(f"Starting batch {batch_num}")
        
        processed = process_batch()
        total_processed += processed
        
        if processed == 0:
            logger.info("No more transcripts to process")
            break
        
        logger.info(f"Total processed so far: {total_processed}")
        time.sleep(5)  # Cool down between batches
    
    # Final status check
    with app.app_context():
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                COUNT(CASE WHEN gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done,
                COUNT(CASE WHEN openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_done
            FROM transcript 
            WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        
        total, anthropic_done, gemini_done, openai_done = row
        
        logger.info("FINAL STATUS:")
        logger.info(f"Total: {total}")
        logger.info(f"OpenAI: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
        logger.info(f"Anthropic: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
        logger.info(f"Gemini: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
        logger.info(f"Total processed this session: {total_processed}")

if __name__ == "__main__":
    main()