"""
Session Summary Service - Generate comprehensive one-click session summaries
"""
import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class SessionSummaryService:
    def __init__(self):
        self.ai_service = AIService()
    
    def generate_session_summary(self, transcript_data: Dict) -> Dict:
        """Generate a comprehensive one-click session summary"""
        try:
            logger.info(f"Generating session summary for transcript: {transcript_data.get('original_filename', 'Unknown')}")
            
            # Extract all available AI analyses
            openai_analysis = self._extract_analysis_text(transcript_data.get('openai_analysis'))
            anthropic_analysis = self._extract_analysis_text(transcript_data.get('anthropic_analysis'))
            gemini_analysis = self._extract_analysis_text(transcript_data.get('gemini_analysis'))
            
            # Get raw transcript content for additional processing if needed
            raw_content = transcript_data.get('raw_content', '')
            
            # Generate comprehensive summary
            summary_data = {
                'session_overview': self._generate_session_overview(openai_analysis, anthropic_analysis, gemini_analysis),
                'key_insights': self._extract_key_insights(openai_analysis, anthropic_analysis, gemini_analysis),
                'therapeutic_progress': self._assess_therapeutic_progress(openai_analysis, anthropic_analysis, gemini_analysis),
                'client_presentation': self._analyze_client_presentation(openai_analysis, anthropic_analysis, gemini_analysis),
                'session_goals': self._identify_session_goals(openai_analysis, anthropic_analysis, gemini_analysis),
                'interventions_used': self._extract_interventions(openai_analysis, anthropic_analysis, gemini_analysis),
                'homework_assignments': self._extract_homework(openai_analysis, anthropic_analysis, gemini_analysis),
                'risk_assessment': self._assess_risk_factors(openai_analysis, anthropic_analysis, gemini_analysis),
                'next_session_focus': self._plan_next_session(openai_analysis, anthropic_analysis, gemini_analysis),
                'clinical_impressions': self._extract_clinical_impressions(openai_analysis, anthropic_analysis, gemini_analysis),
                'session_rating': self._calculate_session_rating(openai_analysis, anthropic_analysis, gemini_analysis),
                'follow_up_actions': self._identify_follow_up_actions(openai_analysis, anthropic_analysis, gemini_analysis)
            }
            
            # Add metadata
            summary_data['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'transcript_id': transcript_data.get('id'),
                'client_name': transcript_data.get('client_name', 'Unknown'),
                'session_date': transcript_data.get('session_date'),
                'ai_providers_used': self._get_available_providers(openai_analysis, anthropic_analysis, gemini_analysis),
                'summary_version': '1.0'
            }
            
            logger.info("Session summary generated successfully")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return self._generate_error_summary(str(e))
    
    def _extract_analysis_text(self, analysis_data) -> str:
        """Extract text content from analysis data (handles both string and dict formats)"""
        if not analysis_data:
            return ""
        
        if isinstance(analysis_data, str):
            return analysis_data
        
        if isinstance(analysis_data, dict):
            # Look for common text fields
            text_fields = ['content', 'analysis', 'summary', 'text', 'response']
            for field in text_fields:
                if field in analysis_data and analysis_data[field]:
                    return str(analysis_data[field])
            
            # If no specific field found, convert entire dict to string
            return json.dumps(analysis_data, indent=2)
        
        return str(analysis_data)
    
    def _generate_session_overview(self, openai: str, anthropic: str, gemini: str) -> str:
        """Generate a comprehensive session overview"""
        analyses = [openai, anthropic, gemini]
        
        # Look for session overview patterns
        overview_patterns = [
            r'SUBJECTIVE[:\s]*(.{100,600}?)(?=OBJECTIVE|ASSESSMENT|$)',
            r'Session Overview[:\s]*(.{100,500}?)(?=\n\n|\n[A-Z])',
            r'COMPREHENSIVE NARRATIVE SUMMARY[:\s]*(.{100,600}?)(?=\n\n|$)',
            r'Client presented[:\s]*(.{50,400}?)(?=\.|$)'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in overview_patterns:
                    match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    if match:
                        overview = match.group(1).strip()
                        overview = re.sub(r'\s+', ' ', overview)
                        if len(overview) > 50:  # Ensure meaningful content
                            return overview[:500] + "..." if len(overview) > 500 else overview
        
        return "Session focused on therapeutic progress and addressing client concerns."
    
    def _extract_key_insights(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Extract key therapeutic insights from the session"""
        insights = []
        analyses = [openai, anthropic, gemini]
        
        insight_patterns = [
            r'Key insights?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])',
            r'Important observations?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])',
            r'Notable points?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])',
            r'Significant themes?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in insight_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        insight = match.group(1).strip()
                        insight = re.sub(r'\s+', ' ', insight)
                        if len(insight) > 20 and insight not in insights:
                            insights.append(insight)
        
        # If no structured insights found, extract from bullet points
        if not insights:
            bullet_pattern = r'[•\-\*]\s*(.{20,150}?)(?=\n|$)'
            for analysis in analyses:
                if analysis:
                    matches = re.finditer(bullet_pattern, analysis, re.IGNORECASE)
                    for match in matches:
                        insight = match.group(1).strip()
                        if len(insight) > 20 and insight not in insights:
                            insights.append(insight)
        
        return insights[:5]  # Return top 5 insights
    
    def _assess_therapeutic_progress(self, openai: str, anthropic: str, gemini: str) -> Dict:
        """Assess therapeutic progress indicators"""
        progress_data = {
            'overall_progress': 'Moderate',
            'specific_improvements': [],
            'areas_of_concern': [],
            'goal_achievement': 'In Progress'
        }
        
        analyses = [openai, anthropic, gemini]
        
        # Look for progress indicators
        progress_patterns = [
            r'progress[:\s]*(.{50,200}?)(?=\n\n|\.|$)',
            r'improvement[:\s]*(.{50,200}?)(?=\n\n|\.|$)',
            r'therapeutic gains?[:\s]*(.{50,200}?)(?=\n\n|\.|$)'
        ]
        
        improvements = []
        concerns = []
        
        for analysis in analyses:
            if analysis:
                # Look for positive progress indicators
                if any(word in analysis.lower() for word in ['improved', 'better', 'progress', 'growth', 'breakthrough']):
                    for pattern in progress_patterns:
                        matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            text = match.group(1).strip()
                            if any(pos_word in text.lower() for pos_word in ['improved', 'better', 'progress']):
                                improvements.append(text[:100])
                
                # Look for areas of concern
                if any(word in analysis.lower() for word in ['concern', 'difficulty', 'struggle', 'challenge', 'setback']):
                    concern_patterns = [
                        r'concern[:\s]*(.{50,200}?)(?=\n\n|\.|$)',
                        r'difficulty[:\s]*(.{50,200}?)(?=\n\n|\.|$)',
                        r'challenge[:\s]*(.{50,200}?)(?=\n\n|\.|$)'
                    ]
                    for pattern in concern_patterns:
                        matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            text = match.group(1).strip()
                            concerns.append(text[:100])
        
        progress_data['specific_improvements'] = list(set(improvements))[:3]
        progress_data['areas_of_concern'] = list(set(concerns))[:3]
        
        return progress_data
    
    def _analyze_client_presentation(self, openai: str, anthropic: str, gemini: str) -> Dict:
        """Analyze client's presentation during the session"""
        presentation = {
            'mood': 'Stable',
            'affect': 'Appropriate',
            'engagement_level': 'Good',
            'behavioral_observations': []
        }
        
        analyses = [openai, anthropic, gemini]
        
        # Mood indicators
        mood_keywords = {
            'depressed': ['depressed', 'sad', 'down', 'low mood'],
            'anxious': ['anxious', 'worried', 'nervous', 'tense'],
            'stable': ['stable', 'calm', 'balanced', 'even'],
            'elevated': ['elevated', 'manic', 'high', 'euphoric']
        }
        
        for analysis in analyses:
            if analysis:
                analysis_lower = analysis.lower()
                for mood, keywords in mood_keywords.items():
                    if any(keyword in analysis_lower for keyword in keywords):
                        presentation['mood'] = mood.title()
                        break
        
        return presentation
    
    def _identify_session_goals(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Identify session goals and objectives"""
        goals = []
        analyses = [openai, anthropic, gemini]
        
        goal_patterns = [
            r'goals?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'objectives?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'focus[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in goal_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        goal = match.group(1).strip()
                        goal = re.sub(r'\s+', ' ', goal)
                        if len(goal) > 15 and goal not in goals:
                            goals.append(goal)
        
        return goals[:3]  # Return top 3 goals
    
    def _extract_interventions(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Extract therapeutic interventions used in the session"""
        interventions = []
        analyses = [openai, anthropic, gemini]
        
        intervention_keywords = [
            'CBT', 'cognitive behavioral', 'mindfulness', 'psychoeducation',
            'exposure', 'behavioral activation', 'EMDR', 'solution-focused',
            'motivational interviewing', 'DBT', 'acceptance', 'grounding'
        ]
        
        for analysis in analyses:
            if analysis:
                analysis_lower = analysis.lower()
                for keyword in intervention_keywords:
                    if keyword.lower() in analysis_lower:
                        if keyword not in interventions:
                            interventions.append(keyword)
        
        return interventions
    
    def _extract_homework(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Extract homework assignments or between-session tasks"""
        homework = []
        analyses = [openai, anthropic, gemini]
        
        homework_patterns = [
            r'homework[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'assignment[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'between sessions?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'practice[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in homework_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        hw = match.group(1).strip()
                        hw = re.sub(r'\s+', ' ', hw)
                        if len(hw) > 10 and hw not in homework:
                            homework.append(hw)
        
        return homework[:3]  # Return top 3 assignments
    
    def _assess_risk_factors(self, openai: str, anthropic: str, gemini: str) -> Dict:
        """Assess any risk factors mentioned in the session"""
        risk_assessment = {
            'suicide_risk': 'Low',
            'self_harm_risk': 'Low',
            'substance_use': 'None reported',
            'safety_concerns': []
        }
        
        analyses = [openai, anthropic, gemini]
        
        risk_keywords = {
            'suicide': ['suicide', 'suicidal', 'kill myself', 'end my life'],
            'self_harm': ['self-harm', 'cutting', 'hurt myself', 'self-injury'],
            'substance': ['alcohol', 'drinking', 'drugs', 'substance', 'using']
        }
        
        for analysis in analyses:
            if analysis:
                analysis_lower = analysis.lower()
                
                # Check for suicide risk
                if any(keyword in analysis_lower for keyword in risk_keywords['suicide']):
                    risk_assessment['suicide_risk'] = 'Elevated - Requires Assessment'
                
                # Check for self-harm
                if any(keyword in analysis_lower for keyword in risk_keywords['self_harm']):
                    risk_assessment['self_harm_risk'] = 'Present'
                
                # Check for substance use
                if any(keyword in analysis_lower for keyword in risk_keywords['substance']):
                    risk_assessment['substance_use'] = 'Discussed in session'
        
        return risk_assessment
    
    def _plan_next_session(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Plan focus areas for the next session"""
        next_session = []
        analyses = [openai, anthropic, gemini]
        
        next_patterns = [
            r'next session[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'future sessions?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'follow[- ]?up[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'continue[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in next_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        item = match.group(1).strip()
                        item = re.sub(r'\s+', ' ', item)
                        if len(item) > 10 and item not in next_session:
                            next_session.append(item)
        
        return next_session[:3]  # Return top 3 focus areas
    
    def _extract_clinical_impressions(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Extract clinical impressions and diagnostic considerations"""
        impressions = []
        analyses = [openai, anthropic, gemini]
        
        impression_patterns = [
            r'clinical impression[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'assessment[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'diagnosis[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'DSM[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in impression_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        impression = match.group(1).strip()
                        impression = re.sub(r'\s+', ' ', impression)
                        if len(impression) > 10 and impression not in impressions:
                            impressions.append(impression)
        
        return impressions[:3]  # Return top 3 impressions
    
    def _calculate_session_rating(self, openai: str, anthropic: str, gemini: str) -> Dict:
        """Calculate overall session effectiveness rating"""
        rating_data = {
            'overall_rating': 7,  # Default rating out of 10
            'rating_rationale': 'Session showed good therapeutic engagement',
            'effectiveness_factors': []
        }
        
        analyses = [openai, anthropic, gemini]
        
        # Look for positive indicators
        positive_indicators = ['breakthrough', 'progress', 'insight', 'engaged', 'motivated']
        negative_indicators = ['resistant', 'difficult', 'withdrawn', 'crisis', 'setback']
        
        positive_count = 0
        negative_count = 0
        
        for analysis in analyses:
            if analysis:
                analysis_lower = analysis.lower()
                positive_count += sum(1 for indicator in positive_indicators if indicator in analysis_lower)
                negative_count += sum(1 for indicator in negative_indicators if indicator in analysis_lower)
        
        # Adjust rating based on indicators
        base_rating = 7
        if positive_count > negative_count:
            rating_data['overall_rating'] = min(10, base_rating + (positive_count - negative_count))
            rating_data['rating_rationale'] = 'Session showed positive therapeutic progress and engagement'
        elif negative_count > positive_count:
            rating_data['overall_rating'] = max(3, base_rating - (negative_count - positive_count))
            rating_data['rating_rationale'] = 'Session presented some challenges requiring attention'
        
        return rating_data
    
    def _identify_follow_up_actions(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Identify follow-up actions for the therapist"""
        actions = []
        analyses = [openai, anthropic, gemini]
        
        action_patterns = [
            r'follow[- ]?up[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'action items?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'therapist tasks?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])',
            r'recommendations?[:\s]*(.{30,200}?)(?=\n\n|\n[A-Z])'
        ]
        
        for analysis in analyses:
            if analysis:
                for pattern in action_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        action = match.group(1).strip()
                        action = re.sub(r'\s+', ' ', action)
                        if len(action) > 10 and action not in actions:
                            actions.append(action)
        
        return actions[:3]  # Return top 3 actions
    
    def _get_available_providers(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Get list of AI providers that provided analysis"""
        providers = []
        if openai: providers.append('OpenAI')
        if anthropic: providers.append('Anthropic')
        if gemini: providers.append('Gemini')
        return providers
    
    def _generate_error_summary(self, error_message: str) -> Dict:
        """Generate error summary when processing fails"""
        return {
            'error': True,
            'message': f'Failed to generate session summary: {error_message}',
            'session_overview': 'Summary generation failed',
            'key_insights': [],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'summary_version': '1.0',
                'status': 'error'
            }
        }