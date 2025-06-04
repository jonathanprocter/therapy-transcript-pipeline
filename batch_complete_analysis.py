"""
Batch complete AI analysis for all clients - optimized for efficiency
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import openai
import anthropic
import google.generativeai as genai
from datetime import datetime, timezone
import time

# Add the project root to Python path
sys.path.append('/home/runner/workspace')

from app import app, db
from models import Client, Transcript, ProcessingLog
from config import Config

class BatchAnalyzer:
    def __init__(self):
        # Initialize AI clients
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        print("AI clients initialized")

    def get_incomplete_transcripts(self, limit=10):
        """Get transcripts missing AI analysis"""
        with app.app_context():
            query = text("""
                SELECT t.id, t.client_id, t.original_filename, c.name as client_name
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
                   OR (t.gemini_analysis IS NULL OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000)
                   OR (t.openai_analysis IS NULL OR CHAR_LENGTH(CAST(t.openai_analysis AS TEXT)) < 1000)
                AND t.raw_content IS NOT NULL 
                AND CHAR_LENGTH(t.raw_content) > 100
                ORDER BY t.client_id, t.id
                LIMIT :limit
            """)
            
            result = db.session.execute(query, {"limit": limit})
            return result.fetchall()

    def complete_analysis_for_transcript(self, transcript_id):
        """Complete missing analysis for a single transcript"""
        with app.app_context():
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                return False
            
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
                        print(f"  ✓ OpenAI complete")
                except Exception as e:
                    print(f"  ✗ OpenAI failed: {str(e)[:50]}")
            else:
                success_count += 1
            
            time.sleep(1)
            
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
                        print(f"  ✓ Anthropic complete")
                except Exception as e:
                    print(f"  ✗ Anthropic failed: {str(e)[:50]}")
            else:
                success_count += 1
            
            time.sleep(1)
            
            # Gemini Analysis
            if not transcript.gemini_analysis or len(str(transcript.gemini_analysis)) < 1000:
                try:
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
                        success_count += 1
                        print(f"  ✓ Gemini complete")
                except Exception as e:
                    print(f"  ✗ Gemini failed: {str(e)[:50]}")
            else:
                success_count += 1
            
            # Update status if all complete
            if success_count == 3:
                transcript.processing_status = 'completed'
                
                # Add log entry
                log_entry = ProcessingLog(
                    transcript_id=transcript.id,
                    status='success',
                    message=f"Completed comprehensive AI analysis with all 3 providers",
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(log_entry)
            
            db.session.commit()
            return success_count == 3

    def run_batch_processing(self):
        """Run batch processing in manageable chunks"""
        print("Starting batch AI analysis processing...")
        
        total_processed = 0
        batch_num = 1
        
        while True:
            print(f"\n--- Batch {batch_num} ---")
            
            # Get next batch of incomplete transcripts
            incomplete = self.get_incomplete_transcripts(10)
            
            if not incomplete:
                print("No more incomplete transcripts found")
                break
            
            print(f"Processing {len(incomplete)} transcripts...")
            
            for row in incomplete:
                transcript_id, client_id, filename, client_name = row
                print(f"Processing: {client_name} - {filename}")
                
                success = self.complete_analysis_for_transcript(transcript_id)
                if success:
                    print(f"  ✓ All providers complete")
                    total_processed += 1
                else:
                    print(f"  ⚠ Partial completion")
                
                time.sleep(2)  # Rate limiting
            
            batch_num += 1
            
            # Safety limit
            if batch_num > 20:
                print("Reached batch limit - stopping")
                break
        
        print(f"\nBatch processing complete. Total fully processed: {total_processed}")
        
        # Final status report
        self.generate_status_report()

    def generate_status_report(self):
        """Generate final status report"""
        print("\n" + "="*60)
        print("FINAL STATUS REPORT")
        print("="*60)
        
        with app.app_context():
            query = text("""
                SELECT 
                    c.name,
                    COUNT(t.id) as total,
                    COUNT(CASE WHEN t.openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_done,
                    COUNT(CASE WHEN t.anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                    COUNT(CASE WHEN t.gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done
                FROM client c 
                LEFT JOIN transcript t ON c.id = t.client_id 
                WHERE t.id IS NOT NULL
                GROUP BY c.id, c.name 
                ORDER BY c.name
            """)
            
            result = db.session.execute(query)
            
            complete_clients = 0
            total_clients = 0
            
            for row in result:
                name, total, openai_done, anthropic_done, gemini_done = row
                total_clients += 1
                
                all_complete = (openai_done == total and anthropic_done == total and gemini_done == total)
                if all_complete:
                    complete_clients += 1
                    status = "✓ COMPLETE"
                else:
                    status = f"⚠ PARTIAL (O:{openai_done}/{total} A:{anthropic_done}/{total} G:{gemini_done}/{total})"
                
                print(f"{name:30} | {total:2} sessions | {status}")
            
            print(f"\nSUMMARY: {complete_clients}/{total_clients} clients fully complete")

def main():
    """Main execution function"""
    analyzer = BatchAnalyzer()
    analyzer.run_batch_processing()

if __name__ == "__main__":
    main()