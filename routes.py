from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Client, Transcript, ProcessingLog, SystemSettings
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from services.analytics_service import AnalyticsService
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)

# Initialize services
try:
    dropbox_service = DropboxService()
    ai_service = AIService()
    notion_service = NotionService()
    analytics_service = AnalyticsService()
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    dropbox_service = None
    ai_service = None
    notion_service = None
    analytics_service = None

@app.route('/')
def dashboard():
    """Main dashboard showing overview of all clients and recent activity"""
    try:
        # Get all clients with their transcript counts
        clients = db.session.query(Client).all()
        
        client_stats = []
        for client in clients:
            transcript_count = len(client.transcripts)
            latest_session = max([t.session_date for t in client.transcripts if t.session_date], default=None)
            
            client_stats.append({
                'id': client.id,
                'name': client.name,
                'transcript_count': transcript_count,
                'latest_session': latest_session,
                'notion_database_id': client.notion_database_id
            })
        
        # Get recent processing logs
        recent_logs = db.session.query(ProcessingLog)\
            .order_by(ProcessingLog.created_at.desc())\
            .limit(10).all()
        
        # Get system statistics
        total_transcripts = db.session.query(Transcript).count()
        pending_transcripts = db.session.query(Transcript)\
            .filter(Transcript.processing_status == 'pending').count()
        failed_transcripts = db.session.query(Transcript)\
            .filter(Transcript.processing_status == 'failed').count()
        
        system_stats = {
            'total_clients': len(clients),
            'total_transcripts': total_transcripts,
            'pending_processing': pending_transcripts,
            'failed_processing': failed_transcripts
        }
        
        return render_template('dashboard.html', 
                             clients=client_stats,
                             recent_logs=recent_logs,
                             system_stats=system_stats)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboard.html', clients=[], recent_logs=[], system_stats={})

