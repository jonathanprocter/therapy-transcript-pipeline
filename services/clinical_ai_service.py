"""
Clinical AI Service - Implements specific therapeutic prompts for comprehensive analysis
"""
import json
import logging
from typing import Dict, Optional, List
import os
from openai import OpenAI
import anthropic
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ClinicalAIService:
    """Advanced AI service implementing specific clinical prompts"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_client = None
        
        # Initialize clients
        self._initialize_openai()
        self._initialize_anthropic()
        self._initialize_gemini()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def _initialize_anthropic(self):
        """Initialize Anthropic client"""
        try:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def _initialize_gemini(self):
        """Initialize Google Gemini client"""
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    def get_comprehensive_clinical_prompt(self, client_name: str = None) -> str:
        """Get the comprehensive clinical analysis prompt"""
        return f"""You are a highly skilled and experienced therapist specializing in creating comprehensive and insightful clinical progress notes. Your task is to analyze a provided counseling session transcript and generate a detailed progress note that mirrors the depth, detail, and clinical sophistication of an expert human therapist.

**Clinical Analysis Requirements:**

1. **SOAP Note Structure:**
   - **Subjective:** Detailed account of client's reported experiences, feelings, concerns, and significant life events with specific quotes
   - **Objective:** Client's behavior, demeanor, emotional state, and physical manifestations throughout session
   - **Assessment:** Comprehensive evaluation integrating subjective and objective data, identifying patterns and underlying issues
   - **Plan:** Comprehensive management plan with specific therapeutic interventions and frameworks (ACT, DBT, Narrative, Existential)

2. **Supplemental Analyses:**
   - **Tonal Analysis:** Identify 5-7 significant shifts in tone with specific triggers and implications
   - **Thematic Analysis:** Identify 4-5 major themes with 2-3 specific quotes illustrating each
   - **Sentiment Analysis:** Line-by-line categorization (positive/negative/neutral) for Self, Others, and Therapy Process

3. **Key Elements:**
   - At least 3 key points with therapeutic relevance
   - 3-5 significant quotes with full context and clinical implications
   - Comprehensive narrative summary weaving together all elements

**Output Format:**
- Title: Comprehensive Clinical Progress Note for {client_name or '[Client Name]'}'s Therapy Session on [Date]
- All sections clearly structured with NO markdown syntax in final output
- Professional clinical voice with therapeutic sophistication
- Integration of multiple therapeutic frameworks

