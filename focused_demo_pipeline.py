"""
Focused Demo Pipeline - Process 2 clients completely through the entire system
Demonstrates end-to-end processing with AI analysis and Notion sync
"""
import logging
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Client, Transcript
from services.ai_service import AIService
from services.notion_service import NotionService
from services.enhanced_session_summary import EnhancedSessionSummaryService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedDemoPipeline:
    def __init__(self):
        """Initialize services for focused demonstration"""
        self.ai_service = AIService()
        self.notion_service = NotionService()
        self.session_summary_service = EnhancedSessionSummaryService()
        
    def select_demo_clients(self) -> list:
        """Select 2 clients with good data for demonstration"""
        with app.app_context():
            # Find clients with transcripts that have content
            clients = db.session.query(Client).join(Transcript).filter(
                Transcript.raw_content.isnot(None),
                Transcript.raw_content != ''
            ).limit(2).all()
            
            if len(clients) < 2:
                logger.warning("Not enough clients with content found, selecting any 2 clients")
                clients = db.session.query(Client).limit(2).all()
            
            return clients
    
    def process_client_completely(self, client: Client) -> dict:
        """Process a single client completely through the pipeline"""
        logger.info(f"Processing client: {client.name}")
        
        results = {
            'client_name': client.name,
            'transcripts_processed': 0,
            'ai_analyses': [],
            'session_summaries': [],
            'notion_synced': False,
            'errors': []
        }
        
        # Get all transcripts for this client
        transcripts = db.session.query(Transcript).filter_by(client_id=client.id).all()
        
        for transcript in transcripts:
            try:
                logger.info(f"Processing transcript: {transcript.original_filename}")
                
                # 1. Complete AI Analysis (all 3 providers)
                ai_results = self._complete_ai_analysis(transcript)
                results['ai_analyses'].append(ai_results)
                
                # 2. Generate Enhanced Session Summary
                summary_results = self._generate_session_summary(transcript)
                results['session_summaries'].append(summary_results)
                
                # 3. Update transcript with results
                self._update_transcript(transcript, ai_results, summary_results)
                
                results['transcripts_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing transcript {transcript.original_filename}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # 4. Sync to Notion
        try:
            notion_result = self._sync_to_notion(client)
            results['notion_synced'] = notion_result
        except Exception as e:
            error_msg = f"Error syncing to Notion: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def _complete_ai_analysis(self, transcript: Transcript) -> dict:
        """Complete AI analysis using all 3 providers"""
        logger.info(f"Running AI analysis for transcript {transcript.id}")
        
        ai_results = {
            'openai': None,
            'anthropic': None,
            'gemini': None,
            'errors': []
        }
        
        if not transcript.raw_content:
            ai_results['errors'].append("No raw content available for analysis")
            return ai_results
        
        # OpenAI Analysis
        try:
            if self.ai_service.is_openai_available():
                openai_result = self.ai_service._analyze_with_openai(
                    transcript.raw_content, 
                    transcript.client.name
                )
                ai_results['openai'] = openai_result
                transcript.openai_analysis = openai_result
                logger.info("OpenAI analysis completed")
        except Exception as e:
            ai_results['errors'].append(f"OpenAI error: {str(e)}")
        
        # Anthropic Analysis
        try:
            if self.ai_service.is_anthropic_available():
                anthropic_result = self.ai_service._analyze_with_anthropic(
                    transcript.raw_content,
                    transcript.client.name
                )
                ai_results['anthropic'] = anthropic_result
                transcript.anthropic_analysis = anthropic_result
                logger.info("Anthropic analysis completed")
        except Exception as e:
            ai_results['errors'].append(f"Anthropic error: {str(e)}")
        
        # Gemini Analysis
        try:
            if self.ai_service.is_gemini_available():
                gemini_result = self.ai_service._analyze_with_gemini(
                    transcript.raw_content,
                    transcript.client.name
                )
                ai_results['gemini'] = gemini_result
                transcript.gemini_analysis = gemini_result
                logger.info("Gemini analysis completed")
        except Exception as e:
            ai_results['errors'].append(f"Gemini error: {str(e)}")
        
        return ai_results
    
    def _generate_session_summary(self, transcript: Transcript) -> dict:
        """Generate enhanced session summary"""
        logger.info(f"Generating session summary for transcript {transcript.id}")
        
        try:
            transcript_data = {
                'id': transcript.id,
                'original_filename': transcript.original_filename,
                'raw_content': transcript.raw_content,
                'client_name': transcript.client.name,
                'session_date': transcript.session_date,
                'openai_analysis': transcript.openai_analysis,
                'anthropic_analysis': transcript.anthropic_analysis,
                'gemini_analysis': transcript.gemini_analysis
            }
            
            summary_result = self.session_summary_service.generate_session_summary(transcript_data)
            
            # Store the summary
            transcript.session_summary = summary_result
            
            logger.info("Session summary generated successfully")
            return summary_result
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return {'error': str(e)}
    
    def _update_transcript(self, transcript: Transcript, ai_results: dict, summary_results: dict):
        """Update transcript with all results"""
        try:
            # Update processing status
            transcript.processing_status = 'completed'
            transcript.processed_at = datetime.now()
            
            # Commit changes
            db.session.commit()
            logger.info(f"Transcript {transcript.id} updated successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating transcript: {str(e)}")
            raise
    
    def _sync_to_notion(self, client: Client) -> bool:
        """Sync client data to Notion"""
        logger.info(f"Syncing client {client.name} to Notion")
        
        try:
            # Get all processed transcripts for this client
            transcripts = db.session.query(Transcript).filter_by(
                client_id=client.id,
                processing_status='completed'
            ).all()
            
            for transcript in transcripts:
                # Sync each transcript to Notion
                notion_result = self.notion_service.sync_transcript_to_notion(transcript)
                if notion_result:
                    transcript.notion_synced = True
                    logger.info(f"Transcript {transcript.id} synced to Notion")
            
            # Update client notion sync status
            client.notion_synced = True
            db.session.commit()
            
            logger.info(f"Client {client.name} successfully synced to Notion")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing to Notion: {str(e)}")
            return False
    
    def run_focused_demo(self):
        """Run the complete focused demonstration"""
        logger.info("=== Starting Focused Demo Pipeline ===")
        
        with app.app_context():
            # Select 2 clients for demonstration
            demo_clients = self.select_demo_clients()
            
            if len(demo_clients) < 2:
                logger.error("Not enough clients found for demonstration")
                return
            
            logger.info(f"Selected clients for demo: {[c.name for c in demo_clients]}")
            
            demo_results = {
                'start_time': datetime.now().isoformat(),
                'clients_processed': [],
                'total_transcripts': 0,
                'total_summaries': 0,
                'notion_syncs': 0,
                'errors': []
            }
            
            # Process each client completely
            for client in demo_clients:
                try:
                    client_results = self.process_client_completely(client)
                    demo_results['clients_processed'].append(client_results)
                    demo_results['total_transcripts'] += client_results['transcripts_processed']
                    demo_results['total_summaries'] += len(client_results['session_summaries'])
                    if client_results['notion_synced']:
                        demo_results['notion_syncs'] += 1
                    demo_results['errors'].extend(client_results['errors'])
                    
                except Exception as e:
                    error_msg = f"Error processing client {client.name}: {str(e)}"
                    logger.error(error_msg)
                    demo_results['errors'].append(error_msg)
            
            demo_results['end_time'] = datetime.now().isoformat()
            
            # Print final results
            self._print_demo_results(demo_results)
            
            return demo_results
    
    def _print_demo_results(self, results: dict):
        """Print comprehensive demo results"""
        logger.info("=== FOCUSED DEMO PIPELINE RESULTS ===")
        logger.info(f"Processing completed: {results['end_time']}")
        logger.info(f"Clients processed: {len(results['clients_processed'])}")
        logger.info(f"Total transcripts: {results['total_transcripts']}")
        logger.info(f"Session summaries generated: {results['total_summaries']}")
        logger.info(f"Notion syncs completed: {results['notion_syncs']}")
        
        if results['errors']:
            logger.warning(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        for client_result in results['clients_processed']:
            logger.info(f"\nClient: {client_result['client_name']}")
            logger.info(f"  - Transcripts processed: {client_result['transcripts_processed']}")
            logger.info(f"  - AI analyses completed: {len(client_result['ai_analyses'])}")
            logger.info(f"  - Session summaries: {len(client_result['session_summaries'])}")
            logger.info(f"  - Notion synced: {client_result['notion_synced']}")

if __name__ == "__main__":
    # Run the focused demonstration
    pipeline = FocusedDemoPipeline()
    results = pipeline.run_focused_demo()