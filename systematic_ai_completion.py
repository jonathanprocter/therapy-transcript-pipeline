"""
Systematic AI completion for all transcripts using exact clinical prompts
Processes transcripts methodically with proper error handling and progress tracking
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.append('/home/runner/workspace')

from app import app, db
from models import Client, Transcript, ProcessingLog
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SystematicAIProcessor:
    def __init__(self):
        # Initialize AI clients
        import openai
        import anthropic
        import google.generativeai as genai
        
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        self.processed = 0
        self.errors = 0
        
        logger.info("AI clients initialized for systematic processing")

    def process_missing_anthropic(self, limit=20):
        """Process transcripts missing Anthropic analysis"""
        logger.info(f"Processing {limit} transcripts missing Anthropic analysis")
        
        with app.app_context():
            from sqlalchemy import text
            
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name, 
                       CHAR_LENGTH(t.raw_content) as content_length
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
                AND t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                ORDER BY t.id
                LIMIT :limit
            """)
            
            result = db.session.execute(query, {"limit": limit})
            transcripts = result.fetchall()
            
            for row in transcripts:
                transcript_id, filename, client_name, content_length = row
                logger.info(f"Processing Anthropic: {client_name} - {filename} ({content_length} chars)")
                
                transcript = db.session.get(Transcript, transcript_id)
                if not transcript:
                    continue
                
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
                        db.session.commit()
                        self.processed += 1
                        logger.info(f"  ✓ Anthropic complete ({len(analysis)} chars)")
                        
                        # Add success log
                        log_entry = ProcessingLog(
                            transcript_id=transcript.id,
                            status='success',
                            message=f"Completed Anthropic analysis using clinical prompt",
                            created_at=datetime.now(timezone.utc)
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                    else:
                        logger.warning(f"  Short analysis: {len(analysis)} chars")
                        self.errors += 1
                        
                except Exception as e:
                    logger.error(f"  Anthropic failed: {str(e)[:100]}")
                    self.errors += 1
                
                time.sleep(3)  # Rate limiting

    def process_missing_gemini(self, limit=20):
        """Process transcripts missing Gemini analysis"""
        logger.info(f"Processing {limit} transcripts missing Gemini analysis")
        
        with app.app_context():
            from sqlalchemy import text
            
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name,
                       CHAR_LENGTH(t.raw_content) as content_length
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE (t.gemini_analysis IS NULL OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000)
                AND t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                ORDER BY t.id
                LIMIT :limit
            """)
            
            result = db.session.execute(query, {"limit": limit})
            transcripts = result.fetchall()
            
            for row in transcripts:
                transcript_id, filename, client_name, content_length = row
                logger.info(f"Processing Gemini: {client_name} - {filename} ({content_length} chars)")
                
                transcript = db.session.get(Transcript, transcript_id)
                if not transcript:
                    continue
                
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
                        db.session.commit()
                        self.processed += 1
                        logger.info(f"  ✓ Gemini complete ({len(analysis)} chars)")
                        
                        # Add success log
                        log_entry = ProcessingLog(
                            transcript_id=transcript.id,
                            status='success',
                            message=f"Completed Gemini analysis using clinical prompt",
                            created_at=datetime.now(timezone.utc)
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                    else:
                        logger.warning(f"  Short analysis: {len(analysis)} chars")
                        self.errors += 1
                        
                except Exception as e:
                    logger.error(f"  Gemini failed: {str(e)[:100]}")
                    self.errors += 1
                
                time.sleep(3)  # Rate limiting

    def complete_missing_openai(self, limit=20):
        """Complete missing OpenAI analysis"""
        logger.info(f"Processing {limit} transcripts missing OpenAI analysis")
        
        with app.app_context():
            from sqlalchemy import text
            import openai
            
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name,
                       CHAR_LENGTH(t.raw_content) as content_length
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE (t.openai_analysis IS NULL OR CHAR_LENGTH(CAST(t.openai_analysis AS TEXT)) < 1000)
                AND t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                ORDER BY t.id
                LIMIT :limit
            """)
            
            result = db.session.execute(query, {"limit": limit})
            transcripts = result.fetchall()
            
            for row in transcripts:
                transcript_id, filename, client_name, content_length = row
                logger.info(f"Processing OpenAI: {client_name} - {filename} ({content_length} chars)")
                
                transcript = db.session.get(Transcript, transcript_id)
                if not transcript:
                    continue
                
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
                        db.session.commit()
                        self.processed += 1
                        logger.info(f"  ✓ OpenAI complete ({len(analysis)} chars)")
                        
                        # Add success log
                        log_entry = ProcessingLog(
                            transcript_id=transcript.id,
                            status='success',
                            message=f"Completed OpenAI analysis using clinical prompt",
                            created_at=datetime.now(timezone.utc)
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                    else:
                        logger.warning(f"  Short analysis: {len(analysis)} chars")
                        self.errors += 1
                        
                except Exception as e:
                    logger.error(f"  OpenAI failed: {str(e)[:100]}")
                    self.errors += 1
                
                time.sleep(2)  # Rate limiting

    def update_processing_status(self):
        """Update processing status for completed transcripts"""
        with app.app_context():
            from sqlalchemy import text
            
            # Update status for transcripts with all 3 analyses
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
            
            logger.info(f"Updated processing status for {updated} transcripts")

    def get_completion_status(self):
        """Get current completion status"""
        with app.app_context():
            from sqlalchemy import text
            
            query = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_done,
                    COUNT(CASE WHEN anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                    COUNT(CASE WHEN gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done
                FROM transcript 
                WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
            """)
            
            result = db.session.execute(query)
            row = result.fetchone()
            
            total, openai_done, anthropic_done, gemini_done = row
            complete_all = min(openai_done, anthropic_done, gemini_done)
            
            logger.info(f"COMPLETION STATUS:")
            logger.info(f"Total transcripts: {total}")
            logger.info(f"OpenAI: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
            logger.info(f"Anthropic: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
            logger.info(f"Gemini: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
            logger.info(f"All 3 complete: {complete_all}/{total} ({complete_all/total*100:.1f}%)")
            
            return {
                'total': total,
                'openai_done': openai_done,
                'anthropic_done': anthropic_done,
                'gemini_done': gemini_done,
                'complete_all': complete_all
            }

    def run_systematic_processing(self):
        """Run systematic processing in manageable phases"""
        logger.info("Starting systematic AI processing")
        
        # Phase 1: Complete missing OpenAI analysis
        self.complete_missing_openai(15)
        
        # Phase 2: Process Anthropic analysis
        self.process_missing_anthropic(15)
        
        # Phase 3: Process Gemini analysis  
        self.process_missing_gemini(15)
        
        # Phase 4: Update processing status
        self.update_processing_status()
        
        # Phase 5: Final status report
        status = self.get_completion_status()
        
        logger.info(f"Processing session complete")
        logger.info(f"Successfully processed: {self.processed}")
        logger.info(f"Errors encountered: {self.errors}")
        
        return status

def main():
    """Main execution function"""
    processor = SystematicAIProcessor()
    processor.run_systematic_processing()

if __name__ == "__main__":
    main()