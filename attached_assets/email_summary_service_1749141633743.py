"""
Email Summary Service for Therapy Progress Notes
Generates and sends comprehensive session summaries with action items
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

# Custom exception for service configuration issues
class ServiceNotConfiguredError(Exception):
    """Custom exception for when a service is not configured properly."""
    pass

class EmailSummaryService:
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.sendgrid_client = None  # Placeholder for the actual SendGrid client
        self.is_configured = False

        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not found. EmailSummaryService is not configured.")
        else:
            try:
                # In a real scenario, you would initialize the SendGrid client here:
                # from sendgrid import SendGridAPIClient
                # self.sendgrid_client = SendGridAPIClient(self.api_key)
                # For this subtask, we'll use a placeholder for an initialized client.
                # If the API key exists, we assume the client *could* be initialized.
                self.sendgrid_client = True # Placeholder indicating client *would be* initialized
                self.is_configured = True
                logger.info("EmailSummaryService configured (SendGrid client placeholder).")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client (placeholder): {e}")
                self.sendgrid_client = None # Ensure client is None if init fails
                self.is_configured = False
        
    def extract_session_summary(self, transcript_data: Dict) -> Dict:
        """Extract key information from AI analyses to create session summary"""
        try:
            # Combine all AI analyses - handle both string and dict formats
            openai_analysis = transcript_data.get('openai_analysis', '')
            if isinstance(openai_analysis, dict):
                openai_analysis = str(openai_analysis)
            
            anthropic_analysis = transcript_data.get('anthropic_analysis', '')
            if isinstance(anthropic_analysis, dict):
                anthropic_analysis = str(anthropic_analysis)
                
            gemini_analysis = transcript_data.get('gemini_analysis', '')
            if isinstance(gemini_analysis, dict):
                gemini_analysis = str(gemini_analysis)
            
            # Extract key components using pattern matching
            summary_data = {
                'session_overview': self._extract_session_overview(openai_analysis, anthropic_analysis),
                'key_topics': self._extract_key_topics(openai_analysis, anthropic_analysis, gemini_analysis),
                'therapeutic_insights': self._extract_therapeutic_insights(openai_analysis, anthropic_analysis),
                'action_items': self._extract_action_items(openai_analysis, anthropic_analysis, gemini_analysis),
                'follow_up_questions': self._generate_follow_up_questions(openai_analysis, anthropic_analysis),
                'next_session_focus': self._identify_next_session_focus(openai_analysis, anthropic_analysis, gemini_analysis),
                'significant_quotes': self._extract_significant_quotes(openai_analysis, anthropic_analysis),
                'progress_indicators': self._extract_progress_indicators(openai_analysis, anthropic_analysis, gemini_analysis)
            }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error extracting session summary: {str(e)}")
            return {}
    
    def _extract_session_overview(self, openai_analysis: str, anthropic_analysis: str) -> str:
        """Extract concise session overview"""
        # Look for subjective or assessment sections
        patterns = [
            r'SUBJECTIVE\s*(.{200,800}?)(?=OBJECTIVE|ASSESSMENT|$)',
            r'Session Overview\s*(.{200,600}?)(?=\n\n|\n[A-Z])',
            r'COMPREHENSIVE NARRATIVE SUMMARY\s*(.{200,800}?)(?=\n\n|$)'
        ]
        
        for pattern in patterns:
            for analysis in [openai_analysis, anthropic_analysis]:
                if analysis:
                    match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    if match:
                        overview = match.group(1).strip()
                        # Clean up and truncate
                        overview = re.sub(r'\s+', ' ', overview)
                        return overview[:400] + "..." if len(overview) > 400 else overview
        
        return "Session focused on therapeutic progress and client concerns."
    
    def _extract_key_topics(self, openai_analysis: str, anthropic_analysis: str, gemini_analysis: str) -> List[str]:
        """Extract key topics discussed in session"""
        topics = []
        
        # Look for thematic analysis sections
        patterns = [
            r'Thematic Analysis.*?(?=\n\n|[A-Z]{2,})',
            r'KEY POINTS\s*(.*?)(?=\n\n|[A-Z]{2,})',
            r'Major themes.*?(?=\n\n|[A-Z]{2,})'
        ]
        
        for analysis in [openai_analysis, anthropic_analysis, gemini_analysis]:
            if analysis:
                for pattern in patterns:
                    matches = re.findall(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        # Extract bullet points or numbered items
                        topic_items = re.findall(r'[•\-\*]\s*([^\n]{20,150})', match)
                        topics.extend(topic_items[:3])  # Limit to top 3 per analysis
        
        # Remove duplicates and clean up
        unique_topics = []
        for topic in topics:
            clean_topic = re.sub(r'\s+', ' ', topic.strip())
            if clean_topic not in unique_topics and len(clean_topic) > 10:
                unique_topics.append(clean_topic)
        
        return unique_topics[:6]  # Return top 6 topics
    
    def _extract_therapeutic_insights(self, openai_analysis: str, anthropic_analysis: str) -> List[str]:
        """Extract key therapeutic insights and interventions"""
        insights = []
        
        patterns = [
            r'ASSESSMENT\s*(.{100,500}?)(?=PLAN|$)',
            r'therapeutic.*?insights?\s*(.{100,400}?)(?=\n\n|[A-Z]{2,})',
            r'Clinical.*?observations?\s*(.{100,400}?)(?=\n\n|[A-Z]{2,})'
        ]
        
        for analysis in [openai_analysis, anthropic_analysis]:
            if analysis:
                for pattern in patterns:
                    match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    if match:
                        insight = match.group(1).strip()
                        insight = re.sub(r'\s+', ' ', insight)
                        if len(insight) > 50:
                            insights.append(insight[:200])
        
        return insights[:3]
    
    def _extract_action_items(self, openai_analysis: str, anthropic_analysis: str, gemini_analysis: str) -> List[str]:
        """Extract specific action items and homework assignments"""
        action_items = []
        
        patterns = [
            r'PLAN\s*(.*?)(?=\n\n|[A-Z]{2,}|$)',
            r'homework.*?assignments?\s*(.*?)(?=\n\n|[A-Z]{2,})',
            r'action.*?items?\s*(.*?)(?=\n\n|[A-Z]{2,})',
            r'follow-?up.*?appointments?\s*(.*?)(?=\n\n|[A-Z]{2,})'
        ]
        
        for analysis in [openai_analysis, anthropic_analysis, gemini_analysis]:
            if analysis:
                for pattern in patterns:
                    matches = re.findall(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        # Extract specific actionable items
                        items = re.findall(r'[•\-\*]\s*([^\n]{20,200})', match)
                        action_items.extend(items)
        
        # Clean and deduplicate
        unique_actions = []
        for item in action_items:
            clean_item = re.sub(r'\s+', ' ', item.strip())
            if clean_item not in unique_actions and len(clean_item) > 15:
                unique_actions.append(clean_item)
        
        return unique_actions[:5]
    
    def _generate_follow_up_questions(self, openai_analysis: str, anthropic_analysis: str) -> List[str]:
        """Generate follow-up questions for next session"""
        questions = []
        
        # Look for areas that need exploration
        patterns = [
            r'explore.*?further\s*(.{50,200}?)(?=\.|,|\n)',
            r'follow.*?up.*?on\s*(.{50,200}?)(?=\.|,|\n)',
            r'monitor.*?progress\s*(.{50,200}?)(?=\.|,|\n)'
        ]
        
        base_questions = [
            "How have you been feeling since our last session?",
            "What progress have you noticed with the strategies we discussed?",
            "Are there any new concerns or challenges that have come up?",
            "How effective were the coping techniques we practiced?"
        ]
        
        for analysis in [openai_analysis, anthropic_analysis]:
            if analysis:
                for pattern in patterns:
                    matches = re.findall(pattern, analysis, re.IGNORECASE)
                    for match in matches:
                        question = f"How has {match.strip().lower()} been progressing?"
                        if question not in questions:
                            questions.append(question)
        
        # Combine with base questions
        all_questions = base_questions + questions
        return all_questions[:6]
    
    def _identify_next_session_focus(self, openai_analysis: str, anthropic_analysis: str, gemini_analysis: str) -> List[str]:
        """Identify key focus areas for next session"""
        focus_areas = []
        
        patterns = [
            r'next.*?session.*?focus\s*(.{50,300}?)(?=\n\n|[A-Z]{2,})',
            r'continue.*?working.*?on\s*(.{50,200}?)(?=\.|,|\n)',
            r'areas.*?requiring.*?attention\s*(.{50,200}?)(?=\.|,|\n)'
        ]
        
        for analysis in [openai_analysis, anthropic_analysis, gemini_analysis]:
            if analysis:
                for pattern in patterns:
                    matches = re.findall(pattern, analysis, re.IGNORECASE | re.DOTALL)
                    focus_areas.extend(matches)
        
        # Clean and format
        cleaned_focus = []
        for area in focus_areas:
            clean_area = re.sub(r'\s+', ' ', area.strip())
            if len(clean_area) > 20 and clean_area not in cleaned_focus:
                cleaned_focus.append(clean_area)
        
        return cleaned_focus[:4]
    
    def _extract_significant_quotes(self, openai_analysis: str, anthropic_analysis: str) -> List[str]:
        """Extract significant client quotes"""
        quotes = []
        
        patterns = [
            r'"([^"]{30,200})"',
            r'SIGNIFICANT QUOTES\s*(.*?)(?=\n\n|[A-Z]{2,})'
        ]
        
        for analysis in [openai_analysis, anthropic_analysis]:
            if analysis:
                for pattern in patterns:
                    matches = re.findall(pattern, analysis, re.DOTALL)
                    for match in matches:
                        if isinstance(match, str) and len(match) > 30:
                            quotes.append(match.strip())
        
        return quotes[:3]
    
    def _extract_progress_indicators(self, openai_analysis: str, anthropic_analysis: str, gemini_analysis: str) -> List[str]:
        """Extract progress indicators and improvements"""
        indicators = []
        
        patterns = [
            r'progress.*?noted\s*(.{50,200}?)(?=\.|,|\n)',
            r'improvement.*?in\s*(.{50,200}?)(?=\.|,|\n)',
            r'positive.*?changes?\s*(.{50,200}?)(?=\.|,|\n)'
        ]
        
        for analysis in [openai_analysis, anthropic_analysis, gemini_analysis]:
            if analysis:
                for pattern in patterns:
                    matches = re.findall(pattern, analysis, re.IGNORECASE)
                    indicators.extend(matches)
        
        return [ind.strip() for ind in indicators[:4] if len(ind.strip()) > 20]
    
    def generate_email_content(self, client_name: str, session_date: str, summary_data: Dict) -> Dict:
        """Generate formatted email content"""
        
        subject = f"Therapy Session Summary - {client_name} - {session_date}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    Therapy Session Summary
                </h1>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5aa0;">Session Details</h3>
                    <p><strong>Client:</strong> {client_name}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <h3 style="color: #2c5aa0;">Session Overview</h3>
                <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #2c5aa0;">
                    {summary_data.get('session_overview', 'No overview available')}
                </p>
                
                <h3 style="color: #2c5aa0;">Key Topics Discussed</h3>
                <ul>
        """
        
        for topic in summary_data.get('key_topics', []):
            html_content += f"<li>{topic}</li>"
        
        html_content += """
                </ul>
                
                <h3 style="color: #2c5aa0;">Therapeutic Insights</h3>
                <ul>
        """
        
        for insight in summary_data.get('therapeutic_insights', []):
            html_content += f"<li>{insight}</li>"
        
        html_content += """
                </ul>
                
                <h3 style="color: #2c5aa0;">Action Items & Homework</h3>
                <ul>
        """
        
        for action in summary_data.get('action_items', []):
            html_content += f"<li>{action}</li>"
        
        html_content += """
                </ul>
                
                <h3 style="color: #2c5aa0;">Next Session Focus Questions</h3>
                <ol>
        """
        
        for question in summary_data.get('follow_up_questions', []):
            html_content += f"<li>{question}</li>"
        
        html_content += """
                </ol>
                
                <h3 style="color: #2c5aa0;">Areas for Next Session</h3>
                <ul>
        """
        
        for focus in summary_data.get('next_session_focus', []):
            html_content += f"<li>{focus}</li>"
        
        if summary_data.get('significant_quotes'):
            html_content += """
                </ul>
                
                <h3 style="color: #2c5aa0;">Significant Client Statements</h3>
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px;">
            """
            for quote in summary_data.get('significant_quotes', []):
                html_content += f'<p style="font-style: italic; margin: 10px 0;">"{quote}"</p>'
            html_content += "</div>"
        
        if summary_data.get('progress_indicators'):
            html_content += """
                <h3 style="color: #2c5aa0;">Progress Indicators</h3>
                <ul style="color: #28a745;">
            """
            for indicator in summary_data.get('progress_indicators', []):
                html_content += f"<li>{indicator}</li>"
            html_content += "</ul>"
        
        html_content += """
                <div style="margin-top: 30px; padding: 15px; background-color: #e7f3ff; border-radius: 5px;">
                    <p style="margin: 0; font-size: 12px; color: #666;">
                        This summary was automatically generated from AI analysis of the therapy session transcript. 
                        Please review for accuracy and supplement with your clinical observations as needed.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Generate plain text version
        text_content = f"""
