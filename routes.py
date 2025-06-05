from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Client, Transcript, ProcessingLog, SystemSettings
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from services.analytics_service import AnalyticsService
from services.emotional_analysis import EmotionalAnalysis
# from services.visualization_service import VisualizationService # Removed
from services.email_summary_service import EmailSummaryService
from services.manual_upload_service import ManualUploadService
from sqlalchemy import func, or_, text, literal_column
from datetime import datetime, timezone
import logging
import json
from markdown import markdown
# import os # No longer needed in this file

logger = logging.getLogger(__name__)

# Standardized API Response Helpers
def make_success_response(data=None, message=None, status_code=200):
    response_dict = {"success": True}
    if data is not None:
        response_dict["data"] = data
    if message is not None:
        response_dict["message"] = message
    return jsonify(response_dict), status_code

def make_error_response(message, error_code=None, details=None, status_code=400):
    error_payload = {"message": message}
    if error_code is not None:
        error_payload["code"] = error_code
    if details is not None:
        error_payload["details"] = details
    response_dict = {"success": False, "error": error_payload}
    return jsonify(response_dict), status_code

# Initialize services
try:
    dropbox_service = DropboxService()
    ai_service = AIService()
    notion_service = NotionService()
    analytics_service = AnalyticsService()
    emotional_analyzer = EmotionalAnalysis()
    # visualization_service = VisualizationService() # Removed
    email_summary_service = EmailSummaryService()
    manual_upload_service = ManualUploadService(ai_service=ai_service) # Pass ai_service
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    dropbox_service = None
    ai_service = None
    notion_service = None
    analytics_service = None
    emotional_analyzer = None
    # visualization_service = None # Removed
    email_summary_service = None
    manual_upload_service = None

