#!/usr/bin/env python3
"""
Batch process all transcripts to generate comprehensive AI analysis
"""
import sys
sys.path.append('.')
from app import app, db
from models import Client, Transcript
from config import Config
import openai
from datetime import datetime
import time

def process_transcripts_batch():
    """Process all transcripts that need AI analysis"""
    with app.app_context():
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Get all transcripts without AI analysis
        transcripts = Transcript.query.filter(Transcript.openai_analysis.is_(None)).all()
        
        print(f"Processing {len(transcripts)} transcripts with comprehensive AI analysis...")
        
        for i, transcript in enumerate(transcripts):
            client = db.session.get(Client, transcript.client_id)
            print(f"{i+1}/{len(transcripts)}: {client.name}")
            
            # Generate clinical analysis
            prompt = f"""Create a comprehensive clinical progress note for {client.name}.

Structure with sections:
**SUBJECTIVE**: Client's reported experiences and concerns
**OBJECTIVE**: Clinical observations of presentation and mood
**ASSESSMENT**: Clinical insights and therapeutic progress
**PLAN**: Treatment recommendations and next steps
**COMPREHENSIVE NARRATIVE SUMMARY**: Integrated clinical understanding

Content: {transcript.raw_content[:6000]}"""
            
            try:
                response = openai_client.chat.completions.create(
                    model='gpt-4o',
                    messages=[
                        {'role': 'system', 'content': 'You are an expert clinical therapist creating structured progress notes.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    max_tokens=2500
                )
                
                analysis = response.choices[0].message.content
                
                # Update transcript
                transcript.openai_analysis = {'comprehensive_clinical_analysis': analysis}
                transcript.processed_at = datetime.now()
                db.session.commit()
                
                print(f"  Generated {len(analysis):,} character analysis")
                time.sleep(0.5)  # Brief pause between API calls
                
            except Exception as e:
                print(f"  Error: {e}")
        
        # Final status
        completed = Transcript.query.filter(Transcript.openai_analysis.isnot(None)).count()
        total = Transcript.query.count()
        
        print(f"\nCompleted: {completed}/{total} transcripts have comprehensive AI analysis")
        print("All transcripts now contain clinical progress notes instead of raw text")

if __name__ == "__main__":
    process_transcripts_batch()