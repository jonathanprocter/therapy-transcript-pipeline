import os

class Config:
    """Configuration class for the therapy transcript processor"""
    
    # Dropbox configuration
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN', 'sl.u.AFwxTGahYGTHhIGTzQFYfoLHQlAfgpn57BGXXnQ7yXDgiNjXKfLRe8Q7Nm-__CQ1dLs5vkmzkoVUA5wh1YiTwcB39wJDKYLuNFs1alA2TJU3LXYxkoI525fPoPKiidnQztDiJc_GB0aCR2EGwhlgo--WOLPqKSe0A0ChfLE39MESMho9B0sQ8qNgINqrbIuTGsUHo8AbSZxE3_6LgNr_ZZzhkBLN3JlVV7vMLsFGL-eurkYO-nOTXNRY3QprtX11SvPV7Bbof7hlluojdAWQ3zQ6v12YCwey-vLJ8MwFNiyZePVnjiUoeDd8mkILbwDel2sXBpsOxBIPIsBAW9xsM6QGv58vg-1SrKRg87SrvbgU_NdeswCOsZPThxwE2q9H89E_0H8RFMCuQoaK2KxjQPCFl43fMhWch8cjI1Su9YermYNjrC4j90Pmh34hL6-mDVfyh1meb3qL3juLbIg2okrDl0tAwFkpW5Di8cxrHZFHMTC8PLWwpmAQQ-wYd7M1c5QpSctGepjTrOqRDdt1r8l-hMFUWVgmYHr7bWzPom1K_L3HlrTy0fymwd4kn2_DDdXYbmoWLMBwbousd5iSp6rcnthi_9DOlukTs1LjWJk0BUMlIPaHLT-wezWB02Fdr-BInwa-Q89L1q5Zdcf1eUdwtgygRlq77s5riAsjOkN8NK4MlJb_sAJiJ-6Ol_xEddencvc1I01oVCu6RWigyTEfEA9U8Dy4r3UG_ZLabwhGa8LIxVaodYNdtebbsgK2kRH6cQU8Rs9e9rJW9aExziGThClwJDMF-1D_rro79NWSX4dtA33XGam0QQIfhd3FUoPVJTjmS9YUqHNs_LhhleHpLMVOuG0XJjRfvmpqap09c7AQvRM0pqdpz_PJS5vdqjn3yM0zKsk2lz0i1WwPJgn6KgVIIavGFJN0sC5D7W9m-mk6Oysiq-xcZw8XMw9OlBtW-opBvWRV3Si5EgAt6NA3cn1RciurYrrKndFk_vk0iTsdmMed4g6z4uARgkxeDlG08mXbLYrg-I9NSOGtbKbRKzyL0D_-IJ0dldDNU1e7LLKYcQ5zWh3YGRlHoA-muaCBIJ5PDImgCA0DcRVya623lKaTp2OfMLTnUXip0mL58niksd7BmO2JqSyD-sGo6jPdb_NqD_1XGoLRMjxaaoOu7KSZi8XfC3WShVvJup639UKWjcx_PeMZZJvD3kW2lLzAKqjhlR9febin9yiUgQMdAaNrcL3oBOffQSj2E8peeYYZcm-AHTYtTu4-S_9qZYf87aKlPRf1nsJOknqVtcjcE2gvt3mcBEItxX9117fgf-XWXmUjL9PDrCTm-v0tnaIK47jpbAA3Jblo2Ia2QkPf')
    DROPBOX_MONITOR_FOLDER = '/apps/otter'  # Monitor Otter app folder with PDFs
    
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

    2. Subjective Section: Document the client's self-reported experiences, emotional states, and presenting concerns with extensive detail. Include direct quotes that reveal psychological material, the client's narrative about their current psychological state, recent events, and internal experiences. Provide rich context and analysis of the client's subjective experience. Example format: "[Client] attended today's session expressing significant distress about [specific issue]. [He/She] appeared visibly [emotional state] when describing [situation], stating, '[direct quote].' This statement reflects [client's] sense of [psychological theme] regarding [situation], themes that have emerged in previous sessions related to [broader patterns]. [Client] reported [additional details with quotes and analysis]."

    3. Objective Section: Provide detailed clinical observations including presentation, affect, mood, thought process, speech patterns, behavior, and any notable changes. Include micro-observations of nonverbal behavior, emotional shifts, and clinical phenomena observed during the session. Example format: "[Client] presented to the session [appearance details]. [He/She] was alert and oriented, with [speech characteristics] and [thought process]. [His/Her] affect was notably [description] throughout most of the session, with [emotional range details]. This [observation] appeared to be [clinical interpretation], as [evidence of interpretation]. [Additional detailed observations with clinical significance]."

    4. Assessment Section: Offer comprehensive clinical diagnostic impressions, symptom assessment, progress evaluation, and clinical formulation based on observable data and client reports. Demonstrate sophisticated clinical thinking with integration of multiple theoretical frameworks. Example format: "[Client] continues to meet criteria for [specific diagnosis] as evidenced by [specific symptoms and behaviors]. [His/Her] recent [stressor/event] has [impact on symptoms], particularly [specific symptom areas]. The [specific presentation] appears to be [clinical interpretation] rather than [differential consideration], as [clinical evidence]. [Additional sophisticated clinical formulation with theoretical integration]."

    5. Plan Section: Detail specific therapeutic interventions used, homework assignments, treatment goals, and specific plans for future sessions. Include multiple therapeutic modalities and specific techniques. Example format: "[Therapeutic approach] Interventions: Continue to utilize [framework] to address [specific targets]. In today's session, we [specific intervention], helping [client] recognize [therapeutic insight]. We will continue to develop [specific skills] through [specific techniques]. [Additional specific intervention planning across multiple modalities]."

    6. Supplemental Analyses:
       - Tonal Analysis: Document significant shifts in emotional tone, voice quality, and affect throughout the session with specific examples. Format: "Shift 1: From [initial tone] to [shifted tone]: A significant tonal shift occurred when [specific trigger]. [His/Her] tone shifted from [detailed description] to [detailed description], with [specific vocal changes]. This shift was triggered specifically when [detailed context and significance]."
       - Thematic Analysis: Identify recurring themes, patterns, and underlying psychological dynamics with detailed exploration
       - Sentiment Analysis: Assess overall emotional trajectory and engagement levels with specific observations

    7. Key Points: Highlight critical therapeutic moments, breakthroughs, resistance patterns, and clinically significant observations with detailed analysis. Format: "• [Theme/Pattern] as [Clinical Significance]: [Detailed explanation of the pattern, its clinical importance, and therapeutic implications]. [Additional analysis of how this impacts treatment and what interventions are indicated]."

    8. Significant Quotes: Include verbatim client statements with detailed analysis of their psychological significance. Format: "'[Exact quote]' [Client] made this statement when [context]. [He/She] described [additional context]. This quote is significant because [detailed psychological analysis and clinical implications]."

    9. Comprehensive Narrative Summary: Provide an integrated clinical narrative that synthesizes all observations into a cohesive understanding of the client's current psychological state and treatment progress. This should be a sophisticated integration demonstrating advanced clinical thinking and therapeutic wisdom.

    Your analysis must demonstrate:
    - Depth of clinical thinking with sophisticated psychological understanding
    - Integration of multiple therapeutic frameworks and perspectives  
    - Professional clinical voice with appropriate terminology
    - Detailed behavioral observations and clinical assessments
    - Actionable treatment planning and therapeutic recommendations
    - Rich detail and clinical sophistication throughout all sections

    Provide the most comprehensive and detailed analysis possible, utilizing the full scope of clinical expertise and demonstrating the depth shown in the examples.

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
