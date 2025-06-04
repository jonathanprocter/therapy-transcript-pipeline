"""
Complete comprehensive AI analysis for Krista Flood's transcripts using exact clinical prompts
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

class KristaFloodAnalyzer:
    def __init__(self):
        # Initialize AI clients
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        print("✓ AI clients initialized")

    def complete_openai_analysis(self, transcript):
        """Complete OpenAI analysis using exact therapy prompt"""
        try:
            if transcript.openai_analysis and len(transcript.openai_analysis) > 1000:
                print(f"  OpenAI analysis already complete for {transcript.original_filename}")
                return True
                
            print(f"  Generating OpenAI analysis for {transcript.original_filename}")
            
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
                print(f"  ✓ OpenAI analysis completed ({len(analysis)} chars)")
                return True
            else:
                print(f"  ✗ OpenAI analysis too short ({len(analysis)} chars)")
                return False
                
        except Exception as e:
            print(f"  ✗ OpenAI analysis failed: {str(e)}")
            return False

    def complete_anthropic_analysis(self, transcript):
        """Complete Anthropic analysis using exact therapy prompt"""
        try:
            if transcript.anthropic_analysis and len(transcript.anthropic_analysis) > 1000:
                print(f"  Anthropic analysis already complete for {transcript.original_filename}")
                return True
                
            print(f"  Generating Anthropic analysis for {transcript.original_filename}")
            
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
                print(f"  ✓ Anthropic analysis completed ({len(analysis)} chars)")
                return True
            else:
                print(f"  ✗ Anthropic analysis too short ({len(analysis)} chars)")
                return False
                
        except Exception as e:
            print(f"  ✗ Anthropic analysis failed: {str(e)}")
            return False

    def complete_gemini_analysis(self, transcript):
        """Complete Gemini analysis using exact therapy prompt"""
        try:
            if transcript.gemini_analysis and len(transcript.gemini_analysis) > 1000:
                print(f"  Gemini analysis already complete for {transcript.original_filename}")
                return True
                
            print(f"  Generating Gemini analysis for {transcript.original_filename}")
            
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
                print(f"  ✓ Gemini analysis completed ({len(analysis)} chars)")
                return True
            else:
                print(f"  ✗ Gemini analysis too short ({len(analysis)} chars)")
                return False
                
        except Exception as e:
            print(f"  ✗ Gemini analysis failed: {str(e)}")
            return False

    def process_krista_transcripts(self):
        """Process all Krista Flood transcripts for complete AI analysis"""
        print("Starting comprehensive AI analysis for Krista Flood transcripts...")
        
        with app.app_context():
            # Get Krista Flood's client record
            client = db.session.query(Client).filter_by(name='Krista Flood').first()
            if not client:
                print("✗ Krista Flood client not found")
                return
                
            # Get all transcripts for Krista
            transcripts = db.session.query(Transcript).filter_by(client_id=client.id).all()
            print(f"Found {len(transcripts)} transcripts for Krista Flood")
            
            for transcript in transcripts:
                print(f"\nProcessing: {transcript.original_filename}")
                
                # Check if transcript has content
                if not transcript.raw_content or len(transcript.raw_content) < 100:
                    print(f"  ✗ Insufficient content ({len(transcript.raw_content or '')} chars)")
                    continue
                
                # Complete all three AI analyses
                openai_success = self.complete_openai_analysis(transcript)
                time.sleep(2)  # Rate limiting
                
                anthropic_success = self.complete_anthropic_analysis(transcript)
                time.sleep(2)  # Rate limiting
                
                gemini_success = self.complete_gemini_analysis(transcript)
                time.sleep(2)  # Rate limiting
                
                # Update processing status
                if openai_success and anthropic_success and gemini_success:
                    transcript.processing_status = 'completed'
                    db.session.commit()
                    print(f"  ✓ All AI analyses completed for {transcript.original_filename}")
                    
                    # Log completion
                    log_entry = ProcessingLog(
                        transcript_id=transcript.id,
                        status='success',
                        message=f"Completed comprehensive AI analysis with all 3 providers",
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                else:
                    print(f"  ⚠ Partial completion for {transcript.original_filename}")
            
            print("\n=== Krista Flood Analysis Summary ===")
            # Final status check
            for transcript in transcripts:
                has_openai = bool(transcript.openai_analysis and len(transcript.openai_analysis) > 1000)
                has_anthropic = bool(transcript.anthropic_analysis and len(transcript.anthropic_analysis) > 1000)
                has_gemini = bool(transcript.gemini_analysis and len(transcript.gemini_analysis) > 1000)
                providers = f"{int(has_openai) + int(has_anthropic) + int(has_gemini)}/3"
                
                print(f"{transcript.original_filename}: {providers} providers complete")

def main():
    """Main execution function"""
    analyzer = KristaFloodAnalyzer()
    analyzer.process_krista_transcripts()

if __name__ == "__main__":
    main()