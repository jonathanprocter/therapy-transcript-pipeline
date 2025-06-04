from app import db
from datetime import datetime, timezone
from sqlalchemy import Text, DateTime, Float, Integer, String, Boolean, JSON

class Client(db.Model):
    """Model for tracking therapy clients"""
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False)
    notion_database_id = db.Column(String(255), unique=True)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship to transcripts
    transcripts = db.relationship('Transcript', backref='client', lazy=True, cascade='all, delete-orphan')

class Transcript(db.Model):
    """Model for storing processed transcripts"""
    id = db.Column(Integer, primary_key=True)
    client_id = db.Column(Integer, db.ForeignKey('client.id'), nullable=False)
    
    # File information
    original_filename = db.Column(String(255), nullable=False)
    dropbox_path = db.Column(String(500), nullable=False)
    file_type = db.Column(String(50), nullable=False)  # pdf, txt, docx
    
    # Content
    raw_content = db.Column(Text, nullable=False)
    session_date = db.Column(DateTime)
    
    # Processing status
    processing_status = db.Column(String(50), default='pending')  # pending, processing, completed, failed
    processed_at = db.Column(DateTime)
    
    # AI Analysis results
    openai_analysis = db.Column(JSON)
    anthropic_analysis = db.Column(JSON)
    gemini_analysis = db.Column(JSON)
    
    # Extracted insights
    sentiment_score = db.Column(Float)
    key_themes = db.Column(JSON)  # List of themes/keywords
    therapy_insights = db.Column(JSON)  # Structured therapy-specific insights
    progress_indicators = db.Column(JSON)  # Progress tracking data
    
    # Notion integration
    notion_page_id = db.Column(String(255))
    notion_synced = db.Column(Boolean, default=False)
    notion_sync_error = db.Column(Text)
    
    # Timestamps
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ProcessingLog(db.Model):
    """Model for tracking processing activities and errors"""
    id = db.Column(Integer, primary_key=True)
    transcript_id = db.Column(Integer, db.ForeignKey('transcript.id'), nullable=True)
    
    # Log details
    activity_type = db.Column(String(100), nullable=False)  # dropbox_scan, file_process, ai_analysis, notion_sync
    status = db.Column(String(50), nullable=False)  # success, error, warning
    message = db.Column(Text)
    error_details = db.Column(Text)
    
    # Additional context data
    context_metadata = db.Column(JSON)  # Additional context data
    
    # Timestamps
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SystemSettings(db.Model):
    """Model for storing system configuration"""
    id = db.Column(Integer, primary_key=True)
    key = db.Column(String(255), unique=True, nullable=False)
    value = db.Column(Text)
    description = db.Column(Text)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