Provide a clinically sophisticated analysis that demonstrates expert-level therapeutic reasoning and would meet the highest standards of professional documentation."""

    def analyze_with_openai(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using OpenAI with comprehensive clinical prompt"""
        if not self.openai_client:
            return {"error": "OpenAI client not available"}
        
        try:
            prompt = self.get_comprehensive_clinical_prompt(client_name)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Latest OpenAI model
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Please analyze this therapy session transcript:\n\n{transcript_content[:4000]}"}
                ],
                max_tokens=3000,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "provider": "openai",
                "model": "gpt-4o",
                "analysis": analysis,
                "client_focus": client_name or "Client",
                "analysis_type": "comprehensive_clinical",
                "therapeutic_frameworks": ["ACT", "DBT", "Narrative", "Existential"],
                "sections": ["subjective", "objective", "assessment", "plan", "supplemental_analyses"]
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            return {"error": f"OpenAI analysis failed: {str(e)}"}

    def analyze_with_anthropic(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using Anthropic with comprehensive clinical prompt"""
        if not self.anthropic_client:
            return {"error": "Anthropic client not available"}
        
        try:
            prompt = self.get_comprehensive_clinical_prompt(client_name)
            
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nPlease analyze this therapy session transcript:\n\n{transcript_content[:4000]}"}
                ]
            )
            
            analysis = response.content[0].text
            
            return {
                "provider": "anthropic",
                "model": "claude-3-sonnet",
                "analysis": analysis,
                "client_focus": client_name or "Client",
                "analysis_type": "comprehensive_clinical",
                "therapeutic_frameworks": ["ACT", "DBT", "Narrative", "Existential"],
                "sections": ["subjective", "objective", "assessment", "plan", "supplemental_analyses"]
            }
            
        except Exception as e:
            logger.error(f"Anthropic analysis error: {e}")
            return {"error": f"Anthropic analysis failed: {str(e)}"}

    def analyze_with_gemini(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using Gemini with comprehensive clinical prompt"""
        if not self.gemini_client:
            return {"error": "Gemini client not available"}
        
        try:
            prompt = self.get_comprehensive_clinical_prompt(client_name)
            
            response = self.gemini_client.generate_content(
                f"{prompt}\n\nPlease analyze this therapy session transcript:\n\n{transcript_content[:4000]}"
            )
            
            analysis = response.text
            
            return {
                "provider": "gemini",
                "model": "gemini-pro",
                "analysis": analysis,
                "client_focus": client_name or "Client",
                "analysis_type": "comprehensive_clinical",
                "therapeutic_frameworks": ["ACT", "DBT", "Narrative", "Existential"],
                "sections": ["subjective", "objective", "assessment", "plan", "supplemental_analyses"]
            }
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return {"error": f"Gemini analysis failed: {str(e)}"}

    def complete_analysis_for_transcript(self, transcript_data: Dict) -> Dict:
        """Complete comprehensive analysis for a single transcript"""
        results = {}
        client_name = transcript_data.get('client_name', 'Client')
        content = transcript_data.get('raw_content', '')
        
        # OpenAI Analysis
        if not transcript_data.get('openai_analysis'):
            openai_result = self.analyze_with_openai(content, client_name)
            results['openai_analysis'] = openai_result
        
        # Anthropic Analysis
        if not transcript_data.get('anthropic_analysis'):
            anthropic_result = self.analyze_with_anthropic(content, client_name)
            results['anthropic_analysis'] = anthropic_result
        
        # Gemini Analysis
        if not transcript_data.get('gemini_analysis'):
            gemini_result = self.analyze_with_gemini(content, client_name)
            results['gemini_analysis'] = gemini_result
        
        return results

    def extract_themes_from_analysis(self, analysis_data: Dict) -> List[str]:
        """Extract key themes from AI analysis"""
        themes = []
        
        if isinstance(analysis_data, dict):
            analysis_text = analysis_data.get('analysis', '')
            if isinstance(analysis_text, str):
                # Extract themes from comprehensive analysis
                if 'thematic analysis' in analysis_text.lower():
                    # Parse themes from the thematic analysis section
                    lines = analysis_text.split('\n')
                    for line in lines:
                        if any(keyword in line.lower() for keyword in ['theme', 'pattern', 'concern', 'issue']):
                            if len(line.strip()) > 10 and len(line.strip()) < 100:
                                themes.append(line.strip())
                
                # Fallback: extract from key clinical terms
                clinical_terms = [
                    'anxiety', 'depression', 'trauma', 'relationships', 'coping',
                    'identity', 'grief', 'stress', 'communication', 'boundaries',
                    'self-esteem', 'emotional regulation', 'therapeutic alliance'
                ]
                
                for term in clinical_terms:
                    if term in analysis_text.lower():
                        themes.append(term.title())
        
        return list(set(themes))[:5]  # Return unique themes, max 5

    def calculate_sentiment_score(self, analysis_data: Dict) -> float:
        """Calculate overall sentiment score from analysis"""
        if not isinstance(analysis_data, dict):
            return 0.5  # Neutral
        
        analysis_text = analysis_data.get('analysis', '')
        if not isinstance(analysis_text, str):
            return 0.5
        
        # Simple sentiment calculation based on clinical terms
        positive_terms = ['progress', 'improvement', 'strength', 'resilient', 'engaged', 'insight']
        negative_terms = ['distress', 'struggle', 'difficult', 'challenging', 'crisis', 'severe']
        
        positive_count = sum(1 for term in positive_terms if term in analysis_text.lower())
        negative_count = sum(1 for term in negative_terms if term in analysis_text.lower())
        
        total = positive_count + negative_count
        if total == 0:
            return 0.5
        
        return positive_count / total