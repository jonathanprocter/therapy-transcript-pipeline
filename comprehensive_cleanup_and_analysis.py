"""
Comprehensive cleanup of duplicates and complete AI analysis for all transcripts
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

def remove_all_duplicates():
    """Remove all duplicate transcripts keeping the first occurrence"""
    with app.app_context():
        from sqlalchemy import text
        
        # Get all duplicates
        query = text("""
            SELECT t.original_filename, 
                   ARRAY_AGG(t.id ORDER BY t.id) as transcript_ids
            FROM transcript t
            GROUP BY t.original_filename
            HAVING COUNT(*) > 1
        """)
        
        result = db.session.execute(query)
        duplicates = result.fetchall()
        
        total_removed = 0
        
        for row in duplicates:
            filename, transcript_ids = row
            # Keep the first ID, remove the rest
            ids_to_remove = transcript_ids[1:]  # Skip first element
            
            logger.info(f"Removing {len(ids_to_remove)} duplicates for: {filename}")
            
            for transcript_id in ids_to_remove:
                transcript = db.session.get(Transcript, transcript_id)
                if transcript:
                    db.session.delete(transcript)
                    total_removed += 1
            
            db.session.commit()
        
        logger.info(f"Removed {total_removed} duplicate transcripts")
        return total_removed

def complete_ai_analysis():
    """Complete AI analysis for all transcripts using exact clinical prompts"""
    import openai
    import anthropic
    import google.generativeai as genai
    
    # Initialize AI clients
    openai.api_key = Config.OPENAI_API_KEY
    anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    
    processed = 0
    errors = 0
    
    with app.app_context():
        from sqlalchemy import text
        
        # Get transcripts missing analysis
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
                OR
                (t.openai_analysis IS NULL OR CHAR_LENGTH(CAST(t.openai_analysis AS TEXT)) < 1000)
            )
            ORDER BY t.id
        """)
        
        result = db.session.execute(query)
        incomplete_transcripts = result.fetchall()
        
        logger.info(f"Processing {len(incomplete_transcripts)} transcripts needing AI analysis")
        
        for row in incomplete_transcripts:
            transcript_id, filename, client_name = row
            logger.info(f"Processing: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript or not transcript.raw_content:
                continue
            
            success_count = 0
            
            # OpenAI Analysis
            if not transcript.openai_analysis or len(str(transcript.openai_analysis)) < 1000:
                try:
                    response = openai.chat.completions.create(
                        model=Config.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an expert clinical therapist creating comprehensive clinical progress notes."},
                            {"role": "user", "content": f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}"}
                        ],
                        max_tokens=4000,
                        temperature=0.3
                    )
                    
                    analysis = response.choices[0].message.content.strip()
                    if len(analysis) > 500:
                        transcript.openai_analysis = analysis
                        success_count += 1
                        logger.info(f"  ✓ OpenAI complete ({len(analysis)} chars)")
                        
                except Exception as e:
                    logger.error(f"  OpenAI failed: {str(e)[:50]}")
                    errors += 1
                
                time.sleep(2)
            else:
                success_count += 1
            
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
                    errors += 1
                
                time.sleep(3)
            else:
                success_count += 1
            
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
                        logger.info(f"  ✓ Gemini complete ({len(analysis)} chars)")
                        
                except Exception as e:
                    logger.error(f"  Gemini failed: {str(e)[:50]}")
                    errors += 1
                
                time.sleep(3)
            else:
                success_count += 1
            
            # Update processing status
            if success_count >= 3:  # All 3 providers complete
                transcript.processing_status = 'completed'
                
                # Add success log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    status='success',
                    message=f"Completed comprehensive AI analysis with all 3 providers using clinical prompts",
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                processed += 1
            
            db.session.commit()
            
            # Rate limiting between transcripts
            time.sleep(2)
            
            # Process in batches of 10
            if processed > 0 and processed % 10 == 0:
                logger.info(f"Processed {processed} transcripts so far, taking a break...")
                time.sleep(10)
        
        logger.info(f"AI analysis complete. Processed: {processed}, Errors: {errors}")

def generate_final_report():
    """Generate comprehensive final status report"""
    with app.app_context():
        from sqlalchemy import text
        
        # Overall stats
        query = text("""
            SELECT 
                COUNT(*) as total_transcripts,
                COUNT(DISTINCT client_id) as total_clients,
                COUNT(CASE WHEN openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_complete,
                COUNT(CASE WHEN anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_complete,
                COUNT(CASE WHEN gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_complete,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as status_complete
            FROM transcript 
            WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        
        total, clients, openai_done, anthropic_done, gemini_done, status_complete = row
        complete_all = min(openai_done, anthropic_done, gemini_done)
        
        logger.info("=" * 60)
        logger.info("COMPREHENSIVE THERAPY TRANSCRIPT SYSTEM STATUS REPORT")
        logger.info("=" * 60)
        logger.info(f"Total clients: {clients}")
        logger.info(f"Total transcripts: {total}")
        logger.info("-" * 40)
        logger.info("AI ANALYSIS COMPLETION:")
        logger.info(f"OpenAI analysis: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
        logger.info(f"Anthropic analysis: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
        logger.info(f"Gemini analysis: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
        logger.info(f"All 3 providers complete: {complete_all}/{total} ({complete_all/total*100:.1f}%)")
        logger.info(f"Processing status 'completed': {status_complete}/{total} ({status_complete/total*100:.1f}%)")
        logger.info("=" * 60)
        
        if complete_all == total:
            logger.info("🎉 ALL TRANSCRIPTS HAVE COMPREHENSIVE AI ANALYSIS!")
            logger.info("System is ready for deployment with complete clinical insights.")
        else:
            logger.info(f"Still need to complete {total - complete_all} transcripts")
        
        logger.info("=" * 60)

def main():
    """Main execution function"""
    logger.info("Starting comprehensive cleanup and AI analysis")
    
    # Step 1: Remove duplicates
    logger.info("Step 1: Removing duplicate transcripts")
    removed = remove_all_duplicates()
    
    # Step 2: Complete AI analysis
    logger.info("Step 2: Completing comprehensive AI analysis")
    complete_ai_analysis()
    
    # Step 3: Generate final report
    logger.info("Step 3: Generating final status report")
    generate_final_report()
    
    logger.info("Comprehensive cleanup and analysis complete!")

if __name__ == "__main__":
    main()