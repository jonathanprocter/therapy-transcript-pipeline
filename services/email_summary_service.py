"""
Email summary service for therapy session review and follow-up
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class EmailSummaryService:
    """Service for generating and sending therapy session email summaries"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def generate_session_summary(self, transcript_data: Dict, ai_analysis: Dict) -> Dict:
        """Generate concise session summary for email review"""
        
        client_name = transcript_data.get('client_name', 'Client')
        session_date = transcript_data.get('session_date', 'Unknown Date')
        
        # Extract key information from AI analysis
        summary_data = self._extract_key_insights(ai_analysis)
        
        # Generate follow-up questions
        follow_up_questions = self._generate_follow_up_questions(summary_data, ai_analysis)
        
        # Generate reflection questions for client
        reflection_questions = self._generate_reflection_questions(summary_data, ai_analysis)
        
        # Create concise summary
        summary = {
            'client_name': client_name,
            'session_date': session_date,
            'session_summary': summary_data['brief_summary'],
            'key_themes': summary_data['key_themes'],
            'emotional_state': summary_data['emotional_assessment'],
            'progress_indicators': summary_data['progress_notes'],
            'areas_of_focus': summary_data['focus_areas'],
            'follow_up_questions': follow_up_questions,
            'reflection_questions': reflection_questions,
            'next_session_recommendations': self._generate_session_recommendations(summary_data),
            'generated_at': datetime.now().isoformat()
        }
        
        return summary
    
    def _extract_key_insights(self, ai_analysis: Dict) -> Dict:
        """Extract key insights from comprehensive AI analysis"""
        
        insights = {
            'brief_summary': '',
            'key_themes': [],
            'emotional_assessment': '',
            'progress_notes': '',
            'focus_areas': []
        }
        
        # Extract from different AI providers
        for provider in ['openai_analysis', 'anthropic_analysis', 'gemini_analysis']:
            provider_data = ai_analysis.get(provider, {})
            
            if not provider_data:
                continue
            
            # Extract from clinical progress note format
            if 'clinical_progress_note' in provider_data:
                content = provider_data['clinical_progress_note']
                insights.update(self._parse_clinical_content(content))
                break  # Use first available comprehensive analysis
        
        return insights
    
    def _parse_clinical_content(self, content: str) -> Dict:
        """Parse clinical progress note content for key insights"""
        
        parsed = {
            'brief_summary': '',
            'key_themes': [],
            'emotional_assessment': '',
            'progress_notes': '',
            'focus_areas': []
        }
        
        if not content:
            return parsed
        
        # Extract brief summary (first paragraph of subjective section)
        subjective_match = re.search(r'Subjective[:\s]+(.*?)(?=Objective|$)', content, re.DOTALL | re.IGNORECASE)
        if subjective_match:
            subjective_text = subjective_match.group(1).strip()
            # Take first 2-3 sentences
            sentences = re.split(r'[.!?]+', subjective_text)
            parsed['brief_summary'] = '. '.join(sentences[:3]).strip() + '.'
        
        # Extract emotional assessment from objective section
        objective_match = re.search(r'Objective[:\s]+(.*?)(?=Assessment|$)', content, re.DOTALL | re.IGNORECASE)
        if objective_match:
            objective_text = objective_match.group(1).strip()
            # Look for emotional/affective descriptions
            affect_sentences = [s for s in re.split(r'[.!?]+', objective_text) if any(word in s.lower() for word in ['affect', 'mood', 'emotional', 'feeling'])]
            if affect_sentences:
                parsed['emotional_assessment'] = affect_sentences[0].strip() + '.'
        
        # Extract progress notes from assessment section
        assessment_match = re.search(r'Assessment[:\s]+(.*?)(?=Plan|$)', content, re.DOTALL | re.IGNORECASE)
        if assessment_match:
            assessment_text = assessment_match.group(1).strip()
            sentences = re.split(r'[.!?]+', assessment_text)
            parsed['progress_notes'] = '. '.join(sentences[:2]).strip() + '.'
        
        # Extract key themes from thematic analysis
        themes_match = re.search(r'Key Points[:\s]+(.*?)(?=Significant Quotes|$)', content, re.DOTALL | re.IGNORECASE)
        if themes_match:
            themes_text = themes_match.group(1).strip()
            # Extract bullet points or numbered items
            themes = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', themes_text)
            parsed['key_themes'] = [theme.strip() for theme in themes[:5]]
        
        # Extract focus areas from plan section
        plan_match = re.search(r'Plan[:\s]+(.*?)(?=Supplemental|$)', content, re.DOTALL | re.IGNORECASE)
        if plan_match:
            plan_text = plan_match.group(1).strip()
            # Extract action items or focus areas
            focus_items = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', plan_text)
            parsed['focus_areas'] = [item.strip() for item in focus_items[:4]]
        
        return parsed
    
    def _generate_follow_up_questions(self, summary_data: Dict, ai_analysis: Dict) -> List[str]:
        """Generate follow-up questions for therapist to explore in next session"""
        
        questions = []
        
        # Questions based on key themes
        themes = summary_data.get('key_themes', [])
        for theme in themes[:2]:  # Limit to top 2 themes
            if 'relationship' in theme.lower():
                questions.append(f"How have your relationship patterns evolved since our last discussion about {theme.lower()}?")
            elif 'anxiety' in theme.lower() or 'stress' in theme.lower():
                questions.append(f"What specific situations have triggered anxiety for you this week, and how did you respond?")
            elif 'progress' in theme.lower() or 'improvement' in theme.lower():
                questions.append(f"What specific changes have you noticed in yourself since we discussed {theme.lower()}?")
            else:
                questions.append(f"Tell me more about how {theme.lower()} has been affecting you since our last session.")
        
        # Questions based on emotional state
        emotional_state = summary_data.get('emotional_assessment', '').lower()
        if 'anxious' in emotional_state or 'nervous' in emotional_state:
            questions.append("What has been your experience with the coping strategies we discussed for managing anxiety?")
        elif 'sad' in emotional_state or 'depressed' in emotional_state:
            questions.append("How has your mood been this week, and what moments stood out as particularly difficult or encouraging?")
        elif 'anger' in emotional_state or 'frustrated' in emotional_state:
            questions.append("Have you encountered situations that triggered anger or frustration, and how did you handle them?")
        
        # Questions based on progress areas
        focus_areas = summary_data.get('focus_areas', [])
        for area in focus_areas[:2]:
            if 'homework' in area.lower() or 'assignment' in area.lower():
                questions.append("How did you find completing the therapeutic exercises we discussed?")
            elif 'coping' in area.lower() or 'skill' in area.lower():
                questions.append("Which coping strategies have you found most helpful, and which have been challenging to implement?")
        
        # Ensure minimum number of questions
        if len(questions) < 3:
            questions.extend([
                "What has been on your mind most since our last session?",
                "Have you noticed any patterns in your thoughts or behaviors this week?",
                "What would you like to focus on in today's session?"
            ])
        
        return questions[:5]  # Limit to 5 questions
    
    def _generate_reflection_questions(self, summary_data: Dict, ai_analysis: Dict) -> List[str]:
        """Generate reflection questions for client to consider before next session"""
        
        questions = []
        
        # General reflection questions
        base_questions = [
            "What emotions have you experienced most frequently since our last session?",
            "What situations or interactions this week felt most challenging for you?",
            "When did you feel most like yourself this week?",
            "What patterns have you noticed in your thoughts or reactions?",
            "What would you like to work on or explore in our next session?"
        ]
        
        # Customized questions based on themes
        themes = summary_data.get('key_themes', [])
        for theme in themes[:2]:
            if 'relationship' in theme.lower():
                questions.append("How have your interactions with important people in your life felt this week?")
            elif 'work' in theme.lower() or 'career' in theme.lower():
                questions.append("What aspects of your work or career have been most prominent in your thoughts?")
            elif 'family' in theme.lower():
                questions.append("How have your family relationships or dynamics affected you this week?")
        
        # Combine and limit
        all_questions = questions + base_questions
        return all_questions[:6]  # Limit to 6 reflection questions
    
    def _generate_session_recommendations(self, summary_data: Dict) -> List[str]:
        """Generate recommendations for next session focus"""
        
        recommendations = []
        
        # Based on focus areas
        focus_areas = summary_data.get('focus_areas', [])
        for area in focus_areas[:3]:
            if 'EMDR' in area or 'trauma' in area.lower():
                recommendations.append("Continue EMDR therapy to address identified trauma responses")
            elif 'coping' in area.lower():
                recommendations.append("Review and practice coping strategies, introduce new techniques as needed")
            elif 'family' in area.lower():
                recommendations.append("Explore family dynamics and their impact on current emotional state")
            else:
                recommendations.append(f"Follow up on {area.lower()}")
        
        # General recommendations
        if len(recommendations) < 2:
            recommendations.extend([
                "Review progress since last session and adjust treatment goals",
                "Continue building therapeutic alliance and exploring client's current needs"
            ])
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def format_email_summary(self, summary_data: Dict) -> str:
        """Format summary data into readable email content"""
        
        client_name = summary_data.get('client_name', 'Client')
        session_date = summary_data.get('session_date', 'Unknown Date')
        
        email_content = f"""
THERAPY SESSION SUMMARY
Client: {client_name}
Session Date: {session_date}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

═══════════════════════════════════════════

SESSION OVERVIEW
{summary_data.get('session_summary', 'No summary available')}

EMOTIONAL STATE
{summary_data.get('emotional_state', 'No emotional assessment available')}

KEY THEMES ADDRESSED
"""
        
        themes = summary_data.get('key_themes', [])
        if themes:
            for i, theme in enumerate(themes, 1):
                email_content += f"{i}. {theme}\n"
        else:
            email_content += "No specific themes identified\n"
        
        email_content += f"""
PROGRESS NOTES
{summary_data.get('progress_indicators', 'No progress notes available')}

AREAS OF FOCUS
"""
        
        focus_areas = summary_data.get('areas_of_focus', [])
        if focus_areas:
            for i, area in enumerate(focus_areas, 1):
                email_content += f"{i}. {area}\n"
        else:
            email_content += "No specific focus areas identified\n"
        
        email_content += "\n" + "="*50 + "\n"
        email_content += "FOLLOW-UP QUESTIONS FOR NEXT SESSION\n"
        email_content += "="*50 + "\n\n"
        
        follow_ups = summary_data.get('follow_up_questions', [])
        for i, question in enumerate(follow_ups, 1):
            email_content += f"{i}. {question}\n\n"
        
        email_content += "\n" + "="*50 + "\n"
        email_content += "REFLECTION QUESTIONS FOR CLIENT\n"
        email_content += "="*50 + "\n\n"
        
        reflections = summary_data.get('reflection_questions', [])
        for i, question in enumerate(reflections, 1):
            email_content += f"{i}. {question}\n\n"
        
        email_content += "\n" + "="*50 + "\n"
        email_content += "NEXT SESSION RECOMMENDATIONS\n"
        email_content += "="*50 + "\n\n"
        
        recommendations = summary_data.get('next_session_recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            email_content += f"{i}. {rec}\n"
        
        email_content += f"""

═══════════════════════════════════════════
This summary was automatically generated from comprehensive therapy session analysis.
Please review before next session to inform treatment planning and session focus.
═══════════════════════════════════════════
"""
        
        return email_content
    
    def send_email_summary(self, summary_data: Dict, recipient_email: str, smtp_username: str, smtp_password: str) -> bool:
        """Send email summary to specified recipient"""
        
        try:
            # Format email content
            email_body = self.format_email_summary(summary_data)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = f"Session Summary: {summary_data.get('client_name', 'Client')} - {summary_data.get('session_date', 'Date Unknown')}"
            
            # Attach body
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            text = msg.as_string()
            server.sendmail(smtp_username, recipient_email, text)
            server.quit()
            
            logger.info(f"Email summary sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email summary: {str(e)}")
            return False
    
    def create_summary_for_transcript(self, transcript_id: int) -> Optional[Dict]:
        """Create summary for a specific transcript ID"""
        
        try:
            from models import Transcript
            from app import db
            
            # Get transcript data
            transcript = db.session.get(Transcript, transcript_id)
            if not transcript:
                logger.error(f"Transcript {transcript_id} not found")
                return None
            
            # Prepare transcript data
            transcript_data = {
                'client_name': transcript.client.name if transcript.client else 'Unknown Client',
                'session_date': transcript.session_date.isoformat() if transcript.session_date else 'Unknown Date',
                'raw_content': transcript.raw_content
            }
            
            # Prepare AI analysis data
            ai_analysis = {
                'openai_analysis': transcript.openai_analysis,
                'anthropic_analysis': transcript.anthropic_analysis,
                'gemini_analysis': transcript.gemini_analysis
            }
            
            # Generate summary
            summary = self.generate_session_summary(transcript_data, ai_analysis)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating summary for transcript {transcript_id}: {str(e)}")
            return None