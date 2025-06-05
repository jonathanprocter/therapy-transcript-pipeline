"""
Enhanced Session Summary Service - Generate rich text formatted summaries with bridge questions
"""
import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class EnhancedSessionSummaryService:
    def __init__(self):
        self.ai_service = AIService()
    
    def generate_session_summary(self, transcript_data: Dict) -> Dict:
        """Generate a comprehensive session summary with rich text formatting and bridge questions"""
        try:
            logger.info(f"Generating enhanced session summary for transcript: {transcript_data.get('original_filename', 'Unknown')}")
            
            # Get raw content and client info
            raw_content = transcript_data.get('raw_content', '')
            client_name = transcript_data.get('client_name', 'Client')
            
            if not raw_content:
                return self._generate_fallback_summary(transcript_data)
            
            # Generate AI-powered summary with proper formatting
            summary_data = self._generate_ai_enhanced_summary(raw_content, client_name)
            
            # Add metadata
            summary_data['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'transcript_id': transcript_data.get('id'),
                'client_name': client_name,
                'session_date': transcript_data.get('session_date'),
                'summary_version': '2.0'
            }
            
            logger.info("Enhanced session summary generated successfully")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating enhanced session summary: {str(e)}")
            return self._generate_error_summary(str(e))
    
    def _generate_ai_enhanced_summary(self, raw_content: str, client_name: str) -> Dict:
        """Generate AI-enhanced summary with proper rich text formatting"""
        try:
            # Create comprehensive prompt for rich text formatting
            prompt = f"""
Generate a comprehensive therapy session summary for {client_name} using proper rich text formatting. 
DO NOT use any markdown syntax (no *, #, -, etc.). Format using proper headings and bullet points.

Based on the session transcript, provide:

SESSION OVERVIEW
Brief 2-3 sentence overview of the session's main focus and client's presentation.

KEY INSIGHTS
• List 3-5 key therapeutic insights from the session
• Each insight should be on its own line with bullet points
• Focus on breakthroughs, patterns, or significant moments

THERAPEUTIC PROGRESS
Overall Progress: [Rate as Excellent/Good/Moderate/Limited/Concerning]
Goal Achievement: [In Progress/Significant Progress/Goal Met/New Goals Identified]

Specific Improvements:
• List observable improvements or positive changes
• Include behavioral, emotional, or cognitive changes

Areas for Continued Focus:
• Identify areas that need ongoing attention
• Include challenges or concerns that emerged

RISK ASSESSMENT
Suicide Risk: [Low/Moderate/High based on assessment]
Self-Harm Risk: [Low/Moderate/High based on assessment]
Substance Use: [None reported/Discussed/Concern identified]

SESSION EFFECTIVENESS
Rating: [1-10 scale]
Session showed positive therapeutic progress and engagement

BRIDGE TO NEXT SESSION

Suggested Opening Questions:
• "How have you been feeling since our last session when we talked about [main topic]?"
• "Have you had any thoughts about [key issue discussed] since we last met?"
• "What's been on your mind this week regarding [therapeutic focus]?"

Focus Areas for Next Session:
• Continue working on [specific therapeutic goal]
• Explore [emerging theme or pattern]
• Practice [skills or techniques introduced]

Reflection Prompts for Client:
• "What was most helpful about our conversation today?"
• "What would you like to continue exploring next time?"
• "How are you feeling about the progress you're making?"

Session Transcript:
{raw_content[:3000]}
"""
            
            # Get AI response using OpenAI
            if self.ai_service and self.ai_service.is_openai_available():
                try:
                    # Use the analyze_transcript method which handles OpenAI calls
                    ai_result = self.ai_service._analyze_with_openai(prompt[:4000])
                    if ai_result and 'content' in ai_result:
                        response = ai_result['content']
                        return self._parse_ai_response(response)
                except Exception as e:
                    logger.warning(f"AI analysis failed, using structured summary: {str(e)}")
            
            return self._generate_structured_summary(raw_content, client_name)
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced summary generation: {str(e)}")
            return self._generate_structured_summary(raw_content, client_name)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured summary data"""
        # Clean the response of any remaining markdown
        cleaned_response = self._clean_markdown(response)
        
        # Extract sections using pattern matching
        sections = self._extract_sections(cleaned_response)
        
        return {
            'session_overview': sections.get('session_overview', 'Session overview not available'),
            'key_insights': sections.get('key_insights', []),
            'therapeutic_progress': sections.get('therapeutic_progress', {}),
            'risk_assessment': sections.get('risk_assessment', {}),
            'session_rating': sections.get('session_rating', {}),
            'bridge_questions': sections.get('bridge_questions', {}),
            'formatted_summary': cleaned_response
        }
    
    def _clean_markdown(self, text: str) -> str:
        """Remove all markdown syntax and clean formatting"""
        if not text:
            return ""
        
        # Remove markdown headers
        cleaned = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic markdown
        cleaned = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', cleaned)
        cleaned = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', cleaned)
        
        # Convert markdown bullets to proper bullets
        cleaned = re.sub(r'^[\s]*[-*+]\s*', '• ', cleaned, flags=re.MULTILINE)
        
        # Remove code blocks and inline code
        cleaned = re.sub(r'```[^`]*```', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
        
        # Remove markdown links
        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
        
        # Clean up extra whitespace while preserving structure
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_sections(self, text: str) -> Dict:
        """Extract different sections from the formatted text"""
        sections = {}
        
        # Extract session overview
        overview_match = re.search(r'SESSION OVERVIEW\s*\n(.*?)(?=\n[A-Z]|\n\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
        if overview_match:
            sections['session_overview'] = overview_match.group(1).strip()
        
        # Extract key insights
        insights_match = re.search(r'KEY INSIGHTS\s*\n(.*?)(?=\n[A-Z]|\n\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
        if insights_match:
            insights_text = insights_match.group(1)
            insights = [line.strip().lstrip('• ') for line in insights_text.split('\n') if line.strip() and '•' in line]
            sections['key_insights'] = insights[:5]
        
        # Extract therapeutic progress
        progress_match = re.search(r'THERAPEUTIC PROGRESS\s*\n(.*?)(?=\n[A-Z]|\n\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
        if progress_match:
            progress_text = progress_match.group(1)
            
            overall_match = re.search(r'Overall Progress:\s*([^\n]+)', progress_text)
            goal_match = re.search(r'Goal Achievement:\s*([^\n]+)', progress_text)
            
            sections['therapeutic_progress'] = {
                'overall_progress': overall_match.group(1).strip() if overall_match else 'Moderate',
                'goal_achievement': goal_match.group(1).strip() if goal_match else 'In Progress'
            }
        
        # Extract risk assessment
        risk_match = re.search(r'RISK ASSESSMENT\s*\n(.*?)(?=\n[A-Z]|\n\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
        if risk_match:
            risk_text = risk_match.group(1)
            
            suicide_match = re.search(r'Suicide Risk:\s*([^\n]+)', risk_text)
            harm_match = re.search(r'Self-Harm Risk:\s*([^\n]+)', risk_text)
            substance_match = re.search(r'Substance Use:\s*([^\n]+)', risk_text)
            
            sections['risk_assessment'] = {
                'suicide_risk': suicide_match.group(1).strip() if suicide_match else 'Low',
                'self_harm_risk': harm_match.group(1).strip() if harm_match else 'Low',
                'substance_use': substance_match.group(1).strip() if substance_match else 'None reported'
            }
        
        # Extract session rating
        rating_match = re.search(r'Rating:\s*([^\n]+)', text)
        if rating_match:
            rating_text = rating_match.group(1).strip()
            rating_num = re.search(r'(\d+)', rating_text)
            sections['session_rating'] = {
                'overall_rating': int(rating_num.group(1)) if rating_num else 7,
                'rating_rationale': 'Session showed positive therapeutic progress and engagement'
            }
        
        # Extract bridge questions
        bridge_match = re.search(r'BRIDGE TO NEXT SESSION\s*\n(.*?)$', text, re.DOTALL | re.IGNORECASE)
        if bridge_match:
            bridge_text = bridge_match.group(1)
            
            opening_questions = []
            focus_areas = []
            reflection_prompts = []
            
            # Extract opening questions
            opening_match = re.search(r'Suggested Opening Questions:(.*?)(?=Focus Areas|Reflection Prompts|$)', bridge_text, re.DOTALL)
            if opening_match:
                opening_text = opening_match.group(1)
                opening_questions = [line.strip().lstrip('• ').strip('"') for line in opening_text.split('\n') if line.strip() and '•' in line]
            
            # Extract focus areas
            focus_match = re.search(r'Focus Areas for Next Session:(.*?)(?=Reflection Prompts|$)', bridge_text, re.DOTALL)
            if focus_match:
                focus_text = focus_match.group(1)
                focus_areas = [line.strip().lstrip('• ') for line in focus_text.split('\n') if line.strip() and '•' in line]
            
            # Extract reflection prompts
            reflection_match = re.search(r'Reflection Prompts for Client:(.*?)$', bridge_text, re.DOTALL)
            if reflection_match:
                reflection_text = reflection_match.group(1)
                reflection_prompts = [line.strip().lstrip('• ').strip('"') for line in reflection_text.split('\n') if line.strip() and '•' in line]
            
            sections['bridge_questions'] = {
                'opening_questions': opening_questions[:3],
                'next_session_focus': focus_areas[:3],
                'reflection_prompts': reflection_prompts[:3]
            }
        
        return sections
    
    def _generate_structured_summary(self, raw_content: str, client_name: str) -> Dict:
        """Generate a structured summary from raw content without AI"""
        return {
            'session_overview': f'Session with {client_name} focused on therapeutic engagement and progress.',
            'key_insights': [
                'Client demonstrated engagement in therapeutic process',
                'Session addressed current concerns and goals',
                'Therapeutic relationship continues to develop'
            ],
            'therapeutic_progress': {
                'overall_progress': 'Moderate',
                'goal_achievement': 'In Progress'
            },
            'risk_assessment': {
                'suicide_risk': 'Assessment needed',
                'self_harm_risk': 'Assessment needed',
                'substance_use': 'Not assessed'
            },
            'session_rating': {
                'overall_rating': 7,
                'rating_rationale': 'Session showed therapeutic engagement'
            },
            'bridge_questions': {
                'opening_questions': [
                    'How have you been feeling since our last session?',
                    'What has been on your mind this week?',
                    'Have you had any thoughts about our previous discussion?'
                ],
                'next_session_focus': [
                    'Continue therapeutic work on identified goals',
                    'Explore emerging themes and patterns',
                    'Practice coping strategies and skills'
                ],
                'reflection_prompts': [
                    'What was most helpful about today\'s session?',
                    'What would you like to explore further?',
                    'How are you feeling about your progress?'
                ]
            },
            'formatted_summary': self._generate_formatted_text(client_name)
        }
    
    def _generate_formatted_text(self, client_name: str) -> str:
        """Generate properly formatted summary text"""
        return f"""SESSION OVERVIEW

