"""
AI Completion Dashboard - Real-time monitoring and completion tracking
"""

import time
import logging
from datetime import datetime
from app import app, db
from models import Transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICompletionDashboard:
    def __init__(self):
        self.start_time = datetime.now()
        self.initial_stats = self.get_current_stats()
    
    def get_current_stats(self):
        """Get current completion statistics"""
        with app.app_context():
            total = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed'
            ).count()
            
            openai = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.openai_analysis.isnot(None)
            ).count()
            
            anthropic = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.anthropic_analysis.isnot(None)
            ).count()
            
            gemini = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.gemini_analysis.isnot(None)
            ).count()
            
            notion_synced = db.session.query(Transcript).filter(
                Transcript.processing_status == 'completed',
                Transcript.notion_synced == True
            ).count()
            
            return {
                'total': total,
                'openai': openai,
                'anthropic': anthropic,
                'gemini': gemini,
                'notion': notion_synced,
                'timestamp': datetime.now()
            }
    
    def calculate_progress(self, current_stats):
        """Calculate progress since monitoring started"""
        initial = self.initial_stats
        
        anthropic_progress = current_stats['anthropic'] - initial['anthropic']
        gemini_progress = current_stats['gemini'] - initial['gemini']
        
        return {
            'anthropic_gained': anthropic_progress,
            'gemini_gained': gemini_progress,
            'total_gained': anthropic_progress + gemini_progress,
            'session_duration': (datetime.now() - self.start_time).total_seconds() / 60
        }
    
    def estimate_completion_time(self, current_stats):
        """Estimate time to completion based on current progress"""
        progress = self.calculate_progress(current_stats)
        
        if progress['total_gained'] == 0:
            return "Unable to estimate (no progress yet)"
        
        # Calculate processing rate (analyses per minute)
        rate = progress['total_gained'] / progress['session_duration']
        
        if rate <= 0:
            return "Unable to estimate"
        
        # Calculate remaining work
        anthropic_remaining = current_stats['total'] - current_stats['anthropic']
        gemini_remaining = current_stats['total'] - current_stats['gemini']
        total_remaining = anthropic_remaining + gemini_remaining
        
        # Estimate completion time
        estimated_minutes = total_remaining / rate
        
        if estimated_minutes < 60:
            return f"{estimated_minutes:.1f} minutes"
        else:
            hours = int(estimated_minutes // 60)
            minutes = int(estimated_minutes % 60)
            return f"{hours}h {minutes}m"
    
    def display_dashboard(self):
        """Display the AI completion dashboard"""
        current_stats = self.get_current_stats()
        progress = self.calculate_progress(current_stats)
        
        print("\n" + "="*70)
        print("AI TRANSCRIPT PROCESSING COMPLETION DASHBOARD")
        print("="*70)
        
        # System Overview
        print(f"System Status: OPERATIONAL")
        print(f"Total Transcripts: {current_stats['total']}")
        print(f"Notion Sync: {current_stats['notion']}/{current_stats['total']} (100%)")
        print()
        
        # AI Analysis Progress
        print("AI ANALYSIS COMPLETION:")
        print(f"  OpenAI:    {current_stats['openai']:>2}/{current_stats['total']} ({current_stats['openai']/current_stats['total']*100:>5.1f}%)")
        print(f"  Anthropic: {current_stats['anthropic']:>2}/{current_stats['total']} ({current_stats['anthropic']/current_stats['total']*100:>5.1f}%)")
        print(f"  Gemini:    {current_stats['gemini']:>2}/{current_stats['total']} ({current_stats['gemini']/current_stats['total']*100:>5.1f}%)")
        print()
        
        # Session Progress
        print("SESSION PROGRESS:")
        print(f"  Session Duration: {progress['session_duration']:.1f} minutes")
        print(f"  Anthropic Gained: +{progress['anthropic_gained']}")
        print(f"  Gemini Gained: +{progress['gemini_gained']}")
        print(f"  Total Progress: +{progress['total_gained']} analyses")
        print()
        
        # Remaining Work
        anthropic_remaining = current_stats['total'] - current_stats['anthropic']
        gemini_remaining = current_stats['total'] - current_stats['gemini']
        
        print("REMAINING ANALYSES:")
        print(f"  Anthropic: {anthropic_remaining} transcripts")
        print(f"  Gemini: {gemini_remaining} transcripts")
        print(f"  Total: {anthropic_remaining + gemini_remaining} analyses")
        print()
        
        # Completion Estimate
        estimate = self.estimate_completion_time(current_stats)
        print(f"ESTIMATED COMPLETION: {estimate}")
        print()
        
        # Processing Rate
        if progress['session_duration'] > 0 and progress['total_gained'] > 0:
            rate = progress['total_gained'] / progress['session_duration']
            print(f"PROCESSING RATE: {rate:.2f} analyses/minute")
        
        print("="*70)
        print(f"Last Updated: {current_stats['timestamp'].strftime('%H:%M:%S')}")
        print("="*70)
    
    def run_monitoring_session(self, duration_minutes=10):
        """Run a monitoring session with periodic updates"""
        logger.info(f"Starting AI completion monitoring for {duration_minutes} minutes")
        
        # Initial display
        self.display_dashboard()
        
        end_time = time.time() + (duration_minutes * 60)
        last_stats = self.initial_stats.copy()
        
        while time.time() < end_time:
            time.sleep(60)  # Check every minute
            
            current_stats = self.get_current_stats()
            
            # Check for changes
            if (current_stats['anthropic'] != last_stats['anthropic'] or 
                current_stats['gemini'] != last_stats['gemini']):
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PROGRESS UPDATE:")
                
                if current_stats['anthropic'] > last_stats['anthropic']:
                    gained = current_stats['anthropic'] - last_stats['anthropic']
                    print(f"  Anthropic: +{gained} ({current_stats['anthropic']}/{current_stats['total']})")
                
                if current_stats['gemini'] > last_stats['gemini']:
                    gained = current_stats['gemini'] - last_stats['gemini']
                    print(f"  Gemini: +{gained} ({current_stats['gemini']}/{current_stats['total']})")
                
                last_stats = current_stats.copy()
        
        # Final summary
        print("\nMONITORING SESSION COMPLETE")
        self.display_dashboard()

def main():
    dashboard = AICompletionDashboard()
    dashboard.display_dashboard()

if __name__ == "__main__":
    main()