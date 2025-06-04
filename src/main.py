import os
import logging
import json
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import traceback

# Fix import paths for deployment compatibility
try:
    from processing_pipeline import ProcessingPipeline
except ImportError:
    from src.processing_pipeline import ProcessingPipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'therapy_transcript_processor_secret_key_2025'
app.config['API_KEYS_FILE'] = '/tmp/api_keys.json'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Global processing pipeline
pipeline = None

# Default API keys for deployment - these will be overridden by user settings
DEFAULT_API_KEYS = {
    'dropbox_token': os.environ.get('DROPBOX_TOKEN', 'placeholder_dropbox_token'),
    'openai_key': os.environ.get('OPENAI_KEY', 'placeholder_openai_key'),
    'claude_key': os.environ.get('CLAUDE_KEY', 'placeholder_claude_key'),
    'gemini_key': os.environ.get('GEMINI_KEY', 'placeholder_gemini_key'),
    'notion_key': os.environ.get('NOTION_KEY', 'placeholder_notion_key'),
    'notion_parent_id': os.environ.get('NOTION_PARENT_ID', 'placeholder_notion_parent_id'),
    'dropbox_folder': os.environ.get('DROPBOX_FOLDER', '/apps/otter')
}

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Load API keys from file or environment variables
def load_api_keys():
    try:
        if os.path.exists(app.config['API_KEYS_FILE']):
            with open(app.config['API_KEYS_FILE'], 'r') as f:
                return json.load(f)
        else:
            # Use default keys if file doesn't exist
            logger.info("API keys file not found, using default/environment keys")
            # Save default keys to file for future use
            save_api_keys(DEFAULT_API_KEYS)
            return DEFAULT_API_KEYS
    except Exception as e:
        logger.error(f"Error loading API keys: {str(e)}")
        logger.error(traceback.format_exc())
        # Return default keys if there's an error
        return DEFAULT_API_KEYS