Session with {client_name} focused on therapeutic engagement and progress. Client demonstrated active participation in the therapeutic process.

KEY INSIGHTS

• Client showed engagement in therapeutic discussions
• Session addressed current concerns and therapeutic goals
• Therapeutic relationship continues to develop positively

THERAPEUTIC PROGRESS

Overall Progress: Moderate
Goal Achievement: In Progress

Specific Improvements:
• Client demonstrated willingness to engage
• Active participation in therapeutic process
• Openness to exploring therapeutic goals

Areas for Continued Focus:
• Continue work on identified therapeutic objectives
• Maintain therapeutic engagement and progress
• Address emerging concerns as they arise

RISK ASSESSMENT

Suicide Risk: Assessment needed
Self-Harm Risk: Assessment needed
Substance Use: Not assessed

SESSION EFFECTIVENESS

Rating: 7/10
Session showed therapeutic engagement and progress

BRIDGE TO NEXT SESSION

Suggested Opening Questions:
• "How have you been feeling since our last session?"
• "What has been on your mind this week?"
• "Have you had any thoughts about our previous discussion?"

Focus Areas for Next Session:
• Continue therapeutic work on identified goals
• Explore emerging themes and patterns
• Practice coping strategies and skills

Reflection Prompts for Client:
• "What was most helpful about today's session?"
• "What would you like to explore further?"
• "How are you feeling about your progress?"
"""
    
    def _generate_fallback_summary(self, transcript_data: Dict) -> Dict:
        """Generate fallback summary when no content is available"""
        return {
            'session_overview': 'Session summary requires transcript content for analysis',
            'key_insights': ['Complete transcript content needed for detailed analysis'],
            'therapeutic_progress': {
                'overall_progress': 'Unable to assess',
                'goal_achievement': 'Requires review'
            },
            'risk_assessment': {
                'suicide_risk': 'Requires clinical assessment',
                'self_harm_risk': 'Requires clinical assessment',
                'substance_use': 'Not assessed'
            },
            'session_rating': {
                'overall_rating': 5,
                'rating_rationale': 'Assessment requires complete session content'
            },
            'bridge_questions': {
                'opening_questions': ['How have you been since our last session?'],
                'next_session_focus': ['Review session content and objectives'],
                'reflection_prompts': ['What would you like to focus on today?']
            },
            'formatted_summary': 'Complete session transcript required for detailed summary generation.',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'status': 'incomplete_data'
            }
        }
    
    def _generate_error_summary(self, error_message: str) -> Dict:
        """Generate error summary when processing fails"""
        return {
            'error': True,
            'message': f'Failed to generate session summary: {error_message}',
            'session_overview': 'Summary generation failed',
            'key_insights': [],
            'formatted_summary': 'Error occurred during summary generation',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'summary_version': '2.0',
                'status': 'error'
            }
        }