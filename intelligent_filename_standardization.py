"""
Intelligent filename standardization and comprehensive AI analysis
Standardizes filenames to "Firstname Lastname MM-DD-YYYY 2400 hrs" format using content analysis
"""
import os
import sys
import time
import re
import logging
from datetime import datetime, timezone

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript, ProcessingLog, Client
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentProcessor:
    def __init__(self):
        import openai
        import anthropic
        import google.generativeai as genai
        
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        self.processed = 0
        self.standardized = 0

    def extract_session_info_from_content(self, content):
        """Extract client name and date from transcript content using AI"""
        try:
            import openai
            
            extraction_prompt = """
            Extract the client's full name and session date from this therapy transcript. 
            Return ONLY in this exact format: "FirstName LastName|MM-DD-YYYY"
            
            If you cannot find clear information, return "UNKNOWN|UNKNOWN"
            
            Transcript excerpt (first 2000 characters):
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Use faster model for extraction
                messages=[
                    {"role": "system", "content": "You are an expert at extracting client names and dates from therapy transcripts."},
                    {"role": "user", "content": f"{extraction_prompt}\n\n{content[:2000]}"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            if "|" in result:
                name_part, date_part = result.split("|", 1)
                return name_part.strip(), date_part.strip()
            
            return None, None
            
        except Exception as e:
            logger.error(f"Content extraction failed: {str(e)[:50]}")
            return None, None

    def standardize_filename(self, transcript):
        """Standardize filename using content analysis"""
        try:
            # Check if filename is already in standard format
            standard_pattern = r'^[A-Z][a-z]+ [A-Z][a-z]+ \d{2}-\d{2}-\d{4} \d{4} hrs\.(pdf|txt|docx)$'
            if re.match(standard_pattern, transcript.original_filename):
                return transcript.original_filename
            
            # Extract info from content
            extracted_name, extracted_date = self.extract_session_info_from_content(transcript.raw_content)
            
            # Get client name from database
            client = db.session.get(Client, transcript.client_id)
            client_name = client.name if client else "Unknown Client"
            
            # Use extracted name if available, otherwise use client name
            if extracted_name and extracted_name != "UNKNOWN":
                final_name = extracted_name
            else:
                final_name = client_name
            
            # Handle date
            if extracted_date and extracted_date != "UNKNOWN":
                try:
                    # Try to parse various date formats
                    date_formats = ['%m-%d-%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
                    parsed_date = None
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(extracted_date, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_date:
                        formatted_date = parsed_date.strftime('%m-%d-%Y')
                    else:
                        formatted_date = extracted_date
                except:
                    formatted_date = extracted_date
            else:
                # Try to extract date from original filename
                date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', transcript.original_filename)
                if date_match:
                    formatted_date = date_match.group(1).replace('/', '-')
                else:
                    # Use creation date as fallback
                    formatted_date = transcript.created_at.strftime('%m-%d-%Y')
            
            # Extract time if available
            time_match = re.search(r'(\d{4}) hrs', transcript.original_filename)
            if time_match:
                session_time = time_match.group(1)
            else:
                # Try other time patterns
                time_match = re.search(r'(\d{1,2}):?(\d{2})', transcript.original_filename)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = time_match.group(2)
                    session_time = f"{hour:02d}{minute}"
                else:
                    session_time = "1200"  # Default to noon
            
            # Get file extension
            ext_match = re.search(r'\.(pdf|txt|docx)$', transcript.original_filename.lower())
            extension = ext_match.group(1) if ext_match else 'pdf'
            
            # Create standardized filename
            standardized = f"{final_name} {formatted_date} {session_time} hrs.{extension}"
            
            logger.info(f"Standardized: {transcript.original_filename} -> {standardized}")
            return standardized
            
        except Exception as e:
            logger.error(f"Filename standardization failed: {str(e)}")
            return transcript.original_filename

    def complete_ai_analysis(self, transcript):
        """Complete comprehensive AI analysis using exact clinical prompts"""
        success_count = 0
        
        # OpenAI Analysis
        if not transcript.openai_analysis or len(str(transcript.openai_analysis)) < 1000:
            try:
                import openai
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
            
            time.sleep(2)
        else:
            success_count += 1
        
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
                response = self.gemini_model.generate_content(
                    f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}",
                    generation_config=self.gemini_model._generation_config.__class__(
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
            
            time.sleep(3)
        else:
            success_count += 1
        
        return success_count

    def process_transcripts(self):
        """Process all transcripts for filename standardization and AI analysis"""
        with app.app_context():
            from sqlalchemy import text
            
            # Get all transcripts needing processing
            query = text("""
                SELECT t.id, t.original_filename, c.name as client_name
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                ORDER BY c.name, t.original_filename
                LIMIT 50
            """)
            
            result = db.session.execute(query)
            transcripts = result.fetchall()
            
            logger.info(f"Processing {len(transcripts)} transcripts")
            
            for row in transcripts:
                transcript_id, filename, client_name = row
                logger.info(f"Processing: {client_name} - {filename}")
                
                transcript = db.session.get(Transcript, transcript_id)
                if not transcript:
                    continue
                
                # Standardize filename
                new_filename = self.standardize_filename(transcript)
                if new_filename != transcript.original_filename:
                    transcript.original_filename = new_filename
                    self.standardized += 1
                
                # Complete AI analysis
                success_count = self.complete_ai_analysis(transcript)
                
                # Update processing status
                if success_count >= 3:
                    transcript.processing_status = 'completed'
                    
                    log_entry = ProcessingLog(
                        transcript_id=transcript.id,
                        status='success',
                        message=f"Completed filename standardization and comprehensive AI analysis",
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    self.processed += 1
                
                db.session.commit()
                time.sleep(1)
                
                # Process in batches
                if self.processed > 0 and self.processed % 10 == 0:
                    logger.info(f"Processed {self.processed} transcripts, taking a break...")
                    time.sleep(5)
        
        logger.info(f"Processing complete. Standardized: {self.standardized}, AI Analyzed: {self.processed}")

    def generate_status_report(self):
        """Generate comprehensive status report"""
        with app.app_context():
            from sqlalchemy import text
            
            query = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_complete,
                    COUNT(CASE WHEN anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_complete,
                    COUNT(CASE WHEN gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_complete,
                    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as status_complete
                FROM transcript 
                WHERE raw_content IS NOT NULL AND CHAR_LENGTH(raw_content) > 100
            """)
            
            result = db.session.execute(query)
            row = result.fetchone()
            
            total, openai_done, anthropic_done, gemini_done, status_complete = row
            complete_all = min(openai_done, anthropic_done, gemini_done)
            
            logger.info("=" * 60)
            logger.info("INTELLIGENT PROCESSING STATUS REPORT")
            logger.info("=" * 60)
            logger.info(f"Total transcripts: {total}")
            logger.info(f"Filenames standardized: {self.standardized}")
            logger.info(f"OpenAI complete: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
            logger.info(f"Anthropic complete: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
            logger.info(f"Gemini complete: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
            logger.info(f"All 3 providers: {complete_all}/{total} ({complete_all/total*100:.1f}%)")
            logger.info("=" * 60)

def main():
    """Main execution function"""
    processor = IntelligentProcessor()
    processor.process_transcripts()
    processor.generate_status_report()

if __name__ == "__main__":
    main()