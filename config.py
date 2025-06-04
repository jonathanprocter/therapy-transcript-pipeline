import os

class Config:
    """Configuration class for the therapy transcript processor"""
    
    # Dropbox configuration
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')
    DROPBOX_MONITOR_FOLDER = '/apps/otter'
    
    # AI Provider API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') 
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Notion configuration
    NOTION_INTEGRATION_SECRET = os.environ.get('NOTION_INTEGRATION_SECRET')
    
    # Processing configuration
    SUPPORTED_FILE_TYPES = ['.pdf', '.txt', '.docx']
    MAX_FILE_SIZE_MB = 50
    
    # Scheduler configuration
    DROPBOX_SCAN_INTERVAL_MINUTES = 5
    
    # AI Model configurations
    OPENAI_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    GEMINI_MODEL = "gemini-pro"
    
    # Analysis prompts
    THERAPY_ANALYSIS_PROMPT = """
    You are an expert therapy transcript analyst. Analyze this therapy session transcript and provide structured insights.
    
    Please analyze the following therapy session transcript and return a JSON response with these fields:
    
    {
        "session_summary": "Brief summary of the session",
        "client_mood": "Overall mood assessment (scale 1-10)",
        "key_topics": ["list", "of", "main", "topics", "discussed"],
        "therapeutic_techniques": ["techniques", "used", "by", "therapist"],
        "client_progress_indicators": {
            "emotional_regulation": "assessment",
            "insight_development": "assessment", 
            "behavioral_changes": "assessment"
        },
        "concerns_raised": ["any", "concerns", "or", "risk", "factors"],
        "homework_assignments": ["any", "assignments", "given"],
        "next_session_goals": ["goals", "for", "next", "session"],
        "sentiment_analysis": {
            "overall_sentiment": "positive/neutral/negative",
            "emotional_tone": "description",
            "engagement_level": "high/medium/low"
        }
    }
    
    Transcript:
    """
    
    LONGITUDINAL_ANALYSIS_PROMPT = """
    You are analyzing therapy progress over time. Based on the following session data, provide longitudinal insights.
    
    Analyze the progression across these sessions and return JSON with:
    
    {
        "overall_progress": "assessment of client progress",
        "trend_analysis": {
            "mood_trend": "improving/stable/declining",
            "engagement_trend": "increasing/stable/decreasing",
            "insight_development": "assessment"
        },
        "recurring_themes": ["themes", "that", "appear", "consistently"],
        "breakthrough_moments": ["significant", "insights", "or", "progress"],
        "areas_for_focus": ["areas", "needing", "attention"],
        "treatment_effectiveness": "assessment of current approach"
    }
    
    Session Data:
    """

# Environment validation
def validate_environment():
    """Validate that required environment variables are set"""
    required_vars = [
        'DROPBOX_ACCESS_TOKEN',
        'OPENAI_API_KEY', 
        'ANTHROPIC_API_KEY',
        'GEMINI_API_KEY',
        'NOTION_INTEGRATION_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("The application may not function properly without these variables.")
    
    return len(missing_vars) == 0

# Call validation on import
validate_environment()
