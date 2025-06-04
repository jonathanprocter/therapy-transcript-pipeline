import os

class Config:
    """Configuration class for the therapy transcript processor"""
    
    # Dropbox configuration
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN', 'sl.u.AFx7adMtGVqRibIthtqU_eSsUTJ9S7fXsh1ARJ8JfB3yWSZQn_5ulh17IItV5oc4tb3J17Zlng3cLbkrbTyfKW4MjQDYcL7sec9TYlK9zk0NxwICJZafj5BePa3Jxgdv_FP-lKXBDg6_utxfpsvO6jI8yZzkBpxBb833tYiqi5WcDy3rA3wJbZ0kOgT0QjXJrAxX-R4HCzroB_7v9-s6V1CdxpHG7AAMn1pErTnTsan01xw-0jlkne5_y-5eL4kwuyKLrmgP3VlXYa2iasi-h5tvpYbO2FolnmvSPwOifUcU5Fg1oZaZMDmIyuu8VhvEn40xl-7CWxWbVxMoyWFA5iIyxSFAarp9J9vW4R4grzGvW7E-9y4St4Wzid7mJ55r0_MyhRCI_LrHPjHkC7Cap6AiUFjdiMg6mD0NGSSz55ojO8H0xn3AvM1G1jGksL1MSVtp_e1G8ajPM3zzcmZEVCqKl7vdv4uSbOZXbeL4loTXGEGbIaM9hYqcuDA72sSF8Vv0Gxffv0eqtNnDts3shFTqpPUh1_askUKt_JIANq3PxcUZ5VJJ8FMB5kBVEWppmghXTU-ymZF_TZhs-TxUf3TmtFAWErvWVJ5rDZtzsZ4K9oZbV6GHtu7rxXDvzI9Ao_YcLgde6JQC4UCe4NAuNLT0Kx9ElS1_eZ1E1jjRb8EODe_-gKt1aO0Crs804q6KX4EOGnOuUR0FyqFt2-asd0thd2KCUg6o0hhjYsni9Dam-fIDXP8f-LnYG5516jWAYAXq-TcBNkeo-SGLq17--bTStVGe6jaOnvBrFOivkx3Ninq1K0o9DsE_rrEFfYlHpGu94n-rskhD1fCFscR5kiHCtPdxgwEzl2xsoDzrgSPErOa1a6L0HnMVVfpbvvg0lqwG5ZsRvT487HEFMcA0KnFfvdOJ6-Mo1gFNrNXmh266qsuO7P8WrT6xvEL7FLfLRX4xJILh8HHjnIWUeuD9GJlK9zR3GZuueb4iqGmpz-XyWJNql6D9eh5QvqieRq7a7FFqickR87QhFFApCKgVhV16dykQP8XOnO_YXBZXIVrdoC2GCAbFIAgKTIgr3iH9HJn91NFkC9_FzfNveUaUBZEl6SwFgh6CLLfGhkN4yE0OASsMXmKfqmcQMkKehNiSgZC82SHvh4rmfcz7pJQqoxKJTb4UgIU1sYOf34rAKHN-3OdE_OaTnr-yTXUqF3xYmZ8o1jyKO3RjfbowC7-2VxlaUSd7CJVlO_uqhr5ePoT0TXv0pUDwOkhI9dRybjapVy0GzvyLk3IeMAKW16jLrbaE9tMANNe0oH5ioA54hOkCKkOTSOZyWtXaCxLCG3i-toOhtrvOLAm2-xHJMIGHfS0q')
    DROPBOX_MONITOR_FOLDER = '/Apps/Otter.ai'  # Monitor Otter.ai app folder
    
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
