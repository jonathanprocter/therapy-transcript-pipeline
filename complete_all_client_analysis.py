"""
Complete comprehensive AI analysis for ALL clients using exact clinical prompts
Fix duplicates and ensure all transcripts have complete 3-provider analysis
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
import json

# Add the project root to Python path
sys.path.append('/home/runner/workspace')

from app import app, db
from models import Client, Transcript, ProcessingLog
from config import Config

class ComprehensiveAnalyzer:
    def __init__(self):
        # Initialize AI clients
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        self.processed_count = 0
        self.error_count = 0
        
        print("✓ AI clients initialized for comprehensive analysis")

    def find_duplicate_transcripts(self):
        """Find and remove duplicate transcripts across all clients"""
        print("\n=== DUPLICATE DETECTION ===")
        
        with app.app_context():
            # Find duplicates by filename and client
            duplicates_query = text("""
                SELECT client_id, original_filename, array_agg(id ORDER BY id) as transcript_ids
                FROM transcript 
                GROUP BY client_id, original_filename 
                HAVING COUNT(*) > 1
                ORDER BY client_id, original_filename
            """)
            
            result = db.session.execute(duplicates_query)
            duplicates = result.fetchall()
            
            total_removed = 0
            for row in duplicates:
                client_id, filename, transcript_ids = row
                transcript_ids = transcript_ids[1:]  # Keep first, remove rest
                
                if transcript_ids:
                    print(f"Removing {len(transcript_ids)} duplicates for {filename}")
                    
                    # Remove processing logs first
                    db.session.execute(text(
                        "DELETE FROM processing_log WHERE transcript_id = ANY(:ids)"
                    ), {"ids": transcript_ids})
                    
                    # Remove duplicate transcripts
                    db.session.execute(text(
                        "DELETE FROM transcript WHERE id = ANY(:ids)"
                    ), {"ids": transcript_ids})
                    
                    total_removed += len(transcript_ids)
            
            db.session.commit()
            print(f"✓ Removed {total_removed} duplicate transcripts")

    def complete_openai_analysis(self, transcript):
        """Complete OpenAI analysis using exact therapy prompt"""
        try:
            if transcript.openai_analysis and len(str(transcript.openai_analysis)) > 1000:
                return True
                
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
                return True
            return False
                
        except Exception as e:
            print(f"    OpenAI error: {str(e)[:100]}")
            return False

    def complete_anthropic_analysis(self, transcript):
        """Complete Anthropic analysis using exact therapy prompt"""
        try:
            if transcript.anthropic_analysis and len(str(transcript.anthropic_analysis)) > 1000:
                return True
                
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
                return True
            return False
                
        except Exception as e:
            print(f"    Anthropic error: {str(e)[:100]}")
            return False

    def complete_gemini_analysis(self, transcript):
        """Complete Gemini analysis using exact therapy prompt"""
        try:
            if transcript.gemini_analysis and len(str(transcript.gemini_analysis)) > 1000:
                return True
                
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
                return True
            return False
                
        except Exception as e:
            print(f"    Gemini error: {str(e)[:100]}")
            return False

    def process_all_clients(self):
        """Process ALL clients for complete AI analysis"""
        print("\n=== COMPREHENSIVE AI ANALYSIS FOR ALL CLIENTS ===")
        
        with app.app_context():
            # Get all clients with transcripts
            clients = db.session.query(Client).join(Transcript).distinct().all()
            print(f"Found {len(clients)} clients with transcripts")
            
            for client_idx, client in enumerate(clients, 1):
                print(f"\n[{client_idx}/{len(clients)}] Processing: {client.name}")
                
                # Get all transcripts for this client
                transcripts = db.session.query(Transcript).filter_by(client_id=client.id).all()
                
                for transcript_idx, transcript in enumerate(transcripts, 1):
                    print(f"  [{transcript_idx}/{len(transcripts)}] {transcript.original_filename}")
                    
                    # Check if transcript has sufficient content
                    if not transcript.raw_content or len(transcript.raw_content) < 100:
                        print(f"    ✗ Insufficient content ({len(transcript.raw_content or '')} chars)")
                        continue
                    
                    # Complete all three AI analyses
                    openai_success = self.complete_openai_analysis(transcript)
                    time.sleep(1)  # Rate limiting
                    
                    anthropic_success = self.complete_anthropic_analysis(transcript)
                    time.sleep(1)  # Rate limiting
                    
                    gemini_success = self.complete_gemini_analysis(transcript)
                    time.sleep(1)  # Rate limiting
                    
                    # Commit changes for this transcript
                    try:
                        db.session.commit()
                        
                        # Update processing status
                        if openai_success and anthropic_success and gemini_success:
                            transcript.processing_status = 'completed'
                            
                            # Log completion
                            log_entry = ProcessingLog(
                                transcript_id=transcript.id,
                                status='success',
                                message=f"Completed comprehensive AI analysis with all 3 providers",
                                created_at=datetime.now(timezone.utc)
                            )
                            db.session.add(log_entry)
                            
                            providers = "3/3"
                            self.processed_count += 1
                        else:
                            providers = f"{int(openai_success) + int(anthropic_success) + int(gemini_success)}/3"
                            self.error_count += 1
                        
                        db.session.commit()
                        print(f"    ✓ Analysis complete: {providers} providers")
                        
                    except Exception as e:
                        print(f"    ✗ Database error: {str(e)}")
                        db.session.rollback()
                        self.error_count += 1

    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE ANALYSIS COMPLETION REPORT")
        print("="*80)
        
        with app.app_context():
            # Get updated statistics for all clients
            clients = db.session.query(Client).join(Transcript).distinct().all()
            
            print(f"Total Clients Processed: {len(clients)}")
            print(f"Transcripts Successfully Processed: {self.processed_count}")
            print(f"Transcripts with Errors: {self.error_count}")
            print("")
            
            # Detailed breakdown by client
            print("CLIENT ANALYSIS BREAKDOWN:")
            print("-" * 50)
            
            for client in clients:
                transcripts = db.session.query(Transcript).filter_by(client_id=client.id).all()
                
                openai_complete = sum(1 for t in transcripts if t.openai_analysis and len(str(t.openai_analysis)) > 1000)
                anthropic_complete = sum(1 for t in transcripts if t.anthropic_analysis and len(str(t.anthropic_analysis)) > 1000)
                gemini_complete = sum(1 for t in transcripts if t.gemini_analysis and len(str(t.gemini_analysis)) > 1000)
                
                total = len(transcripts)
                complete_all = min(openai_complete, anthropic_complete, gemini_complete)
                
                status = "✓ COMPLETE" if complete_all == total else f"⚠ PARTIAL ({complete_all}/{total})"
                
                print(f"{client.name:30} | {total:2} sessions | OpenAI:{openai_complete:2}/{total} | Anthropic:{anthropic_complete:2}/{total} | Gemini:{gemini_complete:2}/{total} | {status}")

def main():
    """Main execution function"""
    print("COMPREHENSIVE THERAPY TRANSCRIPT ANALYSIS SYSTEM")
    print("=" * 60)
    
    analyzer = ComprehensiveAnalyzer()
    
    # Step 1: Remove duplicates
    analyzer.find_duplicate_transcripts()
    
    # Step 2: Complete all AI analysis
    analyzer.process_all_clients()
    
    # Step 3: Generate final report
    analyzer.generate_final_report()
    
    print("\n✓ Comprehensive analysis completed for all clients")

if __name__ == "__main__":
    main()