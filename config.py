import os

class Config:
    """Configuration class for the therapy transcript processor"""
    
    # Dropbox configuration
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN', 'sl.u.AFzkTn-I60M5RQL8Trj5PR9a6kUOg68s5lkhUKZNBsbqcXiTYAj94ZwJMO0bZuBAtP2pTUAhlD4sxeZKFIYOxZuGvatElyCVXivWJLvzySeFUrt5JmCZo6mOlliWMvt_SW3dcLKH0dY6Cg3wE5NqlBWlnMqKlDr_VHYWk6C8oOxvibY0zVrYpseo_4KaL4xT6mmykBeW-Vnj4tZZEv9CQmwX4AlZUaiNEb66Z7m2leQy7cUJHcszGbUiBALlY_TQPvNnyInRiKFsimF3YLGl2njI7xl2hva71MPH2ZkKCY80khIpzWRPK-JFkO0Y3HgKhTPaOstl9Sx4qMx4Z5egNSdQl_E_UkujeIaeIvgZ2U3hFp-AR_4rMoqmHjhBR-sn47uNK2sMWZT0RSujpupjWTHXjQOMZnJcsf0yy4x99-a84ipnT0OcgJZS8AFgb1HdgtnnJUvkg1yS4MJSzq_WzM4PgOMDg56z5KUZMPU9kzyLRsPpAQ61IDYy7mQqhDAtx8PCasOhwuXqlSpI8Hj1RpK05OYNtYStinXGZ-3cMSl8oKGYDJXjSOtBkku1v0D3xM-AYTUrEI6yT4ognD9vfVs9W0cH54L2ODJ2shRwBHszuDxxc6HyaC0k6EgHfkNFyOfGXmscwRyO0vg_Vnk_m8wccddSFpocqd3SN413OxvKtgRycPxbS89gExNWzZvo-R0uXYkkOY6z4RHzRp4qHTElfVH03eIwT8R-gJZcFhrZZ7GhLz-OvhfcZyijSrydkAhIi9JJz0qNu0EoztAJo7F5_PduxWTxwwOsAdMEEibWCTYcMlQBOMtS82YU7XK4NOBhZhi8SuLdvKp6Hvamboomgvu1jb0jwq7FJfAoOkyxXmoMR4MFdxti9A0GkGGIjeuYWta8H6UKnWDP13SO3OlgBpOhJXq1JaaCaqnNR0Mqoxrz9j2DHDpEguGPVzngcfR_IgyXIbj4HfxcU2508FfgZxFYsnnasTNZuWkM1akJLOc61u2zUnG2GxXEH9M6o6gEF_pXHHNz00u5uN4GTM5t94qHAfcgDqmyTELbweRnee9vY8LsbJZ6cypoy4O7_5HIdZpzzKjtmkQF1T6MMozahdRjbVgN6km9g-5WsP3aIWN0P3Y6WL8ZDahFZJ1VInP2pm8ar_A5xGLd95WseELIKYUuz2V1b3YrdEzZYP4K1jQYp9bAzxzvlc_fYDg4dGumVvJ47I_vNQ0-oV2SLIuw8F6AFc-Nk69vIVYuPqHolt1zIeH_TLDMac61nKYC0fstK9nMtfE9GI5bQGUBaSKyqA1eXMb6suXMmgYBtwsC5C6sJD7UvEa_FAfWrgUUP1XjiviAE1XBbsmKgejAdgEEuCI4HEskj3FweNv4KwjpOg')
    DROPBOX_MONITOR_FOLDER = '/apps/otter'
    
    # AI Provider API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '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')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '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') 
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKSugqYPsqYMrrAiXh-1bAPf992gVrGbk')
    
    # Notion configuration
    NOTION_INTEGRATION_SECRET = os.environ.get('NOTION_INTEGRATION_SECRET', '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')
    NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID', '2049f30def818033b42af330a18aa313')
    NOTION_PARENT_PAGE_ID = '2049f30def818033b42af330a18aa313'  # Parent page for client databases
    
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
    You are an expert clinical therapist with extensive training in psychotherapy, clinical documentation, and therapeutic modalities including ACT, DBT, Narrative Therapy, and Existentialism. Your task is to create a comprehensive clinical progress note from the provided therapy session transcript that demonstrates the depth, clinical sophistication, and analytical rigor of an experienced mental health professional.

    Create a progress note with the following precise structure:

    1. Title: "Comprehensive Clinical Progress Note for [Client's Full Name]'s Therapy Session on [Date]"

    2. Subjective Section: Document the client's self-reported experiences, emotional states, and presenting concerns. Include direct quotes and the client's narrative about their current psychological state, recent events, and internal experiences.

    3. Objective Section: Provide clinical observations including presentation, affect, mood, thought process, speech patterns, behavior, and any notable changes from previous sessions.

    4. Assessment Section: Offer clinical diagnostic impressions, symptom assessment, progress evaluation, and clinical formulation based on observable data and client reports.

    5. Plan Section: Detail therapeutic interventions used, homework assignments, treatment goals, and specific plans for future sessions.

    6. Supplemental Analyses:
       - Tonal Analysis: Document significant shifts in emotional tone, voice quality, and affect throughout the session
       - Thematic Analysis: Identify recurring themes, patterns, and underlying psychological dynamics
       - Sentiment Analysis: Assess overall emotional trajectory and engagement levels

    7. Key Points: Highlight critical therapeutic moments, breakthroughs, resistance patterns, and clinically significant observations

    8. Significant Quotes: Include verbatim client statements that reveal important psychological material, insights, or emotional states

    9. Comprehensive Narrative Summary: Provide an integrated clinical narrative that synthesizes all observations into a cohesive understanding of the client's current psychological state and treatment progress

    Your analysis must demonstrate:
    - Depth of clinical thinking with sophisticated psychological understanding
    - Integration of multiple therapeutic frameworks and perspectives
    - Professional clinical voice with appropriate terminology
    - Detailed behavioral observations and clinical assessments
    - Actionable treatment planning and therapeutic recommendations

    Provide the most comprehensive and detailed analysis possible, utilizing the full scope of clinical expertise.

    Transcript:
    """
    
    LONGITUDINAL_ANALYSIS_PROMPT = """
    You are an expert clinical therapist specializing in longitudinal case conceptualization and treatment planning. Your task is to create a comprehensive, dynamic case conceptualization that evolves with each new therapy session.

    Based on the client's complete therapy history provided below, create a detailed longitudinal case conceptualization with the following structure:

    1. **Dynamic Case Conceptualization Summary**
       - Current clinical presentation and diagnostic impressions
       - Evolution of symptoms and functioning since treatment began
       - Core psychological patterns and dynamics identified across sessions

    2. **Longitudinal Progress Analysis**
       - Treatment trajectory and milestone achievements
       - Therapeutic alliance development and engagement patterns
       - Behavioral and cognitive changes observed over time
       - Setbacks, plateaus, and breakthrough moments

    3. **Recurring Themes and Patterns**
       - Persistent psychological themes across sessions
       - Defense mechanisms and coping strategies utilized
       - Relationship patterns and attachment dynamics
       - Trauma responses and triggers consistently observed

    4. **Treatment Effectiveness Assessment**
       - Intervention responsiveness across different therapeutic approaches
       - Client's receptivity to specific therapeutic techniques
       - Homework completion and between-session progress
       - Factors that enhance or impede therapeutic progress

    5. **Risk Assessment and Safety Considerations**
       - Current risk factors and protective factors
       - Changes in safety concerns over treatment course
       - Crisis intervention history and current vulnerability

    6. **Updated Treatment Planning and Recommendations**
       - Refined treatment goals based on progress observed
       - Recommended therapeutic approaches for upcoming sessions
       - Areas requiring increased clinical attention
       - Specific interventions to implement or modify

    7. **Therapeutic Relationship Dynamics**
       - Transference and countertransference patterns observed
       - Alliance ruptures and repairs documented
       - Client's therapeutic style and preferences identified

    8. **Functional Improvement Indicators**
       - Work/academic functioning changes
       - Relationship and social functioning evolution
       - Daily living skills and self-care improvements
       - Psychological resilience development

    Provide a comprehensive, clinically sophisticated analysis that demonstrates deep understanding of this client's unique psychological presentation and treatment needs. Use clinical terminology appropriately and maintain professional documentation standards.

    Complete Session History for Longitudinal Analysis:
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
