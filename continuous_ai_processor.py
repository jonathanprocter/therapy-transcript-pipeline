"""
Continuous AI processor that runs as a background service
Processes transcripts gradually to complete comprehensive analysis
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript, ProcessingLog
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ContinuousProcessor:
    def __init__(self):
        self.running = True
        self.processed_count = 0
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        # Initialize AI clients
        import anthropic
        import google.generativeai as genai
        
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        logger.info("Continuous AI processor initialized")

    def shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def process_single_transcript(self):
        """Process one transcript with missing analysis"""
        with app.app_context():
            from sqlalchemy import text
            
            # Get one transcript missing analysis
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
                LIMIT 1
            """)
            
            result = db.session.execute(query)
            row = result.fetchone()
            
            if not row:
                return False  # No more transcripts to process
            
            transcript_id, filename, client_name = row
            logger.info(f"Processing: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                return False
            
            success = False
            
            # Anthropic Analysis
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
                    logger.error(f"  Anthropic failed: {str(e)[:100]}")
                
                time.sleep(3)  # Rate limiting
            
            # Gemini Analysis
            if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
                try:
                    response = self.gemini_model.generate_content(
                        f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}",
                        generation_config={
                            'max_output_tokens': 4000,
                            'temperature': 0.3
                        }
                    )
                    
                    analysis = response.text.strip()
                    if len(analysis) > 500:
                        transcript.gemini_analysis = analysis
                        success = True
                        logger.info(f"  ✓ Gemini complete ({len(analysis)} chars)")
                        
                except Exception as e:
                    logger.error(f"  Gemini failed: {str(e)[:100]}")
                
                time.sleep(3)  # Rate limiting
            
            # Update status if all analyses are complete
            openai_complete = transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000
            anthropic_complete = transcript.anthropic_analysis and len(str(transcript.anthropic_analysis)) > 1000
            gemini_complete = transcript.gemini_analysis and len(str(transcript.gemini_analysis)) > 1000
            
            if openai_complete and anthropic_complete and gemini_complete:
                transcript.processing_status = 'completed'
                
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    status='success',
                    message=f"Completed comprehensive AI analysis with all 3 providers",
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
            
            db.session.commit()
            
            if success:
                self.processed_count += 1
            
            return True

    def run_continuous_processing(self):
        """Run continuous processing loop"""
        logger.info("Starting continuous AI processing...")
        
        while self.running:
            try:
                # Process one transcript
                has_more = self.process_single_transcript()
                
                if not has_more:
                    logger.info("No more transcripts to process, waiting...")
                    time.sleep(60)  # Wait 1 minute before checking again
                else:
                    # Brief pause between transcripts
                    time.sleep(10)
                
                # Status update every 5 transcripts
                if self.processed_count > 0 and self.processed_count % 5 == 0:
                    self.log_status()
                
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                time.sleep(30)  # Wait 30 seconds on error
        
        logger.info(f"Continuous processor stopped. Total processed: {self.processed_count}")

    def log_status(self):
        """Log current processing status"""
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
            
            logger.info(f"STATUS UPDATE: Anthropic {anthropic_done}/{total}, Gemini {gemini_done}/{total}, Processed this session: {self.processed_count}")

def main():
    """Main execution function"""
    processor = ContinuousProcessor()
    processor.run_continuous_processing()

if __name__ == "__main__":
    main()