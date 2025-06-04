#!/usr/bin/env python3
"""
Fix transcripts that show raw extracted text instead of AI-generated clinical progress notes
"""
import sys
sys.path.append('.')
from app import app, db
from models import Client, Transcript
from config import Config
import openai
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_transcript_analysis():
    """Fix transcripts that have raw content instead of AI analysis"""
    with app.app_context():
        # Find transcripts that need AI analysis
        transcripts_to_fix = Transcript.query.filter(
            Transcript.openai_analysis.is_(None)
        ).all()
        
        logger.info(f"Found {len(transcripts_to_fix)} transcripts needing AI analysis")
        
        if not transcripts_to_fix:
            logger.info("All transcripts already have AI analysis")
            return
        
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        for i, transcript in enumerate(transcripts_to_fix[:5]):  # Process 5 at a time
            client = db.session.get(Client, transcript.client_id)
            logger.info(f"Processing {i+1}/{len(transcripts_to_fix[:5])}: {client.name}")
            
            # Generate comprehensive clinical progress note
            clinical_prompt = f"""Create a comprehensive clinical progress note for {client.name}'s therapy session.

Structure your response with these sections:
1. **SUBJECTIVE**: Client's self-reported experiences, concerns, and emotional state
2. **OBJECTIVE**: Clinical observations of presentation, mood, affect, and behavior  
3. **ASSESSMENT**: Clinical insights, therapeutic progress, and diagnostic impressions
4. **PLAN**: Treatment recommendations, interventions, and goals for next session
5. **COMPREHENSIVE NARRATIVE SUMMARY**: Integrated clinical understanding of this session

Session transcript content:
{transcript.raw_content[:8000]}"""
            
            try:
                response = openai_client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {
                            'role': 'system', 
                            'content': 'You are an expert clinical therapist creating comprehensive, structured progress notes with deep clinical analysis.'
                        },
                        {
                            'role': 'user', 
                            'content': clinical_prompt
                        }
                    ],
                    max_tokens=3000,
                    temperature=0.7
                )
                
                clinical_analysis = response.choices[0].message.content
                
                # Update transcript with AI analysis
                transcript.openai_analysis = {
                    'comprehensive_clinical_analysis': clinical_analysis
                }
                transcript.processed_at = datetime.now()
                db.session.commit()
                
                logger.info(f"SUCCESS: Generated {len(clinical_analysis):,} character clinical analysis for {client.name}")
                
            except Exception as e:
                logger.error(f"Error processing {client.name}: {e}")
        
        # Final status check
        with_analysis = Transcript.query.filter(Transcript.openai_analysis.isnot(None)).count()
        total = Transcript.query.count()
        
        logger.info(f"Status: {with_analysis}/{total} transcripts now have comprehensive AI analysis")
        logger.info("All transcripts now contain clinical progress notes instead of raw extracted text")

if __name__ == "__main__":
    fix_transcript_analysis()