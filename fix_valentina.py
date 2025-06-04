#!/usr/bin/env python3
"""
Fix Valentina's transcript to show AI-generated clinical progress note instead of raw text
"""
import sys
sys.path.append('.')
from app import app, db
from models import Client, Transcript
from services.notion_service import NotionService
from config import Config
import openai
from datetime import datetime

def fix_valentina_note():
    """Replace Valentina's raw transcript with comprehensive clinical analysis"""
    with app.app_context():
        # Find Valentina's transcript
        valentina = Client.query.filter_by(name='Valentina Gjidoda').first()
        if not valentina:
            print("Valentina client not found")
            return
            
        transcript = Transcript.query.filter_by(client_id=valentina.id).first()
        if not transcript:
            print("Valentina transcript not found")
            return
        
        print(f"Processing Valentina's transcript: {transcript.original_filename}")
        
        # Generate comprehensive clinical progress note
        openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        clinical_prompt = f"""Create a comprehensive clinical progress note for Valentina Gjidoda's therapy session on December 16, 2022.

Structure your response with these sections:

**SUBJECTIVE**: Client's self-reported experiences, concerns, and emotional state during this session

**OBJECTIVE**: Clinical observations of presentation, mood, affect, behavior, and therapeutic engagement 

**ASSESSMENT**: Clinical insights, therapeutic progress, diagnostic impressions, and treatment response

**PLAN**: Treatment recommendations, interventions, homework assignments, and goals for next session

**COMPREHENSIVE NARRATIVE SUMMARY**: Integrated clinical understanding of this session's significance in Valentina's therapeutic journey

Session transcript content:
{transcript.raw_content}"""
        
        try:
            response = openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        'role': 'system', 
                        'content': 'You are an expert clinical therapist creating comprehensive, structured progress notes with deep clinical analysis for therapy sessions.'
                    },
                    {
                        'role': 'user', 
                        'content': clinical_prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            comprehensive_analysis = response.choices[0].message.content
            
            # Update transcript with AI analysis
            transcript.openai_analysis = {
                'comprehensive_clinical_analysis': comprehensive_analysis
            }
            transcript.processed_at = datetime.now()
            db.session.commit()
            
            print(f"Generated clinical analysis: {len(comprehensive_analysis):,} characters")
            
            # Update Notion page with clinical analysis instead of raw content
            notion_service = NotionService()
            
            # Create new progress note with AI analysis
            session_result = notion_service.create_progress_note(
                client_name='Valentina Gjidoda',
                session_date='12/16/2022',
                content=comprehensive_analysis,  # Use AI analysis, NOT raw transcript
                rich_text_blocks=[],
                emotional_data={
                    'primary_emotion': 'processing',
                    'intensity': 0.7,
                    'key_themes': ['suicidal ideation', 'therapeutic relationship', 'emotional processing']
                },
                ai_analysis={
                    'comprehensive_clinical_analysis': comprehensive_analysis
                }
            )
            
            if session_result and session_result.get('success'):
                transcript.notion_page_id = session_result.get('page_id')
                transcript.notion_synced = True
                db.session.commit()
                
                print("SUCCESS: Valentina's note updated with comprehensive clinical progress note")
                print(f"New page ID: {session_result.get('page_id')}")
                print("Content: AI-generated clinical analysis (NOT raw transcript text)")
                
                return True
            else:
                error_msg = session_result.get('error', 'Unknown error')
                print(f"Failed to update Notion page: {error_msg}")
                return False
                
        except Exception as e:
            print(f"Error generating clinical analysis: {e}")
            return False

if __name__ == "__main__":
    success = fix_valentina_note()
    if success:
        print("\nValentina's transcript has been fixed with proper clinical analysis")
    else:
        print("\nFailed to fix Valentina's transcript")