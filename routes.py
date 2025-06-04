from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Client, Transcript, ProcessingLog, SystemSettings
from services.dropbox_service import DropboxService
from services.ai_service import AIService
from services.notion_service import NotionService
from services.analytics_service import AnalyticsService
from services.emotional_analysis import EmotionalAnalysis
from services.visualization_service import VisualizationService
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
    visualization_service = VisualizationService()
    email_summary_service = EmailSummaryService()
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    dropbox_service = None
    ai_service = None
    notion_service = None
    analytics_service = None
    emotional_analyzer = None
    visualization_service = None
    email_summary_service = None

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

@app.route('/api/system-stats')
def api_system_stats():
    """API endpoint for system statistics"""
    try:
        # Get system statistics
        total_clients = db.session.query(Client).count()
        total_transcripts = db.session.query(Transcript).count()
        pending_transcripts = db.session.query(Transcript)\
            .filter(Transcript.processing_status == 'pending').count()
        failed_transcripts = db.session.query(Transcript)\
            .filter(Transcript.processing_status == 'failed').count()
        
        system_stats = {
            'total_clients': total_clients,
            'total_transcripts': total_transcripts,
            'pending_processing': pending_transcripts,
            'failed_processing': failed_transcripts
        }
        
        return jsonify({'system_stats': system_stats})
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload and process therapy transcript files manually"""
    import tempfile
    import os
    from werkzeug.utils import secure_filename
    
    # Import the uploaded processing pipeline
    try:
        from src.processing_pipeline import ProcessingPipeline
    except ImportError:
        flash('Processing pipeline not available', 'error')
        return render_template('upload.html')
    
    if request.method == 'POST':
        if 'transcript' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['transcript']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Check file type
        allowed_extensions = {'pdf', 'txt', 'docx'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            flash('Invalid file type. Please upload PDF, TXT, or DOCX files.', 'error')
            return redirect(request.url)
        
        try:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
                file_path = temp.name
                file.save(file_path)
            
            filename = secure_filename(file.filename)
            logger.info(f"Processing uploaded file: {filename}")
            
            # Initialize processing pipeline with API keys
            api_keys = {
                'dropbox_token': os.environ.get('DROPBOX_ACCESS_TOKEN'),
                'openai_key': os.environ.get('OPENAI_API_KEY'),
                'claude_key': os.environ.get('ANTHROPIC_API_KEY'),
                'gemini_key': os.environ.get('GEMINI_API_KEY'),
                'notion_key': os.environ.get('NOTION_INTEGRATION_SECRET'),
                'notion_parent_id': os.environ.get('NOTION_DATABASE_ID'),
                'dropbox_folder': '/apps/otter'
            }
            
            pipeline = ProcessingPipeline(api_keys)
            result = pipeline.process_single_file(file_path)
            
            # Clean up temp file
            try:
                os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error removing temp file: {str(e)}")
            
            if result.get("success", False):
                # Create client record if it doesn't exist
                client_name = result.get("client_name", "Unknown")
                client = Client.query.filter_by(name=client_name).first()
                if not client:
                    client = Client(name=client_name)
                    db.session.add(client)
                    db.session.commit()
                
                # Create transcript record
                transcript = Transcript(
                    client_id=client.id,
                    original_filename=filename,
                    dropbox_path=f"manual_upload/{filename}",
                    file_type=filename.rsplit('.', 1)[1].lower(),
                    raw_content=result.get("content", ""),
                    processing_status='completed',
                    processed_at=datetime.now(timezone.utc),
                    notion_synced=result.get("notion_url") is not None
                )
                db.session.add(transcript)
                db.session.commit()
                
                flash(f'Successfully processed transcript for {client_name}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Error processing file: {result.get("error", "Unknown error")}', 'error')
                
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            flash(f'Error processing file: {str(e)}', 'error')
    
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
        
        # Generate visualization dashboard
        if visualization_service:
            client_data = {'name': client.name, 'id': client.id}
            dashboard_data = visualization_service.generate_longitudinal_dashboard(client_data, session_data)
        else:
            dashboard_data = {'error': 'Visualization service unavailable'}
        
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

@app.route('/transcript/<int:transcript_id>/email-summary', methods=['GET', 'POST'])
def email_summary(transcript_id):
    """Generate and send email summary for session review"""
    try:
        transcript = db.session.get(Transcript, transcript_id)
        if not transcript:
            flash('Transcript not found', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            recipient_email = request.form.get('recipient_email')
            smtp_username = request.form.get('smtp_username')
            smtp_password = request.form.get('smtp_password')
            
            if not all([recipient_email, smtp_username, smtp_password]):
                flash('All email fields are required', 'error')
                return redirect(url_for('email_summary', transcript_id=transcript_id))
            
            # Generate email summary
            if email_summary_service:
                summary_data = email_summary_service.create_summary_for_transcript(transcript_id)
                
                if summary_data:
                    # Send email
                    success = email_summary_service.send_email_summary(
                        summary_data, recipient_email, smtp_username, smtp_password
                    )
                    
                    if success:
                        flash('Email summary sent successfully', 'success')
                    else:
                        flash('Failed to send email summary', 'error')
                else:
                    flash('Failed to generate email summary', 'error')
            else:
                flash('Email service unavailable', 'error')
            
            return redirect(url_for('transcript_detail', transcript_id=transcript_id))
        
        # GET request - show email form with preview
        if email_summary_service:
            summary_data = email_summary_service.create_summary_for_transcript(transcript_id)
            if summary_data:
                email_preview = email_summary_service.format_email_summary(summary_data)
            else:
                email_preview = "Unable to generate email preview"
        else:
            summary_data = None
            email_preview = "Email service unavailable"
        
        return render_template('email_summary.html', 
                             transcript=transcript,
                             email_preview=email_preview,
                             summary_data=summary_data)
        
    except Exception as e:
        logger.error(f"Error with email summary: {str(e)}")
        flash(f"Error with email summary: {str(e)}", 'error')
        return redirect(url_for('transcript_detail', transcript_id=transcript_id))