@app.route('/client/<int:client_id>')
def client_details(client_id):
    """Detailed view of a specific client"""
    try:
        client = db.session.get(Client, client_id)
        if not client:
            flash("Client not found", "error")
            return redirect(url_for('dashboard'))
        
        # Get all transcripts for this client
        transcripts = db.session.query(Transcript)\
            .filter(Transcript.client_id == client_id)\
            .order_by(Transcript.session_date.desc()).all()
        
        # Generate analytics if we have data
        dashboard_data = {}
        if transcripts and analytics_service:
            try:
                # Convert transcripts to format expected by analytics service
                session_data = []
                for transcript in transcripts:
                    session_data.append({
                        'session_date': transcript.session_date,
                        'sentiment_score': transcript.sentiment_score,
                        'key_themes': transcript.key_themes,
                        'therapy_insights': transcript.therapy_insights,
                        'raw_content': transcript.raw_content
                    })
                
                dashboard_data = analytics_service.generate_progress_dashboard(session_data)
                
            except Exception as e:
                logger.error(f"Error generating analytics for client {client_id}: {str(e)}")
                dashboard_data = {}
        
        return render_template('client_details.html', 
                             client=client,
                             transcripts=transcripts,
                             dashboard_data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error loading client details: {str(e)}")
        flash(f"Error loading client details: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/client/<int:client_id>/longitudinal-analysis')
def longitudinal_analysis(client_id):
    """Generate longitudinal analysis for a client"""
    try:
        client = db.session.get(Client, client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get processed transcripts
        transcripts = db.session.query(Transcript)\
            .filter(Transcript.client_id == client_id)\
            .filter(Transcript.processing_status == 'completed')\
            .order_by(Transcript.session_date.asc()).all()
        
        if len(transcripts) < 2:
            return jsonify({'error': 'Need at least 2 sessions for longitudinal analysis'}), 400
        
        if not ai_service:
            return jsonify({'error': 'AI service not available'}), 503
        
        # Prepare session data for analysis
        session_data = []
        for transcript in transcripts:
            session_data.append({
                'session_date': transcript.session_date.isoformat() if transcript.session_date else None,
                'sentiment_score': transcript.sentiment_score,
                'key_themes': transcript.key_themes,
                'therapy_insights': transcript.therapy_insights,
                'progress_indicators': transcript.progress_indicators
            })
        
        # Perform longitudinal analysis
        longitudinal_results = ai_service.analyze_longitudinal_progress(session_data)
        
        # Save results to Notion if configured
        if notion_service and client.notion_database_id:
            try:
                notion_service.create_longitudinal_report(client.notion_database_id, longitudinal_results)
            except Exception as e:
                logger.warning(f"Failed to save longitudinal report to Notion: {str(e)}")
        
        return jsonify(longitudinal_results)
        
    except Exception as e:
        logger.error(f"Error performing longitudinal analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/settings')
def settings():
    """System settings and configuration"""
    try:
        # Test service connections
        service_status = {}
        
        if dropbox_service:
            service_status['dropbox'] = dropbox_service.test_connection()
        else:
            service_status['dropbox'] = False
        
        if notion_service:
            service_status['notion'] = notion_service.test_connection()
        else:
            service_status['notion'] = False
        
        # AI services status
        service_status['openai'] = ai_service.openai_client is not None if ai_service else False
        service_status['anthropic'] = ai_service.anthropic_client is not None if ai_service else False
        service_status['gemini'] = ai_service.gemini_client is not None if ai_service else False
        
        # Get system settings
        settings_records = db.session.query(SystemSettings).all()
        settings_dict = {setting.key: setting.value for setting in settings_records}
        
        return render_template('settings.html', 
                             service_status=service_status,
                             settings=settings_dict)
        
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        flash(f"Error loading settings: {str(e)}", "error")
        return render_template('settings.html', service_status={}, settings={})

@app.route('/api/manual-scan', methods=['POST'])
def manual_scan():
    """Manually trigger a Dropbox scan"""
    try:
        if not dropbox_service:
            return jsonify({'error': 'Dropbox service not available'}), 503
        
        # Get list of already processed files
        processed_files = [t.dropbox_path for t in db.session.query(Transcript).all()]
        
        # Scan for new files
        new_files = dropbox_service.scan_for_new_files(processed_files)
        
        return jsonify({
            'message': f'Scan completed. Found {len(new_files)} new files.',
            'new_files': [f['name'] for f in new_files]
        })
        
    except Exception as e:
        logger.error(f"Error during manual scan: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reprocess-transcript/<int:transcript_id>', methods=['POST'])
def reprocess_transcript(transcript_id):
    """Reprocess a specific transcript"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            return jsonify({'error': 'Transcript not found'}), 404
        
        # Mark for reprocessing
        transcript.processing_status = 'pending'
        db.session.commit()
        
        return jsonify({'message': 'Transcript marked for reprocessing'})
        
    except Exception as e:
        logger.error(f"Error marking transcript for reprocessing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-client', methods=['POST'])
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()
        client_name = data.get('name', '').strip()
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Check if client already exists
        existing_client = db.session.query(Client).filter(Client.name.ilike(f'%{client_name}%')).first()
        if existing_client:
            return jsonify({'error': 'Client with similar name already exists'}), 400
        
        # Create new client
        client = Client(name=client_name)
        db.session.add(client)
        db.session.flush()  # Get the ID
        
        # Create Notion database if service is available
        notion_db_id = None
        if notion_service:
            try:
                notion_db_id = notion_service.create_client_database(client_name)
                if notion_db_id:
                    client.notion_database_id = notion_db_id
            except Exception as e:
                logger.warning(f"Failed to create Notion database for {client_name}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Client {client_name} created successfully',
            'client_id': client.id,
            'notion_database_id': notion_db_id
        })
        
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing-logs')
def get_processing_logs():
    """Get recent processing logs"""
    try:
        logs = db.session.query(ProcessingLog)\
            .order_by(ProcessingLog.created_at.desc())\
            .limit(50).all()
        
        log_data = []
        for log in logs:
            log_data.append({
                'id': log.id,
                'activity_type': log.activity_type,
                'status': log.status,
                'message': log.message,
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'transcript_id': log.transcript_id
            })
        
        return jsonify(log_data)
        
    except Exception as e:
        logger.error(f"Error getting processing logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcript/<int:transcript_id>/analysis')
def get_transcript_analysis(transcript_id):
    """Get detailed analysis for a specific transcript"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            return jsonify({'error': 'Transcript not found'}), 404
        
        analysis_data = {
            'openai_analysis': transcript.openai_analysis,
            'anthropic_analysis': transcript.anthropic_analysis,
            'gemini_analysis': transcript.gemini_analysis,
            'sentiment_score': transcript.sentiment_score,
            'key_themes': transcript.key_themes,
            'therapy_insights': transcript.therapy_insights,
            'progress_indicators': transcript.progress_indicators
        }
        
        return jsonify(analysis_data)
        
    except Exception as e:
        logger.error(f"Error getting transcript analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'services': {
            'database': True,  # If we got here, DB is working
            'dropbox': dropbox_service is not None,
            'ai_service': ai_service is not None,
            'notion': notion_service is not None,
            'analytics': analytics_service is not None
        }
    })
