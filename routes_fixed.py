from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Client, Transcript, ProcessingLog, SystemSettings
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from services.analytics_service import AnalyticsService
from services.emotional_analysis import EmotionalAnalysis
from services.email_summary_service import EmailSummaryService
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
    emotional_analyzer = EmotionalAnalysis()
    email_summary_service = EmailSummaryService()
    from services.manual_upload_service import ManualUploadService
    manual_upload_service = ManualUploadService(ai_service=ai_service)
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    dropbox_service = None
    ai_service = None
    notion_service = None
    analytics_service = None
    emotional_analyzer = None
    email_summary_service = None
    manual_upload_service = None

@app.route('/')
def dashboard():
    """Main dashboard showing overview of all clients and recent activity"""
    try:
        # Get all clients with their transcript counts - ordered alphabetically
        clients = db.session.query(Client).order_by(Client.name.asc()).all()

        client_stats = []
        for client in clients:
            transcripts = db.session.query(Transcript).filter_by(client_id=client.id).all()
            transcript_count = len(transcripts)
            latest_session = max([t.session_date for t in transcripts if t.session_date], default=None)

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

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring system status"""
    try:
        # Test database connection
        db_healthy = True
        try:
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            db_healthy = False

        # Test service connections
        services_status = {}
        
        # Dropbox service
        if dropbox_service:
            services_status['dropbox'] = dropbox_service.test_connection()
        else:
            services_status['dropbox'] = False

        # Notion service
        if notion_service:
            services_status['notion'] = notion_service.test_connection()
        else:
            services_status['notion'] = False

        # AI services
        ai_services_healthy = False
        if ai_service:
            ai_services_healthy = (ai_service.openai_client is not None or 
                                 ai_service.anthropic_client is not None or 
                                 ai_service.gemini_client is not None)

        services_status['ai_services'] = ai_services_healthy

        # Overall health status
        overall_healthy = db_healthy and (services_status['dropbox'] or services_status['notion'] or ai_services_healthy)

        return jsonify({
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': db_healthy,
            'services': services_status
        }), 200 if overall_healthy else 503

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

@app.route('/api/system-stats')
def api_system_stats():
    """API endpoint for system statistics"""
    default_response = {
        'system_stats': {
            'total_clients': 0,
            'total_transcripts': 0,
            'pending_processing': 0,
            'failed_processing': 0
        }
    }

    try:
        # Ensure database session is fresh
        db.session.close()

        # Get system statistics with individual error handling
        try:
            total_clients = db.session.query(Client).count()
        except Exception as e:
            logger.warning(f"Error counting clients: {str(e)}")
            total_clients = 0

        try:
            total_transcripts = db.session.query(Transcript).count()
        except Exception as e:
            logger.warning(f"Error counting transcripts: {str(e)}")
            total_transcripts = 0

        try:
            pending_transcripts = db.session.query(Transcript)\
                .filter(Transcript.processing_status == 'pending').count()
        except Exception as e:
            logger.warning(f"Error counting pending transcripts: {str(e)}")
            pending_transcripts = 0

        try:
            failed_transcripts = db.session.query(Transcript)\
                .filter(Transcript.processing_status == 'failed').count()
        except Exception as e:
            logger.warning(f"Error counting failed transcripts: {str(e)}")
            failed_transcripts = 0

        system_stats = {
            'total_clients': total_clients,
            'total_transcripts': total_transcripts,
            'pending_processing': pending_transcripts,
            'failed_processing': failed_transcripts
        }

        response_data = {'system_stats': system_stats}
        logger.debug(f"System stats response: {response_data}")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Critical error getting system stats: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify(default_response), 200

@app.route('/api/processing-logs')
def get_processing_logs():
    """Get recent processing logs"""
    try:
        # Ensure database session is fresh
        db.session.close()

        logs = db.session.query(ProcessingLog)\
            .order_by(ProcessingLog.created_at.desc())\
            .limit(50).all()

        log_data = []
        for log in logs:
            try:
                log_entry = {
                    'id': log.id,
                    'activity_type': log.activity_type or 'unknown',
                    'status': log.status or 'info',
                    'message': log.message or 'No message',
                    'created_at': log.created_at.isoformat() if log.created_at else datetime.now(timezone.utc).isoformat(),
                    'transcript_id': log.transcript_id
                }
                log_data.append(log_entry)
            except Exception as e:
                logger.warning(f"Error processing log entry {log.id}: {str(e)}")
                continue

        logger.debug(f"Processing logs response: {len(log_data)} entries")
        return jsonify(log_data), 200

    except Exception as e:
        logger.error(f"Critical error getting processing logs: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify([]), 200

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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload and process therapy transcript files manually"""
    if request.method == 'POST':
        if not manual_upload_service: 
            flash('File upload service is currently unavailable. Please try again later.', 'error')
            return render_template('upload.html') 

        if 'transcript' not in request.files:
            flash('No file part selected.', 'error')
            return render_template('upload.html') 

        file = request.files['transcript']
        if not file or not file.filename: 
            flash('No file selected or file has no name.', 'error')
            return render_template('upload.html')

        result = manual_upload_service.handle_file_upload(file)

        if result.get('success'):
            flash(result.get('message', 'File processed successfully!'), 'success')
            return redirect(url_for('dashboard')) 
        else:
            flash(result.get('error', 'An unknown error occurred during file processing.'), 'error')
            return render_template('upload.html') 

    return render_template('upload.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500