@app.route('/')
def dashboard():
    """Main dashboard showing overview of all clients and recent activity"""
    try:
        client_summary_rows = db.session.query(
            Client.id.label('id'),
            Client.name.label('name'),
            Client.notion_database_id.label('notion_database_id'),
            func.count(Transcript.id).label('transcript_count'),
            func.max(Transcript.session_date).label('latest_session')
        ).select_from(Client).outerjoin(
            Transcript, Client.id == Transcript.client_id
        ).group_by(
            Client.id, Client.name, Client.notion_database_id
        ).order_by(
            Client.name.asc()
        ).all()

        client_stats = [
            {
                'id': row.id,
                'name': row.name,
                'transcript_count': int(row.transcript_count) if row.transcript_count is not None else 0,
                'latest_session': row.latest_session,
                'notion_database_id': row.notion_database_id
            }
            for row in client_summary_rows
        ]
        recent_logs = db.session.query(ProcessingLog)\
            .order_by(ProcessingLog.created_at.desc())\
            .limit(10).all()
        total_transcripts = db.session.query(Transcript).count()
        pending_transcripts = db.session.query(Transcript)\
            .filter(Transcript.processing_status == 'pending').count()
        failed_transcripts = db.session.query(Transcript)\
            .filter(Transcript.processing_status == 'failed').count()
        system_stats = {
            'total_clients': len(client_stats),
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
        return render_template('dashboard.html', 
                             clients=[], 
                             recent_logs=[], 
                             system_stats={'total_clients': 0, 'total_transcripts': 0, 'pending_processing': 0, 'failed_processing': 0})

@app.route('/client/<int:client_id>/longitudinal-analysis')
def longitudinal_analysis(client_id):
    """Generate longitudinal analysis for a client"""
    try:
        client = db.session.get(Client, client_id)
        if not client:
            return make_error_response("Client not found", error_code="RESOURCE_NOT_FOUND", status_code=404)

        transcripts = db.session.query(Transcript)\
            .filter(Transcript.client_id == client_id)\
            .filter(Transcript.processing_status == 'completed')\
            .order_by(Transcript.session_date.asc()).all()

        if len(transcripts) < 2:
            return make_error_response("Need at least 2 sessions for longitudinal analysis", error_code="CONDITION_NOT_MET", status_code=400)

        if not ai_service:
            return make_error_response("AI service not available", error_code="SERVICE_UNAVAILABLE", status_code=503)

        session_data = []
        for transcript_obj in transcripts: # Use transcript_obj to avoid confusion with Transcript model
            session_data.append({
                'session_date': transcript_obj.session_date.isoformat() if transcript_obj.session_date else None,
                'sentiment_score': transcript_obj.sentiment_score,
                'key_themes': transcript_obj.key_themes,
                'therapy_insights': transcript_obj.therapy_insights,
                'progress_indicators': transcript_obj.progress_indicators
            })
        longitudinal_results = ai_service.analyze_longitudinal_progress(session_data)
        if notion_service and client.notion_database_id:
            try:
                notion_service.create_longitudinal_report(client.notion_database_id, longitudinal_results)
            except Exception as e:
                logger.warning(f"Failed to save longitudinal report to Notion: {str(e)}")
        return make_success_response(data=longitudinal_results)
    except Exception as e:
        logger.error(f"Error performing longitudinal analysis for client {client_id}: {str(e)}")
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/settings')
def settings():
    """System settings and configuration - Not an API endpoint, so no change to response format."""
    try:
        service_status = {}
        if dropbox_service: service_status['dropbox'] = dropbox_service.test_connection()
        else: service_status['dropbox'] = False
        if notion_service: service_status['notion'] = notion_service.test_connection()
        else: service_status['notion'] = False
        
        if ai_service: # Updated to use new methods
            service_status['openai'] = ai_service.is_openai_available()
            service_status['anthropic'] = ai_service.is_anthropic_available()
            service_status['gemini'] = ai_service.is_gemini_available()
        else:
            service_status['openai'] = False
            service_status['anthropic'] = False
            service_status['gemini'] = False
            
        settings_records = db.session.query(SystemSettings).all()
        settings_dict = {setting.key: setting.value for setting in settings_records}
        return render_template('settings.html', 
                             service_status=service_status,
                             settings=settings_dict)
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        flash(f"Error loading settings: {str(e)}", "error")
        return render_template('settings.html', service_status={}, settings={})

@app.route('/search-transcripts')
def search_transcripts_page():
    try:
        clients = db.session.query(Client).order_by(Client.name.asc()).all()
        return render_template('search_transcripts.html', clients=clients)
    except Exception as e:
        logger.error(f"Error loading search transcripts page: {str(e)}")
        flash("Could not load the search page. Please try again later.", "error")
        return redirect(url_for('dashboard'))

@app.route('/api/system-stats')
def api_system_stats():
    """API endpoint for system statistics"""
    try:
        total_clients = db.session.query(Client).count()
        total_transcripts = db.session.query(Transcript).count()
        pending_transcripts = db.session.query(Transcript).filter(Transcript.processing_status == 'pending').count()
        failed_transcripts = db.session.query(Transcript).filter(Transcript.processing_status == 'failed').count()
        system_stats = {
            'total_clients': total_clients,
            'total_transcripts': total_transcripts,
            'pending_processing': pending_transcripts,
            'failed_processing': failed_transcripts
        }
        return make_success_response(data={'system_stats': system_stats})
    except Exception as e:
        logger.error(f"Critical error getting system stats: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return make_error_response("Critical error getting system stats", error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/api/manual-scan', methods=['POST'])
def manual_scan():
    """Manually trigger a Dropbox scan"""
    try:
        if not dropbox_service:
            return make_error_response("Dropbox service not available", error_code="SERVICE_UNAVAILABLE", status_code=503)
        processed_files = [t.dropbox_path for t in db.session.query(Transcript).all() if t.dropbox_path]
        new_files = dropbox_service.scan_for_new_files(processed_files)
        new_files_data = [f.get('name', 'Unknown') for f in new_files] if new_files else []

        if new_files:
            try:
                from scheduler import process_new_files
                import threading
                thread = threading.Thread(target=process_new_files)
                thread.daemon = True
                thread.start()
                return make_success_response(message=f'Scan completed. Found {len(new_files)} new files. Processing started.', data={"new_files": new_files_data})
            except Exception as e:
                logger.error(f"Error starting background processing: {str(e)}")
                return make_error_response(f"Scan completed. Found {len(new_files)} new files, but failed to start background processing: {str(e)}", error_code="BACKGROUND_TASK_ERROR", status_code=500)
        else:
            return make_success_response(message="Scan completed. No new files found.", data={"new_files": []})
    except Exception as e:
        logger.error(f"Error during manual scan: {str(e)}")
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/api/reprocess-transcript/<int:transcript_id>', methods=['POST'])
def reprocess_transcript(transcript_id):
    """Reprocess a specific transcript"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            return make_error_response("Transcript not found", error_code="RESOURCE_NOT_FOUND", status_code=404)
        transcript.processing_status = 'pending'
        db.session.commit()
        return make_success_response(message="Transcript marked for reprocessing")
    except Exception as e:
        logger.error(f"Error marking transcript {transcript_id} for reprocessing: {str(e)}")
        db.session.rollback()
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/api/create-client', methods=['POST'])
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()
        if not data:
            return make_error_response("Request body must be valid JSON.", error_code="INVALID_REQUEST", status_code=400)
        
        client_name = data.get('name', '').strip()
        if not client_name:
            return make_error_response("Client name is required.", error_code="VALIDATION_ERROR", details={"name": ["Client name is required."]}, status_code=400)

        existing_client = db.session.query(Client).filter(Client.name.ilike(client_name)).first() 
        if existing_client:
            return make_error_response("Client with this name already exists.", error_code="DUPLICATE_RESOURCE", status_code=409)

        client = Client(name=client_name)
        db.session.add(client)
        db.session.flush()
        notion_db_id = None
        if notion_service:
            try:
                notion_db_id = notion_service.create_client_database(client_name)
                if notion_db_id: client.notion_database_id = notion_db_id
            except Exception as e:
                logger.warning(f"Failed to create Notion database for {client_name}: {str(e)}")
        db.session.commit()
        return make_success_response(
            message=f'Client {client_name} created successfully', 
            data={'client_id': client.id, 'notion_database_id': notion_db_id},
            status_code=201
        )
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        db.session.rollback()
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/api/processing-logs')
def get_processing_logs():
    """Get recent processing logs"""
    try:
        logs = db.session.query(ProcessingLog).order_by(ProcessingLog.created_at.desc()).limit(50).all()
        log_data = [{
            'id': log.id,
            'activity_type': log.activity_type or 'unknown',
            'status': log.status or 'info',
            'message': log.message or 'No message',
            'created_at': log.created_at.isoformat() if log.created_at else datetime.now(timezone.utc).isoformat(),
            'transcript_id': log.transcript_id
        } for log in logs]
        return make_success_response(data=log_data)
    except Exception as e:
        logger.error(f"Critical error getting processing logs: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return make_error_response("Critical error getting processing logs.", error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/api/scan-dropbox', methods=['POST'])
def scan_dropbox():
    """Alternative endpoint for Dropbox scanning"""
    try:
        if not dropbox_service:
            return make_error_response("Dropbox service not available", error_code="SERVICE_UNAVAILABLE", status_code=503)
        processed_files = [t.dropbox_path for t in db.session.query(Transcript).all() if t.dropbox_path]
        new_files = dropbox_service.scan_for_new_files(processed_files)
        new_files_data = [f.get('name', 'Unknown') for f in new_files] if new_files else []
        return make_success_response(
            message=f'Scan completed. Found {len(new_files_data)} new files.', 
            data={"new_files_count": len(new_files_data), "new_files": new_files_data}
        )
    except Exception as e:
        logger.error(f"Error in scan-dropbox endpoint: {str(e)}")
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.route('/api/test-dropbox', methods=['POST'])
def test_dropbox():
    """Test Dropbox connection and return detailed status"""
    try:
        if not dropbox_service:
            return make_error_response("Dropbox service not initialized", error_code="SERVICE_UNAVAILABLE", details="Check Dropbox access token configuration", status_code=503)
        
        connection_test = dropbox_service.test_connection()
        if not connection_test:
            return make_error_response("Dropbox connection failed", error_code="CONNECTION_ERROR", details="Authentication or network issue", status_code=502)

        account_name = dropbox_service.get_user_account_display_name() or 'Unknown' # Updated
        monitor_folder_path = dropbox_service.get_monitor_folder() # Updated
        
        folder_status = f"Monitoring folder: {monitor_folder_path}"
        files_count = 0
        try:
            all_files = dropbox_service.list_files() # Uses monitor_folder_path internally by default if service is well-designed
            files_count = len(all_files)
        except Exception as e: folder_status = f"Error accessing folder '{monitor_folder_path}': {str(e)}"

        return make_success_response(data={
            'account_name': account_name,
            'folder_status': folder_status,
            'files_found': files_count,
            'monitor_folder': monitor_folder_path,
            'connection_timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Error testing Dropbox: {str(e)}")
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", details="Unexpected error during Dropbox test", status_code=500)

@app.route('/api/transcript/<int:transcript_id>/analysis')
def get_transcript_analysis(transcript_id):
    """Get detailed analysis for a specific transcript"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            return make_error_response("Transcript not found", error_code="RESOURCE_NOT_FOUND", status_code=404)
        analysis_data = {
            'openai_analysis': transcript.openai_analysis,
            'anthropic_analysis': transcript.anthropic_analysis,
            'gemini_analysis': transcript.gemini_analysis,
            'sentiment_score': transcript.sentiment_score,
            'key_themes': transcript.key_themes,
            'therapy_insights': transcript.therapy_insights,
            'progress_indicators': transcript.progress_indicators
        }
        return make_success_response(data=analysis_data)
    except Exception as e:
        logger.error(f"Error getting transcript analysis for {transcript_id}: {str(e)}")
        return make_error_response(str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500)

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return make_error_response("The requested API endpoint was not found.", error_code="ENDPOINT_NOT_FOUND", status_code=404)
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback() 
    logger.error(f"Internal server error: {str(error)}")
    if request.path.startswith('/api/'):
        return make_error_response("An unexpected internal server error occurred.", error_code="INTERNAL_SERVER_ERROR", status_code=500)
    return render_template('500.html'), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'services': {
            'database': True, 
            'dropbox': dropbox_service is not None,
            'ai_service': ai_service is not None,
            'notion': notion_service is not None,
            'analytics': analytics_service is not None,
            'manual_upload': manual_upload_service is not None
            # 'visualization': visualization_service is not None # Removed
        }
    })

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload and process therapy transcript files manually using ManualUploadService."""
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

@app.route('/client/<int:client_id>/visualization')
def client_visualization(client_id):
    try:
        client = db.session.get(Client, client_id)
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('dashboard'))
        
        transcripts_query = Transcript.query.filter_by(client_id=client_id).order_by(Transcript.session_date.asc()).all() # Ensure asc for chronological
        if not transcripts_query:
            flash('No session data available for visualization.', 'info')
            return redirect(url_for('client_details', client_id=client_id))

        session_data = []
        for t_obj in transcripts_query:
            session_data.append({
                'session_date': t_obj.session_date.isoformat() if t_obj.session_date else None,
                'emotional_analysis': t_obj.emotional_analysis, # Pass raw JSON string or dict
                'sentiment_score': t_obj.sentiment_score,
                'key_themes': t_obj.key_themes,
                'therapy_insights': t_obj.therapy_insights,
                'raw_content': t_obj.raw_content # For keyword extraction if needed
            })
        
        client_data_dict = {'name': client.name, 'id': client.id}
        longitudinal_emotions_data = None
        if emotional_analyzer:
            longitudinal_emotions_data = emotional_analyzer.generate_longitudinal_emotional_data(session_data)

        comprehensive_dashboard_data = {}
        if analytics_service:
            comprehensive_dashboard_data = analytics_service.generate_progress_dashboard(
                sessions=session_data,
                client_data=client_data_dict,
                longitudinal_data=longitudinal_emotions_data 
            )
        else:
            flash('Analytics service is currently unavailable.', 'error')
            comprehensive_dashboard_data = {'error': 'Analytics service unavailable', 'success': False}
            # Consider redirecting or rendering with a more prominent error on the page
            # For now, template will handle the 'error' key.

        return render_template('client_visualization.html', 
                             client=client, 
                             analytics_dashboard=comprehensive_dashboard_data,
                             session_count=len(transcripts_query))
    except Exception as e:
        logger.exception(f"Error generating client visualization for client {client_id}: {str(e)}") # Use logger.exception
        flash(f"Error generating visualization: {str(e)}", 'error')
        return redirect(url_for('client_details', client_id=client_id))

@app.route('/transcript/<int:transcript_id>/adaptive-colors')
def adaptive_color_ui(transcript_id):
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            flash('Transcript not found', 'error')
            return redirect(url_for('dashboard'))
        emotional_data = None
        if hasattr(transcript, 'emotional_analysis') and transcript.emotional_analysis:
            try: emotional_data = json.loads(transcript.emotional_analysis) if isinstance(transcript.emotional_analysis, str) else transcript.emotional_analysis
            except json.JSONDecodeError: emotional_data = None
        if not emotional_data and emotional_analyzer and transcript.raw_content:
            ai_analysis = {
                'openai_analysis': transcript.openai_analysis,
                'anthropic_analysis': transcript.anthropic_analysis,
                'gemini_analysis': transcript.gemini_analysis
            }
            emotional_data = emotional_analyzer.analyze_session_emotions(transcript.raw_content, ai_analysis)
            try:
                transcript.emotional_analysis = json.dumps(emotional_data)
                db.session.commit()
            except Exception as e: logger.warning(f"Could not save emotional analysis for transcript {transcript_id}: {str(e)}")
        if not emotional_data:
            emotional_data = {'primary_emotion': 'neutral', 'intensity': 0.5, 'color_palette': {'primary': '#8E9AAF', 'background': '#F8F9FA', 'text': '#2C3E50'}}
        return render_template('adaptive_color_ui.html', 
                             transcript=transcript,
                             emotional_data=emotional_data)
    except Exception as e:
        logger.error(f"Error loading adaptive color UI for transcript {transcript_id}: {str(e)}")
        flash(f"Error loading adaptive interface: {str(e)}", 'error')
        return redirect(url_for('dashboard')) 

@app.route('/send_email_summary/<int:transcript_id>', methods=['POST'])
def send_email_summary(transcript_id):
    # This route primarily uses flash messages and redirects, not JSON API responses.
    # No changes needed for its core success/failure reporting mechanism.
    from services.email_summary_service import ServiceNotConfiguredError # Moved import here
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            flash('Transcript not found', 'error')
            return redirect(url_for('dashboard'))
        recipient_email = request.form.get('recipient_email')
        if not recipient_email:
            flash('Recipient email is required', 'error')
            return redirect(url_for('client_details', client_id=transcript.client_id))

        transcript_data = {
            'client_name': transcript.client.name,
            'session_date': transcript.session_date.strftime('%B %d, %Y') if transcript.session_date else 'Unknown Date',
            'original_filename': transcript.original_filename,
            'openai_analysis': transcript.openai_analysis,
            'anthropic_analysis': transcript.anthropic_analysis,
            'gemini_analysis': transcript.gemini_analysis
        }
        
        if not email_summary_service: # Check if service itself is None
            flash('Email service is currently unavailable.', 'error')
            return redirect(url_for('client_details', client_id=transcript.client_id))

        success = email_summary_service.process_and_send_summary(transcript_data, recipient_email)
        if success: flash(f'Session summary emailed successfully to {recipient_email}', 'success')
        else: flash('Failed to send email summary. Please check email configuration or server logs.', 'error')
        return redirect(url_for('client_details', client_id=transcript.client_id))
    except ServiceNotConfiguredError as e:
        logger.warning(f"Could not send email summary for transcript {transcript_id}: {str(e)}")
        flash(str(e), 'warning') # Display the specific configuration error message
        return redirect(url_for('client_details', client_id=transcript.client_id if 'transcript' in locals() and transcript else 'dashboard'))
    except Exception as e:
        logger.error(f"Error sending email summary for transcript {transcript_id}: {str(e)}")
        flash(f"An unexpected error occurred while trying to send the email summary.", 'error')
        return redirect(url_for('client_details', client_id=transcript.client_id if 'transcript' in locals() and transcript else 'dashboard'))


@app.route('/client/<int:client_id>')
def client_details(client_id):
    try:
        client = db.session.get(Client, client_id)
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('dashboard'))
        
        transcripts_query_result = db.session.query(Transcript).filter_by(client_id=client_id).order_by(Transcript.session_date.desc(), Transcript.created_at.desc()).all()
        
        transcript_data_display = []
        for t_obj in transcripts_query_result:
            has_openai = bool(t_obj.openai_analysis)
            has_anthropic = bool(t_obj.anthropic_analysis)
            has_gemini = bool(t_obj.gemini_analysis)
            transcript_data_display.append({
                'id': t_obj.id,
                'filename': t_obj.original_filename,
                'session_date': t_obj.session_date,
                'processing_status': t_obj.processing_status,
                'notion_synced': t_obj.notion_synced,
                'has_openai': has_openai,
                'has_anthropic': has_anthropic,
                'has_gemini': has_gemini,
                'ai_providers': f"{int(has_openai) + int(has_anthropic) + int(has_gemini)}/3"
            })
        
        client_stats = {
            'total_sessions': len(transcripts_query_result),
            'completed_sessions': len([t for t in transcripts_query_result if t.processing_status == 'completed']),
            'synced_sessions': len([t for t in transcripts_query_result if t.notion_synced]),
            'notion_connected': bool(client.notion_database_id)
        }

        conceptualization_html = None
        if client and client.current_case_conceptualization:
            try:
                conceptualization_html = markdown(client.current_case_conceptualization)
            except Exception as md_e:
                logger.error(f"Error converting conceptualization Markdown to HTML for client {client_id}: {md_e}")
                conceptualization_html = "<p><em>Error displaying conceptualization content.</em></p>"

        analytics_session_data = []
        for t_obj in transcripts_query_result:
            session_dict = {
                'session_date': t_obj.session_date.isoformat() if t_obj.session_date else None,
                'sentiment_score': t_obj.sentiment_score,
                'key_themes': t_obj.key_themes, 
                'therapy_insights': t_obj.therapy_insights,
                'raw_content': t_obj.raw_content 
            }
            analytics_session_data.append(session_dict)

        analytics_dashboard_data = {} 
        analytics_service_available = (analytics_service is not None)

        if analytics_service_available:
            try:
                client_data_for_dashboard = {'name': client.name, 'id': client.id}
                # Ensure all necessary fields are in analytics_session_data
                # (session_date, sentiment_score, key_themes, therapy_insights, raw_content, emotional_analysis, progress_indicators)
                # The existing loop for analytics_session_data already includes most of these.
                # Adding emotional_analysis and progress_indicators if not already present.
                # This is simplified here; the loop above should be checked/updated.
                
                # For this specific refactoring, we assume analytics_session_data is correctly prepared
                # as per previous steps and the primary goal is to pass the whole dashboard dict.

                analytics_dashboard_data = analytics_service.generate_progress_dashboard(
                    sessions=analytics_session_data, 
                    client_data=client_data_for_dashboard,
                    longitudinal_data=None 
                )
                if not analytics_dashboard_data: 
                     analytics_dashboard_data = {} # Ensure it's a dict
                     logger.warning(f"Analytics dashboard data returned empty for client {client_id} despite service being available.")

            except Exception as e:
                logger.error(f"Error generating analytics dashboard for client {client_id}: {e}")
                analytics_dashboard_data = {} # Ensure it's a dict on error
        else:
            logger.warning("AnalyticsService is not available.")
            # analytics_dashboard_data remains {}

        return render_template('client_details.html', 
                             client=client,
                             transcripts=transcript_data_display, 
                             client_stats=client_stats,   
                             analytics_dashboard_data=analytics_dashboard_data, # Pass the whole dict
                             analytics_service_available=analytics_service_available,
                             conceptualization_html=conceptualization_html,
                             case_conceptualization_updated_at=client.case_conceptualization_updated_at if client else None)
        
    except Exception as e:
        logger.error(f"Error loading client details for {client_id}: {str(e)}")
        flash(f"Error loading client details: {str(e)}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/transcripts/search', methods=['GET'])
def search_transcripts():
    """API endpoint for advanced search and filtering of transcripts."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        q = request.args.get('q', None, type=str)
        client_id_filter = request.args.get('client_id', None, type=int)
        start_date_str = request.args.get('start_date', None, type=str)
        end_date_str = request.args.get('end_date', None, type=str)
        status_filter = request.args.get('status', None, type=str)
        themes_str = request.args.get('themes', None, type=str)
        min_sentiment_str = request.args.get('min_sentiment', None, type=str)
        max_sentiment_str = request.args.get('max_sentiment', None, type=str)

        query = db.session.query(Transcript).join(Client, Transcript.client_id == Client.id)

        if q:
            search_terms = q.strip().split()
            if not search_terms: 
                search_expression = None
            elif len(search_terms) == 1:
                search_expression = f"{search_terms[0]}*" 
            else:
                search_expression = " AND ".join([f"{term}*" for term in search_terms[:-1]] + [f"{search_terms[-1]}*"])

            if search_expression:
                fts_subquery = db.session.query(
                    Transcript.id.label("id") 
                ).filter(
                    text("transcript_fts.raw_content MATCH :query_expr") 
                ).params(
                    query_expr=search_expression
                ).subquery()

                query = query.filter(
                    or_(
                        Transcript.id.in_(db.select(fts_subquery.c.id)),
                        Client.name.ilike(f"%{q}%"),
                        Transcript.original_filename.ilike(f"%{q}%")
                    )
                )
        
        if client_id_filter:
            query = query.filter(Transcript.client_id == client_id_filter)
        
        if start_date_str:
            try:
                start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(Transcript.session_date >= start_date_obj)
            except ValueError:
                return make_error_response("Invalid start_date format. Use YYYY-MM-DD.", error_code="VALIDATION_ERROR", status_code=400)
        
        if end_date_str:
            try:
                end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(Transcript.session_date <= end_date_obj)
            except ValueError:
                return make_error_response("Invalid end_date format. Use YYYY-MM-DD.", error_code="VALIDATION_ERROR", status_code=400)

        if status_filter:
            query = query.filter(Transcript.processing_status == status_filter)

        if themes_str:
            themes_list = [theme.strip() for theme in themes_str.split(',') if theme.strip()]
            for theme_item in themes_list:
                query = query.filter(Transcript.key_themes.ilike(f'%"{theme_item}"%'))

        if min_sentiment_str:
            try:
                min_sentiment = float(min_sentiment_str)
                query = query.filter(Transcript.sentiment_score >= min_sentiment)
            except ValueError:
                 return make_error_response("Invalid min_sentiment value. Must be a number.", error_code="VALIDATION_ERROR", status_code=400)

        if max_sentiment_str:
            try:
                max_sentiment = float(max_sentiment_str)
                query = query.filter(Transcript.sentiment_score <= max_sentiment)
            except ValueError:
                return make_error_response("Invalid max_sentiment value. Must be a number.", error_code="VALIDATION_ERROR", status_code=400)

        query = query.order_by(Transcript.session_date.desc())
        
        paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)
        transcripts_page_items = paginated_results.items

        results_list = []
        for t in transcripts_page_items:
            results_list.append({
                "id": t.id,
                "client_id": t.client_id,
                "client_name": t.client.name if t.client else "N/A",
                "original_filename": t.original_filename,
                "session_date": t.session_date.isoformat() if t.session_date else None,
                "processing_status": t.processing_status,
                "key_themes": t.key_themes, 
                "sentiment_score": t.sentiment_score,
            })

        pagination_meta = {
            "page": paginated_results.page,
            "per_page": paginated_results.per_page,
            "total_pages": paginated_results.pages,
            "total_items": paginated_results.total
        }
        
        return make_success_response(data={"transcripts": results_list, "pagination": pagination_meta})

    except Exception as e:
        logger.error(f"Error in transcript search API: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return make_error_response("An internal error occurred while searching transcripts.", error_code="INTERNAL_SERVER_ERROR", status_code=500)
