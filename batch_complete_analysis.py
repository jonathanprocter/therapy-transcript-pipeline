"""
Batch complete AI analysis for all clients - optimized for efficiency
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

class BatchAnalyzer:
    def __init__(self):
        import openai
        import anthropic
        import google.generativeai as genai
        
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        self.processed = 0
        self.errors = 0

    def get_incomplete_transcripts(self, limit=10):
        """Get transcripts missing AI analysis"""
        with app.app_context():
            from sqlalchemy import text
            
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
                LIMIT :limit
            """)
            
            result = db.session.execute(query, {"limit": limit})
            return result.fetchall()

    def complete_analysis_for_transcript(self, transcript_id):
        """Complete missing analysis for a single transcript"""
        with app.app_context():
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript or not transcript.raw_content:
                return False

            success = False
            
            # Complete Anthropic analysis if missing
            if not transcript.anthropic_analysis or len(str(transcript.anthropic_analysis)) < 1000:
                try:
                    response = self.anthropic_client.messages.create(
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
                        success = True
                        logger.info(f"  ✓ Anthropic complete ({len(analysis)} chars)")
                        
                except Exception as e:
                    logger.error(f"  Anthropic failed: {str(e)[:50]}")
                
                time.sleep(2)  # Rate limiting
            
            # Complete Gemini analysis if missing
            if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
                try:
                    import google.generativeai as genai
                    
                    response = self.gemini_model.generate_content(
                        f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}",
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=4000,
                            temperature=0.3
                        )
                    )
                    
                    analysis = response.text.strip()
                    if len(analysis) > 500:
                        transcript.gemini_analysis = analysis
                        success = True
                        logger.info(f"  ✓ Gemini complete ({len(analysis)} chars)")
                        
                except Exception as e:
                    logger.error(f"  Gemini failed: {str(e)[:50]}")
                
                time.sleep(2)  # Rate limiting
            
            # Update processing status if successful
            if success:
                # Check if all three analyses are now complete
                openai_complete = transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000
                anthropic_complete = transcript.anthropic_analysis and len(str(transcript.anthropic_analysis)) > 1000
                gemini_complete = transcript.gemini_analysis and len(str(transcript.gemini_analysis)) > 1000
                
                if openai_complete and anthropic_complete and gemini_complete:
                    transcript.processing_status = 'completed'
                
                # Add success log
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    status='success', 
                    message=f"Completed AI analysis using clinical prompts",
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
                
            db.session.commit()
            return success

    def run_batch_processing(self):
        """Run batch processing in manageable chunks"""
        logger.info("Starting batch AI analysis completion")
        
        batch_size = 5  # Process 5 transcripts at a time
        max_batches = 30  # Process up to 150 transcripts total
        
        for batch_num in range(1, max_batches + 1):
            logger.info(f"Processing batch {batch_num}")
            
            # Get incomplete transcripts
            incomplete = self.get_incomplete_transcripts(batch_size)
            if not incomplete:
                logger.info("No more transcripts need processing")
                break
            
            batch_processed = 0
            for row in incomplete:
                transcript_id, filename, client_name = row
                logger.info(f"Processing: {client_name} - {filename}")
                
                if self.complete_analysis_for_transcript(transcript_id):
                    batch_processed += 1
                    self.processed += 1
                else:
                    self.errors += 1
                
                time.sleep(1)  # Brief pause between transcripts
            
            logger.info(f"Batch {batch_num} complete: {batch_processed}/{len(incomplete)} successful")
            
            # Longer pause between batches
            time.sleep(3)
        
        logger.info(f"Batch processing complete. Total processed: {self.processed}, Errors: {self.errors}")

    def generate_status_report(self):
        """Generate final status report"""
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
            
            logger.info("="*50)
            logger.info("COMPREHENSIVE AI ANALYSIS STATUS REPORT")
            logger.info("="*50)
            logger.info(f"Total transcripts: {total}")
            logger.info(f"OpenAI complete: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
            logger.info(f"Anthropic complete: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
            logger.info(f"Gemini complete: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
            logger.info(f"Status 'completed': {status_complete}/{total} ({status_complete/total*100:.1f}%)")
            logger.info("="*50)

def main():
    """Main execution function"""
    analyzer = BatchAnalyzer()
    analyzer.run_batch_processing()
    analyzer.generate_status_report()

if __name__ == "__main__":
    main()