# Save API keys to file
def save_api_keys(keys):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(app.config['API_KEYS_FILE']), exist_ok=True)
        
        # Write keys to file
        with open(app.config['API_KEYS_FILE'], 'w') as f:
            json.dump(keys, f)
        return True
    except Exception as e:
        logger.error(f"Error saving API keys: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Initialize or update processing pipeline
def init_pipeline():
    global pipeline
    api_keys = load_api_keys()
    
    # Always initialize pipeline with available keys
    try:
        if pipeline is None:
            pipeline = ProcessingPipeline(api_keys)
            logger.info("Processing pipeline initialized successfully")
        else:
            # Update pipeline with new keys
            pipeline.config = api_keys
            if hasattr(pipeline, 'dropbox') and pipeline.dropbox is not None:
                pipeline.dropbox = pipeline.dropbox.__class__(
                    access_token=api_keys.get('dropbox_token', ''),
                    folder_path=api_keys.get('dropbox_folder', '/apps/otter')
                )
            if hasattr(pipeline, 'ai_processor') and pipeline.ai_processor is not None:
                pipeline.ai_processor = pipeline.ai_processor.__class__(
                    openai_key=api_keys.get('openai_key', ''),
                    claude_key=api_keys.get('claude_key', ''),
                    gemini_key=api_keys.get('gemini_key', '')
                )
            if hasattr(pipeline, 'notion') and pipeline.notion is not None:
                pipeline.notion = pipeline.notion.__class__(
                    api_key=api_keys.get('notion_key', ''),
                    parent_page_id=api_keys.get('notion_parent_id', '')
                )
            logger.info("Processing pipeline updated successfully")
        
        # Check if we have real keys (not placeholders)
        has_real_keys = (
            not api_keys.get('dropbox_token', '').startswith('placeholder_') and
            (not api_keys.get('openai_key', '').startswith('placeholder_') or 
             not api_keys.get('claude_key', '').startswith('placeholder_') or 
             not api_keys.get('gemini_key', '').startswith('placeholder_')) and
            not api_keys.get('notion_key', '').startswith('placeholder_') and
            not api_keys.get('notion_parent_id', '').startswith('placeholder_')
        )
        
        return has_real_keys
    except Exception as e:
        logger.error(f"Error initializing pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Load API keys on startup
API_KEYS = load_api_keys()
try:
    init_pipeline()
except Exception as e:
    logger.error(f"Error initializing pipeline on startup: {str(e)}")
    logger.error(traceback.format_exc())

# Simple authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '5786':
            session['authenticated'] = True
            logger.info("User logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid password', 'error')
            logger.warning("Failed login attempt with incorrect password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('login'))

# Dashboard
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        logger.warning("Unauthenticated access attempt to dashboard")
        return redirect(url_for('login'))
    
    # Get pipeline status
    status = {"is_running": False, "processed_files": 0, "failed_files": 0}
    if pipeline:
        try:
            status = pipeline.get_status()
            logger.debug("Retrieved pipeline status successfully")
        except Exception as e:
            logger.error(f"Error getting pipeline status: {str(e)}")
            logger.error(traceback.format_exc())
            flash("Error retrieving pipeline status. Please check the logs.", "error")
    
    # Check if using placeholder keys
    using_placeholders = False
    for key, value in API_KEYS.items():
        if isinstance(value, str) and value.startswith('placeholder_'):
            using_placeholders = True
            break
    
    if using_placeholders:
        flash("You are using placeholder API keys. Please configure your real API keys in the Settings page.", "warning")
    
    return render_template('dashboard.html', status=status, api_keys=API_KEYS)

# API Keys settings
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global API_KEYS
    
    if not session.get('authenticated'):
        logger.warning("Unauthenticated access attempt to settings")
        return redirect(url_for('login'))
    
    # Handle form submission
    if request.method == 'POST':
        try:
            # Update API keys with form data
            updated_keys = {
                'dropbox_token': request.form.get('dropbox_token', ''),
                'openai_key': request.form.get('openai_key', ''),
                'claude_key': request.form.get('claude_key', ''),
                'gemini_key': request.form.get('gemini_key', ''),
                'notion_key': request.form.get('notion_key', ''),
                'notion_parent_id': request.form.get('notion_parent_id', ''),
                'dropbox_folder': request.form.get('dropbox_folder', '/apps/otter')
            }
            
            # Only update keys that were provided (not empty)
            for key, value in updated_keys.items():
                if value:  # Only update if a value was provided
                    API_KEYS[key] = value
            
            # Save updated keys
            if save_api_keys(API_KEYS):
                # Update pipeline with new keys
                try:
                    if init_pipeline():
                        flash('API keys saved successfully and pipeline updated!', 'success')
                        logger.info("API keys saved and pipeline updated successfully")
                    else:
                        flash('API keys saved, but some required keys are missing for full functionality.', 'warning')
                        logger.warning("API keys saved but missing some required keys")
                except Exception as e:
                    logger.error(f"Error initializing pipeline after key update: {str(e)}")
                    logger.error(traceback.format_exc())
                    flash(f'API keys saved, but error initializing pipeline: {str(e)}', 'warning')
            else:
                flash('Error saving API keys. Please try again.', 'error')
                logger.error("Failed to save API keys")
        except Exception as e:
            logger.error(f"Unexpected error in settings POST: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f'An unexpected error occurred: {str(e)}', 'error')
        
        return redirect(url_for('settings'))
    
    return render_template('api_keys.html', api_keys=API_KEYS)

# Upload page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('authenticated'):
        logger.warning("Unauthenticated access attempt to upload")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Check if the post request has the file part
            if 'transcript' not in request.files:
                flash('No file part in the request', 'error')
                logger.warning("Upload attempted with no file part")
                return redirect(request.url)
            
            file = request.files['transcript']
            
            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file', 'error')
                logger.warning("Upload attempted with no selected file")
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                try:
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
                        file_path = temp.name
                        file.save(file_path)
                    
                    filename = secure_filename(file.filename)
                    logger.info(f"File uploaded: {filename}")
                    
                    # Check if pipeline is initialized
                    if not pipeline:
                        try:
                            if not init_pipeline():
                                flash('Processing pipeline not initialized. Please configure API keys first.', 'error')
                                logger.error("Upload attempted but pipeline not initialized")
                                try:
                                    os.unlink(file_path)
                                    logger.debug(f"Temporary file removed: {file_path}")
                                except Exception as e:
                                    logger.error(f"Error removing temporary file: {str(e)}")
                                return redirect(url_for('settings'))
                        except Exception as e:
                            logger.error(f"Error initializing pipeline during upload: {str(e)}")
                            logger.error(traceback.format_exc())
                            flash(f'Error initializing pipeline: {str(e)}', 'error')
                            try:
                                os.unlink(file_path)
                                logger.debug(f"Temporary file removed: {file_path}")
                            except Exception as e:
                                logger.error(f"Error removing temporary file: {str(e)}")
                            return redirect(url_for('settings'))
                    
                    # Check for placeholder keys
                    using_placeholders = False
                    for key, value in API_KEYS.items():
                        if isinstance(value, str) and value.startswith('placeholder_'):
                            using_placeholders = True
                            break
                    
                    if using_placeholders:
                        flash("Cannot process files with placeholder API keys. Please configure your real API keys in the Settings page.", "error")
                        try:
                            os.unlink(file_path)
                            logger.debug(f"Temporary file removed: {file_path}")
                        except Exception as e:
                            logger.error(f"Error removing temporary file: {str(e)}")
                        return redirect(url_for('settings'))
                    
                    # Process the file
                    try:
                        logger.info(f"Processing file: {filename}")
                        result = pipeline.process_single_file(file_path)
                    except Exception as e:
                        logger.error(f"Error processing file {filename}: {str(e)}")
                        logger.error(traceback.format_exc())
                        result = {
                            "success": False,
                            "error": str(e),
                            "client_name": "Unknown"
                        }
                    
                    # Clean up the temporary file
                    try:
                        os.unlink(file_path)
                        logger.debug(f"Temporary file removed: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing temporary file: {str(e)}")
                    
                    if result.get("success", False):
                        flash(f'Successfully processed transcript for {result.get("client_name", "Unknown")} and saved to Notion!', 'success')
                        logger.info(f"Successfully processed transcript for {result.get('client_name', 'Unknown')}")
                        # Store processing result in session for display
                        session['last_processed'] = {
                            'client_name': result.get("client_name", "Unknown"),
                            'filename': filename,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'notion_url': result.get('notion_url', '#'),
                            'service_used': result.get('service_used', 'unknown')
                        }
                    else:
                        error_msg = result.get("error", "Unknown error")
                        flash(f'Error processing file: {error_msg}', 'error')
                        logger.error(f"Error processing file {filename}: {error_msg}")
                    
                    return redirect(url_for('upload'))
                
                except Exception as e:
                    logger.error(f"Error processing file: {str(e)}")
                    logger.error(traceback.format_exc())
                    flash(f'Error processing file: {str(e)}', 'error')
                    return redirect(request.url)
            else:
                flash('File type not allowed. Please upload a PDF file.', 'error')
                logger.warning(f"Upload attempted with invalid file type: {file.filename}")
                return redirect(request.url)
        except Exception as e:
            logger.error(f"Unexpected error in upload: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f'An unexpected error occurred: {str(e)}', 'error')
            return redirect(request.url)
    
    # For GET request, show the upload form
    last_processed = session.get('last_processed', None)
    return render_template('upload.html', last_processed=last_processed, api_keys=API_KEYS)

# Check Dropbox route
@app.route('/check_dropbox', methods=['POST'])
def check_dropbox():
    if not session.get('authenticated'):
        logger.warning("Unauthenticated access attempt to check_dropbox")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        # Check if pipeline is initialized
        if not pipeline:
            try:
                if not init_pipeline():
                    logger.error("Check Dropbox attempted but pipeline not initialized")
                    return jsonify({
                        "success": False,
                        "error": "Processing pipeline not initialized. Please configure API keys first."
                    }), 400
            except Exception as e:
                logger.error(f"Error initializing pipeline during check_dropbox: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    "success": False,
                    "error": f"Error initializing pipeline: {str(e)}"
                }), 500
        
        # Check for placeholder keys
        using_placeholders = False
        for key, value in API_KEYS.items():
            if isinstance(value, str) and value.startswith('placeholder_'):
                using_placeholders = True
                break
        
        if using_placeholders:
            return jsonify({
                "success": False,
                "error": "Cannot check Dropbox with placeholder API keys. Please configure your real API keys in the Settings page."
            }), 400
        
        # Check Dropbox for new files
        try:
            logger.info("Checking Dropbox for new files")
            result = pipeline.check_dropbox()
            logger.info(f"Dropbox check result: {result}")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error checking Dropbox: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "error": f"Error checking Dropbox: {str(e)}"
            }), 500
    except Exception as e:
        logger.error(f"Unexpected error in check_dropbox: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

# Start/Stop monitoring
@app.route('/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    if not session.get('authenticated'):
        logger.warning("Unauthenticated access attempt to toggle_monitoring")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        # Check if pipeline is initialized
        if not pipeline:
            try:
                if not init_pipeline():
                    logger.error("Toggle monitoring attempted but pipeline not initialized")
                    return jsonify({
                        "success": False,
                        "error": "Processing pipeline not initialized. Please configure API keys first."
                    }), 400
            except Exception as e:
                logger.error(f"Error initializing pipeline during toggle_monitoring: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    "success": False,
                    "error": f"Error initializing pipeline: {str(e)}"
                }), 500
        
        # Check for placeholder keys
        using_placeholders = False
        for key, value in API_KEYS.items():
            if isinstance(value, str) and value.startswith('placeholder_'):
                using_placeholders = True
                break
        
        if using_placeholders:
            return jsonify({
                "success": False,
                "error": "Cannot monitor Dropbox with placeholder API keys. Please configure your real API keys in the Settings page."
            }), 400
        
        # Toggle monitoring
        try:
            if pipeline.is_running:
                logger.info("Stopping Dropbox monitoring")
                pipeline.stop_monitoring()
                return jsonify({
                    "success": True,
                    "is_running": False,
                    "message": "Dropbox monitoring stopped"
                })
            else:
                logger.info("Starting Dropbox monitoring")
                pipeline.start_monitoring()
                return jsonify({
                    "success": True,
                    "is_running": True,
                    "message": "Dropbox monitoring started"
                })
        except Exception as e:
            logger.error(f"Error toggling monitoring: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "error": f"Error toggling monitoring: {str(e)}"
            }), 500
    except Exception as e:
        logger.error(f"Unexpected error in toggle_monitoring: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

# Get pipeline status
@app.route('/status', methods=['GET'])
def get_status():
    if not session.get('authenticated'):
        logger.warning("Unauthenticated access attempt to status")
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        # Check if pipeline is initialized
        if not pipeline:
            logger.info("Status check with uninitialized pipeline")
            return jsonify({
                "success": True,
                "is_running": False,
                "initialized": False,
                "message": "Processing pipeline not initialized"
            })
        
        # Get status
        try:
            logger.debug("Getting pipeline status")
            status = pipeline.get_status()
            status["success"] = True
            status["initialized"] = True
            
            # Add placeholder status
            using_placeholders = False
            for key, value in API_KEYS.items():
                if isinstance(value, str) and value.startswith('placeholder_'):
                    using_placeholders = True
                    break
            
            status["using_placeholders"] = using_placeholders
            
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "error": f"Error getting status: {str(e)}"
            }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_status: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 error: {request.path}")
    return render_template('error.html', error="Page not found", message="The page you requested could not be found."), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 error: {str(e)}")
    return render_template('error.html', error="Internal Server Error", message="An unexpected error occurred. Please try again later."), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning(f"413 error: File too large")
    return render_template('error.html', error="File Too Large", message="The file you tried to upload is too large. Maximum size is 16MB."), 413

# Make templates folder available
@app.context_processor
def inject_template_scope():
    injections = dict()
    injections.update(app.config)
    return injections
