# Therapy Transcript Processor - Deployment Documentation

## Application Overview
The Therapy Transcript Processor is a fully functional web application that automates the processing of therapy session transcripts. It connects Dropbox, OpenAI, Claude, Gemini, and Notion to create a seamless workflow for processing and organizing therapy session notes.

## Architecture
The application consists of several key components:

1. **Web Interface**: A Flask-based web application providing user authentication, file upload, API key configuration, and status monitoring.

2. **Dropbox Integration**: Real-time monitoring of a specified Dropbox folder (`/apps/otter` by default) for new PDF transcripts using the Dropbox API.

3. **PDF Processing**: Extraction of text content from PDF files using PyPDF2.

4. **AI Processing**: Analysis of transcript text using OpenAI (GPT-4), Claude, or Gemini, with intelligent fallback between services.

5. **Notion Integration**: Automatic creation of client-specific databases and organization of processed notes in Notion.

## Directory Structure
```
full_integration_app/
├── app.py                  # Entry point for the application
├── requirements.txt        # Python dependencies
├── src/
│   ├── ai_processor.py     # AI service integration
│   ├── dropbox_direct_api.py # Dropbox API integration
│   ├── main.py             # Flask application routes and logic
│   ├── notion_integration.py # Notion API integration
│   ├── pdf_extractor.py    # PDF text extraction
│   ├── processing_pipeline.py # Main processing workflow
│   └── templates/          # HTML templates for web interface
├── test_files/             # Sample files for testing
├── uploads/                # Temporary storage for uploaded files
└── venv/                   # Python virtual environment
```

## Authentication
- Login with password: `5786`
- All pages require authentication
- Session-based authentication with secure cookie storage

## Features
1. **Dashboard**: Monitor processing status and recent activity
2. **Upload**: Manually upload PDF transcripts for processing
3. **Settings**: Configure API keys for all integrated services
4. **Dropbox Integration**: Automatically process transcripts from the `/apps/otter` folder

## API Integration
The application integrates with the following services:
- **Dropbox**: For accessing and monitoring transcript files
- **OpenAI**: Primary AI for transcript processing
- **Claude**: Secondary AI for processing and fallback
- **Gemini**: Tertiary AI for processing and fallback
- **Notion**: For storing and organizing processed transcripts

## Configuration
To configure the application:
1. Log in using the password
2. Navigate to the Settings page
3. Enter your API keys for each service
4. Click "Save API Keys" to store them securely
5. You will receive confirmation when keys are saved successfully

## API Keys
The application requires the following API keys:
- **Dropbox Token**: For accessing files in your Dropbox account
- **OpenAI API Key**: For processing transcripts with GPT-4
- **Claude API Key**: For processing transcripts with Claude (alternative)
- **Gemini API Key**: For processing transcripts with Gemini (alternative)
- **Notion API Key**: For creating and updating databases
- **Notion Parent Page ID**: The ID of the parent page where client databases will be created

All API keys are stored securely on the server and are not exposed in client-side code. The application includes persistent storage for API keys, so they remain available between sessions.

## Workflow Process
1. **File Detection**: Transcripts are uploaded manually through the web interface or detected in the Dropbox folder
2. **Text Extraction**: The system extracts text from the PDF files using PyPDF2
3. **Client Identification**: Client name is identified from the filename or transcript content
4. **AI Processing**: The transcript is processed using the configured AI models with the therapy note prompt
5. **Database Creation**: If a database doesn't exist for the client, one is created automatically in Notion
6. **Note Storage**: Results are stored in the client's Notion database with proper formatting and metadata

## Technical Details
- **Framework**: Flask (Python)
- **Authentication**: Session-based with secure cookies
- **Data Storage**: Secure file-based storage for API keys
- **File Handling**: Secure temporary file storage for uploads
- **Deployment**: Serverless platform with automatic scaling
- **Security**: HTTPS encryption, password protection, secure API key storage

## Error Handling
The application includes comprehensive error handling:
- **Custom Error Pages**: User-friendly pages for 404, 500, and 413 errors
- **Detailed Logging**: All operations are logged with appropriate detail levels
- **Graceful Degradation**: The system attempts to continue operation even when some services fail
- **User Feedback**: Clear error messages are displayed to users when issues occur
- **API Error Handling**: Robust handling of authentication and API errors from all integrated services

## Maintenance
The application is designed to run with minimal maintenance:
- Regular checks of the logs are recommended to ensure proper functioning
- API keys should be updated if they expire or are revoked
- The Dropbox folder should be monitored occasionally to ensure files are being processed

## Troubleshooting
If you encounter issues:

1. **API Key Issues**:
   - Verify all API keys are correctly configured in the Settings page
   - Check that the Notion parent page ID is correct and accessible
   - Ensure your Dropbox token has the necessary permissions

2. **File Processing Issues**:
   - Ensure PDF files are in a readable format and under 16MB
   - Check that filenames follow expected patterns for client name extraction
   - Verify the Dropbox folder path is correct (`/apps/otter` by default)

3. **Notion Database Issues**:
   - Confirm the parent page exists and is accessible to the integration
   - Check that your Notion API key has the necessary permissions
   - Verify that the integration has been added to the parent page

4. **Application Errors**:
   - Check the application logs for detailed error information
   - Restart the application if it becomes unresponsive
   - Clear browser cache and cookies if the web interface behaves unexpectedly

## Testing
The application includes several test scripts to validate functionality:

- `test_dropbox.py`: Tests Dropbox API integration
- `test_pdf_and_ai.py`: Tests PDF extraction and AI processing
- `test_notion.py`: Tests Notion database creation and updates
- `validate_pipeline.py`: End-to-end validation of the entire processing pipeline

These scripts can be run to diagnose issues or verify functionality after configuration changes.

## Deployment
The application is deployed using a serverless platform that provides a permanent URL. The deployment process:

1. Ensures all dependencies are installed from `requirements.txt`
2. Sets up the necessary environment variables
3. Configures the web server to handle Flask applications
4. Establishes secure HTTPS connections
5. Provides automatic scaling based on demand

## Support
For additional support or questions, please contact the developer.
