from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Client, Transcript, ProcessingLog, SystemSettings
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from services.analytics_service import AnalyticsService
from services.emotional_analysis import EmotionalAnalysis
# VisualizationService has been removed - using AnalyticsService instead
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
    # Import ManualUploadService
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
        # Always return valid structure
        return jsonify(default_response), 200

@app.route('/api/manual-scan', methods=['POST'])
def manual_scan():
    """Manually trigger a Dropbox scan"""
    try:
        if not dropbox_service:
            return jsonify({'error': 'Dropbox service not available'}), 503

        # Get list of already processed files
        try:
            processed_files = [t.dropbox_path for t in db.session.query(Transcript).all() if t.dropbox_path]
        except Exception as e:
            logger.error(f"Error getting processed files: {str(e)}")
            processed_files = []

        # Scan for new files
        new_files = dropbox_service.scan_for_new_files(processed_files)

        if new_files is None:
            new_files = []

        # If new files found, trigger processing
        if new_files:
            try:
                from scheduler import process_new_files
                # Process files in background
                import threading
                thread = threading.Thread(target=process_new_files)
                thread.daemon = True
                thread.start()

                return jsonify({
                    'message': f'Scan completed. Found {len(new_files)} new files. Processing started.',
                    'new_files': [f.get('name', 'Unknown') for f in new_files] if new_files else []
                })
            except Exception as e:
                logger.error(f"Error starting background processing: {str(e)}")
                return jsonify({
                    'message': f'Scan completed. Found {len(new_files)} new files.',
                    'new_files': [f.get('name', 'Unknown') for f in new_files] if new_files else []
                })
        else:
            return jsonify({
                'message': 'Scan completed. No new files found.',
                'new_files': []
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
        # Always return empty array, never an object
        return jsonify([]), 200

@app.route('/api/scan-dropbox', methods=['POST'])
def scan_dropbox():
    """Alternative endpoint for Dropbox scanning"""
    try:
        if not dropbox_service:
            return jsonify({'error': 'Dropbox service not available'}), 503

        # Get list of already processed files
        try:
            processed_files = [t.dropbox_path for t in db.session.query(Transcript).all() if t.dropbox_path]
        except Exception as e:
            logger.error(f"Error getting processed files: {str(e)}")
            processed_files = []

        # Scan for new files
        new_files = dropbox_service.scan_for_new_files(processed_files)

        if new_files is None:
            new_files = []

        return jsonify({
            'success': True,
            'message': f'Scan completed. Found {len(new_files)} new files.',
            'new_files_count': len(new_files),
            'new_files': [f.get('name', 'Unknown') for f in new_files] if new_files else []
        })

    except Exception as e:
        logger.error(f"Error in scan-dropbox endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-dropbox', methods=['POST'])
def test_dropbox():
    """Test Dropbox connection and return detailed status"""
    try:
        if not dropbox_service:
            return jsonify({
                'success': False,
                'error': 'Dropbox service not initialized',
                'details': 'Check Dropbox access token configuration'
            }), 503

        # Test connection
        connection_test = dropbox_service.test_connection()

        if not connection_test:
            return jsonify({
                'success': False,
                'error': 'Dropbox connection failed',
                'details': 'Authentication or network issue'
            }), 400

        # Get account info
        try:
            account = dropbox_service.client.users_get_current_account()
            account_name = account.name.display_name
        except Exception as e:
            account_name = 'Unknown'
            logger.warning(f"Could not get account name: {str(e)}")

        # Test folder access
        try:
            all_files = dropbox_service.list_files()
            folder_status = f"Monitoring folder: {dropbox_service.monitor_folder}"
            files_count = len(all_files)
        except Exception as e:
            folder_status = f"Error accessing folder: {str(e)}"
            files_count = 0

        return jsonify({
            'success': True,
            'account_name': account_name,
            'folder_status': folder_status,
            'files_found': files_count,
            'monitor_folder': dropbox_service.monitor_folder,
            'connection_timestamp': datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error testing Dropbox: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'details': 'Unexpected error during Dropbox test'
        }), 500

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
    """Dynamic longitudinal visualization dashboard for specific client"""
    try:
        client = db.session.get(Client, client_id)
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('dashboard'))

        # Get all transcripts for this client
        transcripts = Transcript.query.filter_by(client_id=client_id).order_by(Transcript.session_date).all()

        if not transcripts:
            flash('No session data available for visualization', 'info')
            return redirect(url_for('client_detail', client_id=client_id))

        # Generate longitudinal emotional data
        session_data = []
        for transcript in transcripts:
            # Extract emotional analysis if available
            emotional_data = None
            if hasattr(transcript, 'emotional_analysis') and transcript.emotional_analysis:
                try:
                    emotional_data = json.loads(transcript.emotional_analysis) if isinstance(transcript.emotional_analysis, str) else transcript.emotional_analysis
                except json.JSONDecodeError:
                    emotional_data = None

            session_data.append({
                'transcript_id': transcript.id,
                'session_date': transcript.session_date.isoformat() if transcript.session_date else None,
                'emotional_analysis': emotional_data,
                'ai_analysis': {
                    'openai_analysis': transcript.openai_analysis,
                    'anthropic_analysis': transcript.anthropic_analysis,
                    'gemini_analysis': transcript.gemini_analysis
                }
            })

        # Generate visualization dashboard using analytics service
        if analytics_service:
            client_data = {'name': client.name, 'id': client.id}
            dashboard_data = analytics_service.generate_progress_dashboard(
                sessions=session_data,
                client_data=client_data,
                longitudinal_data=longitudinal_emotions
            )
        else:
            dashboard_data = {'error': 'Analytics service unavailable'}

        # Generate longitudinal emotional analysis
        if emotional_analyzer:
            longitudinal_emotions = emotional_analyzer.generate_longitudinal_emotional_data(session_data)
        else:
            longitudinal_emotions = {'error': 'Emotional analysis service unavailable'}

        return render_template('client_visualization.html', 
                             client=client, 
                             dashboard_data=dashboard_data,
                             longitudinal_emotions=longitudinal_emotions,
                             session_count=len(transcripts))

    except Exception as e:
        logger.error(f"Error generating client visualization: {str(e)}")
        flash(f"Error generating visualization: {str(e)}", 'error')
        return redirect(url_for('client_detail', client_id=client_id))

@app.route('/transcript/<int:transcript_id>/adaptive-colors')
def adaptive_color_ui(transcript_id):
    """Adaptive color therapy UI based on emotional analysis"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            flash('Transcript not found', 'error')
            return redirect(url_for('dashboard'))

        # Get or generate emotional analysis
        emotional_data = None
        if hasattr(transcript, 'emotional_analysis') and transcript.emotional_analysis:
            try:
                emotional_data = json.loads(transcript.emotional_analysis) if isinstance(transcript.emotional_analysis, str) else transcript.emotional_analysis
            except json.JSONDecodeError:
                emotional_data = None

        # If no emotional analysis exists, generate it
        if not emotional_data and emotional_analyzer and transcript.raw_content:
            ai_analysis = {
                'openai_analysis': transcript.openai_analysis,
                'anthropic_analysis': transcript.anthropic_analysis,
                'gemini_analysis': transcript.gemini_analysis
            }
            emotional_data = emotional_analyzer.analyze_session_emotions(transcript.raw_content, ai_analysis)

            # Save emotional analysis to transcript (if column exists)
            try:
                transcript.emotional_analysis = json.dumps(emotional_data)
                db.session.commit()
            except Exception as e:
                logger.warning(f"Could not save emotional analysis: {str(e)}")

        if not emotional_data:
            emotional_data = {
                'primary_emotion': 'neutral',
                'intensity': 0.5,
                'color_palette': {
                    'primary': '#8E9AAF',
                    'background': '#F8F9FA',
                    'text': '#2C3E50'
                }
            }

        return render_template('adaptive_color_ui.html', 
                             transcript=transcript,
                             emotional_data=emotional_data)

    except Exception as e:
        logger.error(f"Error loading adaptive color UI: {str(e)}")
        flash(f"Error loading adaptive interface: {str(e)}", 'error')
        return redirect(url_for('transcript_detail', transcript_id=transcript_id))

@app.route('/send_email_summary/<int:transcript_id>', methods=['POST'])
def send_email_summary(transcript_id):
    """One-button email export for therapy session summaries"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            flash('Transcript not found', 'error')
            return redirect(url_for('dashboard'))

        # Get recipient email from form
        recipient_email = request.form.get('recipient_email')
        if not recipient_email:
            flash('Recipient email is required', 'error')
            return redirect(url_for('client_details', client_id=transcript.client_id))

        # Check if SendGrid API key is available
        import os
        if not os.environ.get('SENDGRID_API_KEY'):
            flash('Email service not configured. Please contact administrator.', 'error')
            return redirect(url_for('client_details', client_id=transcript.client_id))

        # Initialize email summary service
        from services.email_summary_service import EmailSummaryService
        email_service = EmailSummaryService()

        # Prepare transcript data for summary generation
        transcript_data = {
            'client_name': transcript.client.name,
            'session_date': transcript.session_date.strftime('%B %d, %Y') if transcript.session_date else 'Unknown Date',
            'original_filename': transcript.original_filename,
            'openai_analysis': transcript.openai_analysis,
            'anthropic_analysis': transcript.anthropic_analysis,
            'gemini_analysis': transcript.gemini_analysis
        }

        # Generate and send email summary
        success = email_service.process_and_send_summary(transcript_data, recipient_email)

        if success:
            flash(f'Session summary emailed successfully to {recipient_email}', 'success')
        else:
            flash('Failed to send email summary. Please check email configuration.', 'error')

        return redirect(url_for('client_details', client_id=transcript.client_id))

    except Exception as e:
        logger.error(f"Error sending email summary: {str(e)}")
        flash(f"Error sending email summary: {str(e)}", 'error')
        return redirect(url_for('transcript_detail', transcript_id=transcript_id))

@app.route('/client/<int:client_id>')
def client_details(client_id):
    """Show detailed view of a specific client and their sessions"""
    try:
        # Get client
        client = db.session.get(Client, client_id)
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('dashboard'))

        # Get all transcripts for this client - ordered chronologically (newest first)
        transcripts = db.session.query(Transcript).filter_by(client_id=client_id).order_by(Transcript.session_date.desc(), Transcript.created_at.desc()).all()

        # Calculate statistics
        total_sessions = len(transcripts)
        completed_sessions = len([t for t in transcripts if t.processing_status == 'completed'])
        synced_sessions = len([t for t in transcripts if t.notion_synced])

        # Prepare transcript data with analysis status
        transcript_data = []
        for transcript in transcripts:
            has_openai = bool(transcript.openai_analysis)
            has_anthropic = bool(transcript.anthropic_analysis)
            has_gemini = bool(transcript.gemini_analysis)

            transcript_data.append({
                'id': transcript.id,
                'filename': transcript.original_filename,
                'session_date': transcript.session_date,
                'processing_status': transcript.processing_status,
                'notion_synced': transcript.notion_synced,
                'has_openai': has_openai,
                'has_anthropic': has_anthropic,
                'has_gemini': has_gemini,
                'ai_providers': f"{int(has_openai) + int(has_anthropic) + int(has_gemini)}/3"
            })

        client_stats = {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'synced_sessions': synced_sessions,
            'notion_connected': bool(client.notion_database_id)
        }

        return render_template('client_details.html', 
                             client=client,
                             transcripts=transcript_data,
                             client_stats=client_stats)

    except Exception as e:
        logger.error(f"Error loading client details: {str(e)}")
        flash(f"Error loading client details: {str(e)}", 'error')
        return redirect(url_for('dashboard'))