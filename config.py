import os

class Config:
    """Configuration class for the therapy transcript processor"""

    # Dropbox configuration
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')
    DROPBOX_MONITOR_FOLDER = os.environ.get('DROPBOX_MONITOR_FOLDER', '/apps/otter')  # Monitor Otter app folder with PDFs

    # AI Provider API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') 
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Notion configuration
    NOTION_INTEGRATION_SECRET = os.environ.get('NOTION_INTEGRATION_SECRET')
    NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
    NOTION_PARENT_PAGE_ID = '2049f30def818033b42af330a18aa313'  # Parent page for client databases

    # Processing configuration
    SUPPORTED_FILE_TYPES = ['.pdf', '.txt', '.docx']
    MAX_FILE_SIZE_MB = 50

    # Scheduler configuration
    DROPBOX_SCAN_INTERVAL_MINUTES = 5

    # AI Model configurations
    OPENAI_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    GEMINI_MODEL = "gemini-1.5-flash"

    # Analysis prompts
    THERAPY_ANALYSIS_PROMPT = """
    You are a highly skilled and experienced therapist specializing in creating comprehensive and insightful clinical progress notes. Your task is to analyze the provided counseling session transcript and generate a detailed progress note with the depth, detail, and clinical sophistication of an expert human therapist.

    CRITICAL FORMATTING REQUIREMENT: Use NO markdown syntax whatsoever. No hashtags, asterisks for bold/italic, or any markdown formatting. Use plain text only with proper headings and structure but no markdown characters.

    Create a progress note with the following precise structure:

    Comprehensive Clinical Progress Note for [Client's Full Name]'s Therapy Session on [Date]

    SUBJECTIVE
    Provide extensive detail of the client's reported experiences, feelings, concerns, and significant life events. Include direct quotes that reveal psychological material. Document all key topics discussed, emphasizing their impact on mental and physical well-being. Identify significant quotes highly relevant to the client's concerns, mindset, and emotional state. Analyze the language used and underlying emotions in detail with specific examples and context. Use format: "[Client] attended today's session expressing significant distress about [specific issue]. [He/She] appeared visibly [emotional state] when describing [situation], stating, '[direct quote].' This statement reflects [client's] sense of [psychological theme] regarding [situation], themes that have emerged in previous sessions related to [broader patterns]."

    OBJECTIVE
    Describe the client's behavior and demeanor throughout the session with specific examples. Document emotional state, responsiveness to therapy, and observed physical signs. Include detailed observations of emotional expressions, intensity, unusual aspects, and potential underlying issues. Describe physical manifestations of stress/relaxation and correlate them with the discussion. Use format: "[Client] presented to the session [appearance details]. [He/She] was alert and oriented, with [speech characteristics] and [thought process]. [His/Her] affect was notably [description] throughout most of the session, with [emotional range details]. This [observation] appeared to be [clinical interpretation], as [evidence of interpretation]."

    ASSESSMENT
    Provide comprehensive evaluation integrating subjective and objective data. Analyze the interplay between reported experiences and observed behaviors. Identify patterns, themes, and potential underlying issues. Discuss the impact of personal and external stressors on mental and physical health. Identify and evaluate coping mechanisms with examples and long-term impacts. Assess strengths, resources, and risk factors thoroughly. Use format: "[Client] continues to meet criteria for [specific diagnosis] as evidenced by [specific symptoms and behaviors]. [His/Her] recent [stressor/event] has [impact on symptoms], particularly [specific symptom areas]. The [specific presentation] appears to be [clinical interpretation] rather than [differential consideration], as [clinical evidence]."

    PLAN
    Propose comprehensive management plan specifying all therapeutic steps. Detail adjustments to treatment protocols with clear rationale and expected benefits. Describe specific psychological interventions tailored to the client's needs, explicitly naming therapeutic frameworks (ACT, DBT, Narrative, Existential). Specify frequency and duration of follow-up appointments, homework assignments, and referrals. Use format: "[Therapeutic approach] Interventions: Continue to utilize [framework] to address [specific targets]. In today's session, we [specific intervention], helping [client] recognize [therapeutic insight]. We will continue to develop [specific skills] through [specific techniques]."

    SUPPLEMENTAL ANALYSES

    Tonal Analysis (5-7 detailed paragraphs)
    Identify and describe at least 5-7 significant shifts in tone. Precisely associate each shift with specific topic or intervention that triggered it. Explain implications of each shift on client engagement and therapeutic process with detailed examples. Dedicate separate paragraph to each identified tonal shift. Format: "Shift 1: From [initial tone] to [shifted tone]: A significant tonal shift occurred when [specific trigger]. [His/Her] tone shifted from [detailed description] to [detailed description], with [specific vocal changes]. This shift was triggered specifically when [detailed context and significance]."

    Thematic Analysis (4-5 detailed paragraphs)
    Identify at least 4-5 major themes. Provide 2-3 specific quotes from transcript to clearly illustrate each theme. Connect each theme to client's broader psychological profile and mental health status. Relate themes to previous sessions if context provided. Identify recurring themes and discuss their significance.

    Sentiment Analysis (5-7 detailed paragraphs)
    Perform detailed analysis of client sentiments, categorizing as positive, negative, or neutral. Group sentiments into: 1) Self, 2) Others/External Situations, 3) Therapy/Therapeutic Process. Identify 3 most frequently expressed sentiments in each category with specific quotes. Analyze how ratio of positive to negative sentiments shifts throughout session. Discuss potential reasons for sentiment shifts and implications.

    KEY POINTS
    Identify at least 3 key points from session. For each key point, provide bullet point and subtext explaining relevance to therapy goals and progress. Format: "• [Theme/Pattern] as [Clinical Significance]: [Detailed explanation of pattern, clinical importance, and therapeutic implications]. [Additional analysis of how this impacts treatment and what interventions are indicated]."

    SIGNIFICANT QUOTES
    List at least 3-5 significant quotes with full context. Explain why each quote is significant, focusing on diagnostic or therapeutic implications. Analyze language, emotions, and insights. Do not use minute markers or timestamps. Format: "'[Exact quote]' [Client] made this statement when [context]. [He/She] described [additional context]. This quote is significant because [detailed psychological analysis and clinical implications]."

    COMPREHENSIVE NARRATIVE SUMMARY
    Craft cohesive narrative summary weaving together discussions, quotes, and observations. Encapsulate client's emotional and psychological journey, highlighting key moments. Reflect on implications for future sessions. Discuss how findings align with and advance therapeutic goals. Provide forward-looking perspective outlining challenges and opportunities. Write professionally yet empathetically, demonstrating deep understanding.

    Your analysis must demonstrate depth of clinical thinking, sophisticated psychological understanding, integration of multiple therapeutic frameworks, professional clinical voice, detailed behavioral observations, actionable treatment planning, and rich detail throughout all sections. This is an emulation of expert clinical reasoning producing a deeply insightful and clinically useful document.

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