THERAPY SESSION SUMMARY

Client: {client_name}
Date: {session_date}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

SESSION OVERVIEW
{summary_data.get('session_overview', 'No overview available')}

KEY TOPICS DISCUSSED
"""
        
        for i, topic in enumerate(summary_data.get('key_topics', []), 1):
            text_content += f"{i}. {topic}\n"
        
        text_content += "\nTHERAPEUTIC INSIGHTS\n"
        for i, insight in enumerate(summary_data.get('therapeutic_insights', []), 1):
            text_content += f"{i}. {insight}\n"
        
        text_content += "\nACTION ITEMS & HOMEWORK\n"
        for i, action in enumerate(summary_data.get('action_items', []), 1):
            text_content += f"{i}. {action}\n"
        
        text_content += "\nNEXT SESSION FOCUS QUESTIONS\n"
        for i, question in enumerate(summary_data.get('follow_up_questions', []), 1):
            text_content += f"{i}. {question}\n"
        
        text_content += "\nAREAS FOR NEXT SESSION\n"
        for i, focus in enumerate(summary_data.get('next_session_focus', []), 1):
            text_content += f"{i}. {focus}\n"
        
        if summary_data.get('significant_quotes'):
            text_content += "\nSIGNIFICANT CLIENT STATEMENTS\n"
            for quote in summary_data.get('significant_quotes', []):
                text_content += f'- "{quote}"\n'
        
        if summary_data.get('progress_indicators'):
            text_content += "\nPROGRESS INDICATORS\n"
            for indicator in summary_data.get('progress_indicators', []):
                text_content += f"- {indicator}\n"
        
        text_content += "\n---\nThis summary was automatically generated from AI analysis of the therapy session transcript."
        
        return {
            'subject': subject,
            'html_content': html_content,
            'text_content': text_content
        }
    
    def send_summary_email(self, recipient_email: str, email_content: Dict) -> bool:
        """Send the summary email using SendGrid"""
        if not self.is_configured or not self.sendgrid_client: # Check configuration and client
            logger.error("SendGrid client not configured or initialized. Cannot send email.")
            # Optionally raise ServiceNotConfiguredError here too, or just return False
            # For this refactor, raising in the public method is the primary goal.
            return False
            
        try:
            # Actual SendGrid client usage would be here.
            # from sendgrid import SendGridAPIClient # Already done in __init__ if real
            # from sendgrid.helpers.mail import Mail, Email, To, Content
            
            # sg = self.sendgrid_client # If it were the real client
            
            # The following is a placeholder for the actual email sending logic
            logger.info(f"Attempting to send email to {recipient_email} using SendGrid (placeholder).")
            logger.info(f"Subject: {email_content['subject']}")
            # In a real implementation:
            # message = Mail(
            #    from_email=Email("therapynotes@replit.app", "Therapy Notes System"),
            #    to_emails=To(recipient_email),
            #    subject=email_content['subject'],
            #    html_content=email_content['html_content'],
            #    plain_text_content=email_content['text_content']
            # )
            # response = sg.send(message)
            # if response.status_code in [200, 202]:
            #     logger.info(f"Summary email sent successfully to {recipient_email}")
            #     return True
            # else:
            #     logger.error(f"Failed to send email. Status code: {response.status_code}. Body: {response.body}")
            #     return False
            
            # Placeholder success
            return True 
            
        except Exception as e:
            logger.error(f"Error sending summary email: {str(e)}")
            return False
    
    def process_and_send_summary(self, transcript_data: Dict, recipient_email: str) -> bool:
        """Complete process: extract summary and send email"""
        if not self.is_configured:
            logger.error("EmailSummaryService.process_and_send_summary called but service is not configured.")
            raise ServiceNotConfiguredError("Email service is not configured: SENDGRID_API_KEY is missing or client initialization failed.")
            
        try:
            # Extract session summary
            summary_data = self.extract_session_summary(transcript_data)
                from_email=Email("therapynotes@replit.app", "Therapy Notes System"),
                to_emails=To(recipient_email),
                subject=email_content['subject']
            )
            
            # Add both HTML and text content
            
            # Generate email content
            client_name = transcript_data.get('client_name', 'Unknown Client')
            session_date = transcript_data.get('session_date', 'Unknown Date')
            
            email_content = self.generate_email_content(client_name, session_date, summary_data)
            
            # Send email
            return self.send_summary_email(recipient_email, email_content)
            
        except ServiceNotConfiguredError: # Re-raise if already handled
            raise
        except Exception as e:
            logger.error(f"Error in process_and_send_summary: {str(e)}")
            return False
            
            # Generate email content
            client_name = transcript_data.get('client_name', 'Unknown Client')
            session_date = transcript_data.get('session_date', 'Unknown Date')
            
            email_content = self.generate_email_content(client_name, session_date, summary_data)
            
            # Send email
            return self.send_summary_email(recipient_email, email_content)
            
        except Exception as e:
            logger.error(f"Error in process_and_send_summary: {str(e)}")
            return False