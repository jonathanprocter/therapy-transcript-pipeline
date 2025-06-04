"""
Quick fix for incomplete AI analysis - focused on critical missing pieces
"""
import os
import sys
from sqlalchemy import create_engine, text
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

def complete_missing_analysis():
    """Complete missing AI analysis for transcripts"""
    print("Starting focused AI analysis completion...")
    
    # Initialize AI clients
    openai.api_key = Config.OPENAI_API_KEY
    anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    
    with app.app_context():
        # Get 5 transcripts missing Anthropic analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name 
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE (t.anthropic_analysis IS NULL OR CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) < 1000)
            AND t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            ORDER BY t.id
            LIMIT 5
        """)
        
        result = db.session.execute(query)
        incomplete = result.fetchall()
        
        print(f"Found {len(incomplete)} transcripts missing Anthropic analysis")
        
        for row in incomplete:
            transcript_id, filename, client_name = row
            print(f"Processing: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                continue
            
            try:
                # Complete Anthropic analysis
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
                    db.session.commit()
                    print(f"  ✓ Anthropic analysis completed ({len(analysis)} chars)")
                    
                    # Add log entry
                    log_entry = ProcessingLog(
                        transcript_id=transcript.id,
                        status='success',
                        message=f"Completed Anthropic analysis with clinical prompt",
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                else:
                    print(f"  ✗ Analysis too short ({len(analysis)} chars)")
                    
            except Exception as e:
                print(f"  ✗ Anthropic analysis failed: {str(e)}")
            
            time.sleep(2)  # Rate limiting
        
        # Now get 5 transcripts missing Gemini analysis
        query = text("""
            SELECT t.id, t.original_filename, c.name 
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE (t.gemini_analysis IS NULL OR CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) < 1000)
            AND t.raw_content IS NOT NULL 
            AND CHAR_LENGTH(t.raw_content) > 100
            ORDER BY t.id
            LIMIT 5
        """)
        
        result = db.session.execute(query)
        incomplete = result.fetchall()
        
        print(f"\nFound {len(incomplete)} transcripts missing Gemini analysis")
        
        for row in incomplete:
            transcript_id, filename, client_name = row
            print(f"Processing: {client_name} - {filename}")
            
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                continue
            
            try:
                # Complete Gemini analysis
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
                    db.session.commit()
                    print(f"  ✓ Gemini analysis completed ({len(analysis)} chars)")
                    
                    # Add log entry
                    log_entry = ProcessingLog(
                        transcript_id=transcript.id,
                        status='success',
                        message=f"Completed Gemini analysis with clinical prompt",
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                else:
                    print(f"  ✗ Analysis too short ({len(analysis)} chars)")
                    
            except Exception as e:
                print(f"  ✗ Gemini analysis failed: {str(e)}")
            
            time.sleep(2)  # Rate limiting
        
        # Check current status
        print("\n=== CURRENT STATUS ===")
        query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN t.openai_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.openai_analysis AS TEXT)) > 1000 THEN 1 END) as openai_done,
                COUNT(CASE WHEN t.anthropic_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.anthropic_analysis AS TEXT)) > 1000 THEN 1 END) as anthropic_done,
                COUNT(CASE WHEN t.gemini_analysis IS NOT NULL AND CHAR_LENGTH(CAST(t.gemini_analysis AS TEXT)) > 1000 THEN 1 END) as gemini_done
            FROM transcript t
            WHERE t.raw_content IS NOT NULL AND CHAR_LENGTH(t.raw_content) > 100
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        
        total, openai_done, anthropic_done, gemini_done = row
        
        print(f"Total transcripts: {total}")
        print(f"OpenAI complete: {openai_done}/{total} ({openai_done/total*100:.1f}%)")
        print(f"Anthropic complete: {anthropic_done}/{total} ({anthropic_done/total*100:.1f}%)")
        print(f"Gemini complete: {gemini_done}/{total} ({gemini_done/total*100:.1f}%)")
        
        complete_all = min(openai_done, anthropic_done, gemini_done)
        print(f"All 3 providers complete: {complete_all}/{total} ({complete_all/total*100:.1f}%)")

if __name__ == "__main__":
    complete_missing_analysis()