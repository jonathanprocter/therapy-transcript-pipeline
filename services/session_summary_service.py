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
        """Generate a comprehensive one-click session summary using AI-powered analysis"""
        try:
            logger.info(f"Generating session summary for transcript: {transcript_data.get('original_filename', 'Unknown')}")
            
            # Extract all available AI analyses
            openai_analysis = self._extract_analysis_text(transcript_data.get('openai_analysis'))
            anthropic_analysis = self._extract_analysis_text(transcript_data.get('anthropic_analysis'))
            gemini_analysis = self._extract_analysis_text(transcript_data.get('gemini_analysis'))
            
            # Get raw transcript content for enhanced AI processing
            raw_content = transcript_data.get('raw_content', '')
            client_name = transcript_data.get('client_name', 'Client')
            
            # If we have limited analysis data, use AI to generate enhanced summary
            if not openai_analysis and not anthropic_analysis and not gemini_analysis and raw_content:
                logger.info("Limited analysis data found, generating AI-enhanced summary from raw content")
                summary_data = self._generate_ai_enhanced_summary(raw_content, client_name)
            else:
                # Generate comprehensive summary from existing analyses
                summary_data = self._generate_from_existing_analyses(openai_analysis, anthropic_analysis, gemini_analysis, raw_content, client_name)
            
            # Enhance summary with AI-powered insights if service is available
            if self.ai_service and raw_content:
                summary_data = self._enhance_with_ai_insights(summary_data, raw_content, client_name)
            
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
    
    def _generate_ai_enhanced_summary(self, raw_content: str, client_name: str) -> Dict:
        """Generate enhanced summary using AI when limited analysis data is available"""
        try:
            # Use AI service to generate comprehensive analysis
            prompt = f"""
            As an expert clinical therapist, analyze this therapy session transcript and provide a comprehensive session summary.
            
            Client: {client_name}
            
            Transcript:
            {raw_content[:4000]}  # Limit for token efficiency
            
            Provide a detailed analysis including:
            1. Session overview and key themes
            2. Therapeutic insights and client presentation
            3. Progress indicators and goal achievement
            4. Interventions used and their effectiveness
            5. Risk assessment (suicide, self-harm, substance use)
            6. Clinical impressions and diagnostic considerations
            7. Session effectiveness rating (1-10) with rationale
            8. Recommendations for next session
            
            Format as JSON with detailed, clinically relevant insights.
            """
            
            if self.ai_service.is_openai_available():
                response = self.ai_service.generate_openai_response(prompt, "json_object")
                if response:
                    import json
                    ai_analysis = json.loads(response)
                    return self._format_ai_analysis(ai_analysis)
            
            # Fallback to structured analysis
            return self._generate_structured_fallback(raw_content, client_name)
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced summary generation: {str(e)}")
            return self._generate_structured_fallback(raw_content, client_name)
    
    def _generate_from_existing_analyses(self, openai: str, anthropic: str, gemini: str, raw_content: str, client_name: str) -> Dict:
        """Generate summary from existing AI analyses with enhanced processing"""
        return {
            'session_overview': self._generate_session_overview(openai, anthropic, gemini),
            'key_insights': self._extract_key_insights(openai, anthropic, gemini),
            'therapeutic_progress': self._assess_therapeutic_progress(openai, anthropic, gemini),
            'client_presentation': self._analyze_client_presentation(openai, anthropic, gemini),
            'session_goals': self._identify_session_goals(openai, anthropic, gemini),
            'interventions_used': self._extract_interventions(openai, anthropic, gemini),
            'homework_assignments': self._extract_homework(openai, anthropic, gemini),
            'risk_assessment': self._assess_risk_factors(openai, anthropic, gemini),
            'next_session_focus': self._plan_next_session(openai, anthropic, gemini),
            'clinical_impressions': self._extract_clinical_impressions(openai, anthropic, gemini),
            'session_rating': self._calculate_session_rating(openai, anthropic, gemini),
            'follow_up_actions': self._identify_follow_up_actions(openai, anthropic, gemini)
        }
    
    def _enhance_with_ai_insights(self, summary_data: Dict, raw_content: str, client_name: str) -> Dict:
        """Enhance existing summary with additional AI-powered insights"""
        try:
            if not self.ai_service.is_openai_available():
                return summary_data
            
            # Generate enhanced therapeutic insights
            insight_prompt = f"""
            As a senior clinical therapist, provide additional therapeutic insights for this session summary.
            
            Client: {client_name}
            Current Summary Overview: {summary_data.get('session_overview', 'Not available')}
            
            Raw Transcript Sample:
            {raw_content[:2000]}
            
            Provide:
            1. Specific therapeutic breakthroughs or significant moments
            2. Client's emotional regulation patterns observed
            3. Transference/countertransference dynamics if present
            4. Specific behavioral changes noted during session
            5. Treatment plan modifications recommended
            
            Be specific and clinically detailed, avoiding generic statements.
            """
            
            enhanced_insights = self.ai_service.generate_openai_response(insight_prompt)
            if enhanced_insights:
                if not summary_data.get('key_insights'):
                    summary_data['key_insights'] = []
                summary_data['key_insights'].append(f"Enhanced AI Analysis: {enhanced_insights}")
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error enhancing summary with AI insights: {str(e)}")
            return summary_data
    
    def _format_ai_analysis(self, ai_analysis: Dict) -> Dict:
        """Format AI analysis response into standardized summary structure"""
        return {
            'session_overview': ai_analysis.get('session_overview', 'AI analysis generated session overview'),
            'key_insights': ai_analysis.get('key_insights', []) if isinstance(ai_analysis.get('key_insights'), list) else [ai_analysis.get('key_insights', 'No insights available')],
            'therapeutic_progress': {
                'overall_progress': ai_analysis.get('progress_rating', 'Moderate'),
                'goal_achievement': ai_analysis.get('goal_progress', 'In Progress'),
                'specific_improvements': ai_analysis.get('improvements', []) if isinstance(ai_analysis.get('improvements'), list) else []
            },
            'session_goals': ai_analysis.get('session_goals', []) if isinstance(ai_analysis.get('session_goals'), list) else [],
            'interventions_used': ai_analysis.get('interventions', []) if isinstance(ai_analysis.get('interventions'), list) else [],
            'risk_assessment': {
                'suicide_risk': ai_analysis.get('suicide_risk', 'Low'),
                'self_harm_risk': ai_analysis.get('self_harm_risk', 'Low'),
                'substance_use': ai_analysis.get('substance_use', 'None reported')
            },
            'session_rating': {
                'overall_rating': ai_analysis.get('session_rating', 7),
                'rating_rationale': ai_analysis.get('rating_explanation', 'Session showed positive therapeutic engagement')
            },
            'next_session_focus': ai_analysis.get('next_session_recommendations', []) if isinstance(ai_analysis.get('next_session_recommendations'), list) else [],
            'clinical_impressions': ai_analysis.get('clinical_impressions', []) if isinstance(ai_analysis.get('clinical_impressions'), list) else []
        }
    
    def _generate_structured_fallback(self, raw_content: str, client_name: str) -> Dict:
        """Generate structured fallback summary when AI services are unavailable"""
        # Extract basic information from transcript
        content_length = len(raw_content)
        has_emotional_content = any(word in raw_content.lower() for word in ['anxious', 'depressed', 'angry', 'sad', 'happy', 'stressed'])
        
        return {
            'session_overview': f"Therapy session with {client_name}. Session transcript contains {content_length} characters of therapeutic dialogue.",
            'key_insights': [
                "Session included therapeutic dialogue and client-therapist interaction",
                "Emotional content detected" if has_emotional_content else "Clinical discussion documented"
            ],
            'therapeutic_progress': {
                'overall_progress': 'Assessment needed',
                'goal_achievement': 'Requires clinical review',
                'specific_improvements': []
            },
            'session_goals': ["Requires therapist review to identify specific goals"],
            'interventions_used': ["Clinical interventions documented in transcript"],
            'risk_assessment': {
                'suicide_risk': 'Requires clinical assessment',
                'self_harm_risk': 'Requires clinical assessment', 
                'substance_use': 'Not assessed in automated review'
            },
            'session_rating': {
                'overall_rating': 5,
                'rating_rationale': 'Automated assessment unavailable - requires therapist review'
            },
            'next_session_focus': ["Schedule clinical review of session content"],
            'clinical_impressions': ["Comprehensive clinical review recommended"]
        }
    
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
    
    def _clean_text(self, text: str) -> str:
        """Clean text from formatting issues and syntax errors"""
        if not text:
            return ""
        
        # Remove common syntax issues
        cleaned = re.sub(r'\\n\\n', ' ', text)  # Remove escaped newlines
        cleaned = re.sub(r'\\n', ' ', cleaned)  # Remove single escaped newlines
        cleaned = re.sub(r'\\"', '"', cleaned)  # Fix escaped quotes
        cleaned = re.sub(r'\\', '', cleaned)    # Remove remaining escapes
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = re.sub(r'\*+', '', cleaned)   # Remove asterisks
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _generate_session_overview(self, openai: str, anthropic: str, gemini: str) -> str:
        """Generate a comprehensive session overview"""
        analyses = [a for a in [openai, anthropic, gemini] if a and a.strip()]
        
        # Enhanced pattern matching for clinical content
        overview_patterns = [
            r'SUBJECTIVE[:\s]*(.{100,600}?)(?=OBJECTIVE|ASSESSMENT|PLAN|$)',
            r'Session Overview[:\s]*(.{100,500}?)(?=\n\n|\n[A-Z])',
            r'COMPREHENSIVE NARRATIVE SUMMARY[:\s]*(.{100,600}?)(?=\n\n|$)',
            r'Client presented[:\s]*(.{50,400}?)(?=\.|$)',
            r'During this session[:\s]*(.{50,400}?)(?=\.|$)',
            r'The client[:\s]*(.{50,400}?)(?=\.|$)',
            r'This (\d+[-\w\s]*) session[:\s]*(.{50,400}?)(?=\.|$)'
        ]
        
        for analysis in analyses:
            for pattern in overview_patterns:
                try:
                    match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    if match:
                        # Extract the content (may be in group 1 or 2 depending on pattern)
                        if len(match.groups()) > 1 and match.group(2):
                            overview = match.group(2)
                        else:
                            overview = match.group(1)
                        
                        if overview:
                            overview = self._clean_text(overview)
                            if len(overview) > 50:  # Ensure meaningful content
                                return overview[:500] + "..." if len(overview) > 500 else overview
                except Exception as e:
                    # Skip this pattern if regex fails
                    continue
        
        # If no structured overview found, extract key sentences
        for analysis in analyses:
            if analysis:
                try:
                    # Look for sentences with clinical keywords
                    sentences = re.split(r'[.!?]+', analysis)
                    clinical_sentences = []
                    keywords = ['client', 'patient', 'session', 'therapy', 'discussed', 'reported', 'expressed', 'anxiety', 'depression', 'coping', 'progress']
                    
                    for sentence in sentences:
                        if sentence and any(keyword in sentence.lower() for keyword in keywords) and len(sentence.strip()) > 30:
                            cleaned = self._clean_text(sentence.strip())
                            if len(cleaned) > 50:
                                clinical_sentences.append(cleaned)
                                if len(clinical_sentences) >= 2:
                                    break
                    
                    if clinical_sentences:
                        return '. '.join(clinical_sentences[:2]) + '.'
                except Exception as e:
                    # Skip this analysis if processing fails
                    continue
        
        return "Session focused on therapeutic progress and addressing client concerns."
    
    def _extract_key_insights(self, openai: str, anthropic: str, gemini: str) -> List[str]:
        """Extract key therapeutic insights from the session"""
        insights = []
        analyses = [a for a in [openai, anthropic, gemini] if a and a.strip()]
        
        # Use AI service for enhanced insight extraction if available
        if analyses and self.ai_service and self.ai_service.is_openai_available():
            combined_text = ' '.join(analyses)
            prompt = f"""
            As an expert clinical therapist, extract 3-5 key therapeutic insights from this session analysis.
            
            Analysis: {combined_text[:2500]}
            
            Focus on:
            - Significant therapeutic breakthroughs or moments
            - Client's coping mechanisms and emotional patterns
            - Treatment progress indicators
            - Behavioral observations
            - Clinical assessment findings
            
            Return only the insights as a numbered list, be specific and avoid generic statements.
            """
            ai_insights = self.ai_service.generate_openai_response(prompt)
            if ai_insights:
                # Parse numbered list
                insight_lines = [line.strip() for line in ai_insights.split('\n') if line.strip() and any(c.isdigit() for c in line[:3])]
                for line in insight_lines[:5]:  # Limit to 5 insights
                    # Remove numbering and clean up
                    cleaned = re.sub(r'^\d+\.?\s*', '', line).strip()
                    cleaned = self._clean_text(cleaned)
                    if len(cleaned) > 20:
                        insights.append(cleaned)
        
        # Fallback pattern matching if AI not available
        if not insights:
            insight_patterns = [
                r'Key insights?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])',
                r'Important observations?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])',
                r'Notable points?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])',
                r'Significant themes?[:\s]*(.{50,300}?)(?=\n\n|\n[A-Z])'
            ]
            
            for analysis in analyses:
                for pattern in insight_patterns:
                    matches = re.finditer(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        insight = match.group(1).strip()
                        insight = re.sub(r'\s+', ' ', insight)
                        if len(insight) > 20 and insight not in insights:
                            insights.append(insight)
        
        # If still no insights, extract from bullet points
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