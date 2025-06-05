"""
Demo Pipeline for Two Specific Clients - Sarah Palladino and Krista Flood
Complete end-to-end processing with AI analysis and Notion sync
"""
import logging
import sys
import os
from datetime import datetime
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Client, Transcript
from services.ai_service import AIService
from services.notion_service import NotionService
from services.enhanced_session_summary import EnhancedSessionSummaryService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwoClientDemo:
    def __init__(self):
        self.ai_service = AIService()
        self.notion_service = NotionService()
        self.session_summary_service = EnhancedSessionSummaryService()
        
    def process_client(self, client_id: int, client_name: str):
        """Process a single client completely"""
        logger.info(f"Processing {client_name} (ID: {client_id})")
        
        with app.app_context():
            client = db.session.get(Client, client_id)
            if not client:
                logger.error(f"Client {client_id} not found")
                return
            
            transcripts = db.session.query(Transcript).filter_by(client_id=client_id).all()
            logger.info(f"Found {len(transcripts)} transcripts for {client_name}")
            
            for i, transcript in enumerate(transcripts, 1):
                logger.info(f"Processing transcript {i}/{len(transcripts)}: {transcript.original_filename}")
                
                try:
                    # Complete AI Analysis if missing
                    if not transcript.anthropic_analysis:
                        logger.info("Running Anthropic analysis...")
                        anthropic_result = self.ai_service._analyze_with_anthropic(
                            transcript.raw_content[:4000], client_name
                        )
                        transcript.anthropic_analysis = anthropic_result
                        logger.info("Anthropic analysis completed")
                    
                    if not transcript.gemini_analysis:
                        logger.info("Running Gemini analysis...")
                        gemini_result = self.ai_service._analyze_with_gemini(
                            transcript.raw_content[:4000], client_name
                        )
                        transcript.gemini_analysis = gemini_result
                        logger.info("Gemini analysis completed")
                    
                    # Generate Session Summary
                    logger.info("Generating session summary...")
                    transcript_data = {
                        'id': transcript.id,
                        'original_filename': transcript.original_filename,
                        'raw_content': transcript.raw_content,
                        'client_name': client_name,
                        'session_date': transcript.session_date,
                        'openai_analysis': transcript.openai_analysis,
                        'anthropic_analysis': transcript.anthropic_analysis,
                        'gemini_analysis': transcript.gemini_analysis
                    }
                    
                    summary_result = self.session_summary_service.generate_session_summary(transcript_data)
                    transcript.session_summary = summary_result
                    logger.info("Session summary generated")
                    
                    # Update status
                    transcript.processing_status = 'completed'
                    transcript.processed_at = datetime.now()
                    
                    db.session.commit()
                    logger.info(f"Transcript {i} processing completed")
                    
                except Exception as e:
                    logger.error(f"Error processing transcript {i}: {str(e)}")
                    db.session.rollback()
                    continue
            
            # Sync to Notion
            logger.info(f"Syncing {client_name} to Notion...")
            try:
                for transcript in transcripts:
                    if transcript.processing_status == 'completed':
                        notion_result = self.notion_service.sync_transcript_to_notion(transcript)
                        if notion_result:
                            transcript.notion_synced = True
                            logger.info(f"Transcript {transcript.id} synced to Notion")
                
                client.notion_synced = True
                db.session.commit()
                logger.info(f"{client_name} successfully synced to Notion")
                
            except Exception as e:
                logger.error(f"Error syncing {client_name} to Notion: {str(e)}")
                db.session.rollback()
    
    def run_demo(self):
        """Run the complete demo for both clients"""
        logger.info("=== Starting Two Client Demo Pipeline ===")
        
        # Process Sarah Palladino (ID: 18)
        self.process_client(18, "Sarah Palladino")
        
        # Process Krista Flood (ID: 10) 
        self.process_client(10, "Krista Flood")
        
        logger.info("=== Demo Pipeline Completed ===")
        
        # Generate summary report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final status report"""
        logger.info("=== FINAL DEMO REPORT ===")
        
        with app.app_context():
            for client_id, client_name in [(18, "Sarah Palladino"), (10, "Krista Flood")]:
                client = db.session.get(Client, client_id)
                transcripts = db.session.query(Transcript).filter_by(client_id=client_id).all()
                
                completed = sum(1 for t in transcripts if t.processing_status == 'completed')
                with_anthropic = sum(1 for t in transcripts if t.anthropic_analysis)
                with_gemini = sum(1 for t in transcripts if t.gemini_analysis)
                with_summary = sum(1 for t in transcripts if t.session_summary)
                notion_synced = sum(1 for t in transcripts if t.notion_synced)
                
                logger.info(f"\n{client_name}:")
                logger.info(f"  Total transcripts: {len(transcripts)}")
                logger.info(f"  Completed processing: {completed}")
                logger.info(f"  Anthropic analyses: {with_anthropic}")
                logger.info(f"  Gemini analyses: {with_gemini}")
                logger.info(f"  Session summaries: {with_summary}")
                logger.info(f"  Notion synced: {notion_synced}")
                logger.info(f"  Client Notion status: {client.notion_synced}")

if __name__ == "__main__":
    demo = TwoClientDemo()
    demo.run_demo()