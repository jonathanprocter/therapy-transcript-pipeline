#!/usr/bin/env python3
"""
Quick AI completion for remaining analyses
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Transcript
import anthropic
import google.generativeai as genai
from config import Config

def process_one_anthropic():
    """Process one Anthropic analysis"""
    with app.app_context():
        # Get one transcript missing Anthropic analysis
        transcript = db.session.query(Transcript).filter(
            Transcript.anthropic_analysis.is_(None)
        ).first()
        
        if not transcript:
            print("No transcripts need Anthropic analysis")
            return False
            
        try:
            print(f"Processing Anthropic: {transcript.original_filename}")
            
            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            
            # Create prompt
            prompt = f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}"
            
            # Make API call
            response = client.messages.create(
                model=Config.ANTHROPIC_MODEL,
                max_tokens=8192,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Save result
            result = {
                'clinical_progress_note': response.content[0].text,
                'provider': 'anthropic',
                'model': Config.ANTHROPIC_MODEL,
                'analysis_type': 'comprehensive_clinical',
                'processed_at': datetime.utcnow().isoformat()
            }
            
            transcript.anthropic_analysis = result
            db.session.commit()
            
            print(f"✓ Completed Anthropic analysis for {transcript.original_filename}")
            return True
            
        except Exception as e:
            print(f"✗ Error processing {transcript.original_filename}: {e}")
            db.session.rollback()
            return False

def process_one_gemini():
    """Process one Gemini analysis"""
    with app.app_context():
        # Get one transcript missing Gemini analysis
        transcript = db.session.query(Transcript).filter(
            Transcript.gemini_analysis.is_(None)
        ).first()
        
        if not transcript:
            print("No transcripts need Gemini analysis")
            return False
            
        try:
            print(f"Processing Gemini: {transcript.original_filename}")
            
            # Initialize Gemini
            genai.configure(api_key=Config.GEMINI_API_KEY)
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            
            # Create prompt
            prompt = f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript.raw_content}"
            
            # Make API call
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=8192
                )
            )
            
            # Save result
            result = {
                'clinical_progress_note': response.text,
                'provider': 'gemini',
                'model': Config.GEMINI_MODEL,
                'analysis_type': 'comprehensive_clinical',
                'processed_at': datetime.utcnow().isoformat()
            }
            
            transcript.gemini_analysis = result
            db.session.commit()
            
            print(f"✓ Completed Gemini analysis for {transcript.original_filename}")
            return True
            
        except Exception as e:
            print(f"✗ Error processing {transcript.original_filename}: {e}")
            db.session.rollback()
            return False

def main():
    """Main processing function"""
    print("Starting AI completion process...")
    
    # Process one of each type
    anthropic_success = process_one_anthropic()
    time.sleep(3)  # Rate limiting
    gemini_success = process_one_gemini()
    
    # Show status
    with app.app_context():
        total = db.session.query(Transcript).count()
        anthropic_complete = db.session.query(Transcript).filter(
            Transcript.anthropic_analysis.isnot(None)
        ).count()
        gemini_complete = db.session.query(Transcript).filter(
            Transcript.gemini_analysis.isnot(None)
        ).count()
        
        print(f"\nStatus Update:")
        print(f"Anthropic: {anthropic_complete}/{total} complete")
        print(f"Gemini: {gemini_complete}/{total} complete")

if __name__ == "__main__":
    main()