"""
Background AI processor that runs efficiently without timeouts
Processes transcripts in small batches with proper error handling
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.append('/home/runner/workspace')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_single_batch():
    """Process a single batch of 3 transcripts"""
    try:
        import openai
        import anthropic
        import google.generativeai as genai
        from sqlalchemy import text
        from app import app, db
        from models import Transcript, ProcessingLog
        from config import Config
        
        # Initialize AI clients
        openai.api_key = Config.OPENAI_API_KEY
        anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        
        with app.app_context():
            # Get 3 transcripts missing analysis
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
                AND t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                ORDER BY t.id
                LIMIT 3
            """)
            
            result = db.session.execute(query)
            incomplete = result.fetchall()
            
            if not incomplete:
                logger.info("No more transcripts need processing")
                return 0
            
            logger.info(f"Processing {len(incomplete)} transcripts")
            processed = 0
            
            for row in incomplete:
                transcript_id, filename, client_name = row
                logger.info(f"Processing: {client_name} - {filename}")
                
                transcript = db.session.get(Transcript, transcript_id)
                if not transcript or not transcript.raw_content:
                    continue
                
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
                            logger.info(f"  Anthropic analysis completed ({len(analysis)} chars)")
                        
                    except Exception as e:
                        logger.error(f"  Anthropic failed: {str(e)[:100]}")
                else:
                    success_count += 1
                
                time.sleep(2)  # Rate limiting
                
                # Gemini Analysis
                if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
                    try:
                        response = gemini_model.generate_content(
                            f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}",
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=4000,
                                temperature=0.3
                            )
                        )
                        
                        analysis = response.text.strip()
                        if len(analysis) > 500:
                            transcript.gemini_analysis = analysis
                            success_count += 1
                            logger.info(f"  Gemini analysis completed ({len(analysis)} chars)")
                        
                    except Exception as e:
                        logger.error(f"  Gemini failed: {str(e)[:100]}")
                else:
                    success_count += 1
                
                # Check OpenAI analysis
                if transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000:
                    success_count += 1
                
                # Update processing status
                if success_count >= 2:  # At least 2 of 3 providers
                    transcript.processing_status = 'completed'
                    
                    # Add log entry
                    log_entry = ProcessingLog(
                        transcript_id=transcript.id,
                        status='success',
                        message=f"Completed AI analysis with {success_count}/3 providers using clinical prompts",
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    processed += 1
                
                db.session.commit()
                time.sleep(1)  # Additional rate limiting
            
            logger.info(f"Batch complete. Processed: {processed}/{len(incomplete)}")
            return processed
            
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return 0

def run_background_processor():
    """Run the background processor for multiple batches"""
    logger.info("Starting background AI processor")
    
    total_processed = 0
    batch_count = 0
    max_batches = 50  # Process up to 150 transcripts
    
    while batch_count < max_batches:
        batch_count += 1
        logger.info(f"Starting batch {batch_count}")
        
        processed = process_single_batch()
        total_processed += processed
        
        if processed == 0:
            logger.info("No more transcripts to process")
            break
        
        logger.info(f"Batch {batch_count} complete. Total processed: {total_processed}")
        time.sleep(3)  # Cool down between batches
    
    logger.info(f"Background processing complete. Total processed: {total_processed}")
    
    # Final status check
    try:
        from sqlalchemy import text
        from app import app, db
        
        with app.app_context():
            query = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN t.anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                    COUNT(CASE WHEN t.gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done
                FROM transcript t
                WHERE t.raw_content IS NOT NULL AND CHAR_LENGTH(t.raw_content) > 100
            """)
            
            result = db.session.execute(query)
            row = result.fetchone()
            
            total, anthropic_done, gemini_done = row
            
            logger.info(f"FINAL STATUS:")
            logger.info(f"Total transcripts: {total}")
            logger.info(f"Anthropic complete: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
            logger.info(f"Gemini complete: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
            
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")

if __name__ == "__main__":
    run_background_processor()