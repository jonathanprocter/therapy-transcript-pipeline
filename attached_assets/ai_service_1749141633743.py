import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import openai
import anthropic
import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)

class AIService:
    """Service for coordinating multiple AI providers for transcript analysis"""
    
    def __init__(self):
        self.openai_client = self._initialize_openai()
        self.anthropic_client = self._initialize_anthropic()
        self.gemini_client = self._initialize_gemini()
        
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = Config.OPENAI_API_KEY
            if not api_key:
                logger.warning("OpenAI API key not found")
                return None
            
            client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            return None
    
    def _initialize_anthropic(self):
        """Initialize Anthropic client"""
        try:
            api_key = Config.ANTHROPIC_API_KEY
            if not api_key:
                logger.warning("Anthropic API key not found")
                return None
            
            client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {str(e)}")
            return None
    
    def _initialize_gemini(self):
        """Initialize Google Gemini client"""
        try:
            api_key = Config.GEMINI_API_KEY
            if not api_key:
                logger.warning("Gemini API key not found")
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            logger.info("Gemini client initialized successfully")
            return model
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            return None
    
    def analyze_transcript(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using all available AI providers"""
        analysis_results = {
            'openai_analysis': None,
            'anthropic_analysis': None,
            'gemini_analysis': None,
            'consolidated_insights': None,
            'processing_errors': []
        }
        
        # OpenAI Analysis
        if self.openai_client:
            try:
                analysis_results['openai_analysis'] = self._analyze_with_openai(transcript_content, client_name)
                logger.info("OpenAI analysis completed successfully")
            except Exception as e:
                error_msg = f"OpenAI analysis failed: {str(e)}"
                logger.error(error_msg)
                analysis_results['processing_errors'].append(error_msg)
        
        # Anthropic Analysis
        if self.anthropic_client:
            try:
                analysis_results['anthropic_analysis'] = self._analyze_with_anthropic(transcript_content, client_name)
                logger.info("Anthropic analysis completed successfully")
            except Exception as e:
                error_msg = f"Anthropic analysis failed: {str(e)}"
                logger.error(error_msg)
                analysis_results['processing_errors'].append(error_msg)
        
        # Gemini Analysis
        if self.gemini_client:
            try:
                analysis_results['gemini_analysis'] = self._analyze_with_gemini(transcript_content, client_name)
                logger.info("Gemini analysis completed successfully")
            except Exception as e:
                error_msg = f"Gemini analysis failed: {str(e)}"
                logger.error(error_msg)
                analysis_results['processing_errors'].append(error_msg)
        
        # Consolidate insights from all providers
        analysis_results['consolidated_insights'] = self._consolidate_insights(analysis_results)
        
        return analysis_results
    
    def _analyze_with_openai(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using OpenAI GPT"""
        try:
            prompt = f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript_content}"
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert clinical therapist with extensive training in psychotherapy and clinical documentation. Create comprehensive clinical progress notes using the full depth of your clinical expertise."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for clinical precision
                max_tokens=4096  # Maximum tokens for comprehensive analysis
            )
            
            # Return the comprehensive clinical note as text
            content = response.choices[0].message.content
            result = {
                'clinical_progress_note': content,
                'provider': 'openai',
                'model': Config.OPENAI_MODEL,
                'analysis_type': 'comprehensive_clinical'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {str(e)}")
            raise
    
    def _analyze_with_anthropic(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using Anthropic Claude"""
        try:
            prompt = f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript_content}"
            
            response = self.anthropic_client.messages.create(
                model=Config.ANTHROPIC_MODEL,  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                max_tokens=8192,  # Maximum tokens for comprehensive clinical analysis
                temperature=0.2,  # Lower temperature for clinical precision
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Return the comprehensive clinical note as text
            content = response.content[0].text
            result = {
                'clinical_progress_note': content,
                'provider': 'anthropic',
                'model': Config.ANTHROPIC_MODEL,
                'analysis_type': 'comprehensive_clinical'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Anthropic analysis error: {str(e)}")
            raise
    
    def _analyze_with_gemini(self, transcript_content: str, client_name: str = None) -> Dict:
        """Analyze transcript using Google Gemini"""
        try:
            prompt = f"{Config.THERAPY_ANALYSIS_PROMPT}\n\n{transcript_content}"
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000,
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            result['provider'] = 'gemini'
            result['model'] = Config.GEMINI_MODEL
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {str(e)}")
            raise
    
    def _consolidate_insights(self, analysis_results: Dict) -> Dict:
        """Consolidate insights from multiple AI providers"""
        try:
            consolidated = {
                'session_summary': '',
                'client_mood': 0,
                'key_topics': [],
                'therapeutic_techniques': [],
                'sentiment_analysis': {},
                'confidence_scores': {},
                'provider_consensus': {},
                'consolidated_at': None
            }
            
            valid_analyses = []
            for provider in ['openai_analysis', 'anthropic_analysis', 'gemini_analysis']:
                if analysis_results.get(provider) and isinstance(analysis_results[provider], dict):
                    valid_analyses.append(analysis_results[provider])
            
            if not valid_analyses:
                return consolidated
            
            # Consolidate session summaries
            summaries = [analysis.get('session_summary', '') for analysis in valid_analyses if analysis.get('session_summary')]
            if summaries:
                consolidated['session_summary'] = self._merge_summaries(summaries)
            
            # Average mood scores
            mood_scores = [analysis.get('client_mood') for analysis in valid_analyses if analysis.get('client_mood')]
            if mood_scores:
                # Convert string scores to numbers if needed
                numeric_scores = []
                for score in mood_scores:
                    try:
                        if isinstance(score, str):
                            score = float(score)
                        numeric_scores.append(score)
                    except (ValueError, TypeError):
                        continue
                
                if numeric_scores:
                    consolidated['client_mood'] = round(sum(numeric_scores) / len(numeric_scores), 1)
            
            # Merge key topics
            all_topics = []
            for analysis in valid_analyses:
                topics = analysis.get('key_topics', [])
                if isinstance(topics, list):
                    all_topics.extend(topics)
            consolidated['key_topics'] = list(set(all_topics))  # Remove duplicates
            
            # Merge therapeutic techniques
            all_techniques = []
            for analysis in valid_analyses:
                techniques = analysis.get('therapeutic_techniques', [])
                if isinstance(techniques, list):
                    all_techniques.extend(techniques)
            consolidated['therapeutic_techniques'] = list(set(all_techniques))
            
            # Consolidate sentiment analysis
            sentiments = [analysis.get('sentiment_analysis', {}) for analysis in valid_analyses if analysis.get('sentiment_analysis')]
            if sentiments:
                consolidated['sentiment_analysis'] = self._merge_sentiment_analysis(sentiments)
            
            # Calculate confidence scores based on agreement between providers
            consolidated['confidence_scores'] = self._calculate_confidence_scores(valid_analyses)
            
            consolidated['consolidated_at'] = None  # Will be set by the calling function
            
            return consolidated
            
        except Exception as e:
            logger.error(f"Error consolidating insights: {str(e)}")
            return {}
    
    def _merge_summaries(self, summaries: List[str]) -> str:
        """Merge multiple session summaries"""
        if len(summaries) == 1:
            return summaries[0]
        
        # For now, return the longest summary as it's likely most comprehensive
        return max(summaries, key=len)
    
    def _merge_sentiment_analysis(self, sentiments: List[Dict]) -> Dict:
        """Merge sentiment analyses from multiple providers"""
        merged = {
            'overall_sentiment': 'neutral',
            'emotional_tone': '',
            'engagement_level': 'medium'
        }
        
        # Count sentiment votes
        sentiment_votes = {}
        for sentiment in sentiments:
            overall = sentiment.get('overall_sentiment', 'neutral')
            sentiment_votes[overall] = sentiment_votes.get(overall, 0) + 1
        
        if sentiment_votes:
            merged['overall_sentiment'] = max(sentiment_votes, key=sentiment_votes.get)
        
        # Merge emotional tones
        tones = [s.get('emotional_tone', '') for s in sentiments if s.get('emotional_tone')]
        if tones:
            merged['emotional_tone'] = ', '.join(set(tones))
        
        return merged
    
    def _calculate_confidence_scores(self, analyses: List[Dict]) -> Dict:
        """Calculate confidence scores based on agreement between providers"""
        if len(analyses) < 2:
            return {'overall_confidence': 0.5}
        
        # Simple agreement scoring
        agreements = 0
        total_comparisons = 0
        
        # Compare mood scores
        mood_scores = [a.get('client_mood') for a in analyses if a.get('client_mood')]
        if len(mood_scores) >= 2:
            mood_variance = max(mood_scores) - min(mood_scores) if mood_scores else 0
            if mood_variance <= 2:  # Close agreement
                agreements += 1
            total_comparisons += 1
        
        # Compare sentiment
        sentiments = [a.get('sentiment_analysis', {}).get('overall_sentiment') for a in analyses]
        sentiment_agreement = len(set(filter(None, sentiments))) <= 1
        if sentiment_agreement:
            agreements += 1
        total_comparisons += 1
        
        confidence = agreements / total_comparisons if total_comparisons > 0 else 0.5
        
        return {
            'overall_confidence': round(confidence, 2),
            'provider_count': len(analyses),
            'agreement_ratio': f"{agreements}/{total_comparisons}"
        }
    
    def analyze_longitudinal_progress(self, session_data: List[Dict]) -> Dict:
        """Analyze progress across multiple therapy sessions"""
        try:
            if not session_data or len(session_data) < 2:
                return {'error': 'Insufficient data for longitudinal analysis'}
            
            # Prepare data for analysis
            session_summaries = []
            for session in session_data:
                summary = {
                    'date': session.get('session_date'),
                    'mood': session.get('sentiment_score'),
                    'themes': session.get('key_themes', []),
                    'insights': session.get('therapy_insights', {})
                }
                session_summaries.append(summary)
            
            # Use the best available AI provider for longitudinal analysis
            prompt = f"{Config.LONGITUDINAL_ANALYSIS_PROMPT}\n\n{json.dumps(session_summaries, indent=2)}"
            
            if self.openai_client:
                return self._longitudinal_analysis_openai(prompt)
            elif self.anthropic_client:
                return self._longitudinal_analysis_anthropic(prompt)
            elif self.gemini_client:
                return self._longitudinal_analysis_gemini(prompt)
            else:
                return {'error': 'No AI providers available for analysis'}
                
        except Exception as e:
            logger.error(f"Longitudinal analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _longitudinal_analysis_openai(self, prompt: str) -> Dict:
        """Perform longitudinal analysis using OpenAI"""
        response = self.openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert therapist analyzing long-term client progress. Provide insights in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1500
        )
        
        result = json.loads(response.choices[0].message.content)
        result['analysis_provider'] = 'openai'
        return result
    
    def _longitudinal_analysis_anthropic(self, prompt: str) -> Dict:
        """Perform longitudinal analysis using Anthropic"""
        response = self.anthropic_client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=1500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.content[0].text)
        result['analysis_provider'] = 'anthropic'
        return result
    
    def _longitudinal_analysis_gemini(self, prompt: str) -> Dict:
        """Perform longitudinal analysis using Gemini"""
        response = self.gemini_client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        result['analysis_provider'] = 'gemini'
        return result

    def _call_openai_llm(self, prompt: str, response_format: str = "text", model: Optional[str] = None) -> Optional[str]:
        """
        Helper function to call OpenAI LLM with a specific prompt and desired response format.
        Returns the string content from LLM or None if an error occurs.
        'response_format' can be "text" or "json_object".
        """
        if not self.openai_client:
            logger.error("OpenAI client not available for LLM call.")
            return None
        
        selected_model = model or Config.OPENAI_MODEL # Default to general model if not specified
        if response_format == "json_object" and "gpt-3.5" in selected_model and selected_model != "gpt-3.5-turbo-1106" and selected_model != "gpt-3.5-turbo-0125":
            # Fallback to a model known to reliably support JSON mode if a less capable gpt-3.5 is chosen
            # Or, use gpt-4o if available and configured
            logger.warning(f"Model {selected_model} may not fully support JSON mode. Consider using gpt-4o or gpt-3.5-turbo-1106/0125 for reliable JSON output.")
            # selected_model = Config.OPENAI_DEFAULT_JSON_MODEL or "gpt-3.5-turbo-1106" # Ensure this is a valid model

        try:
            messages = [{"role": "user", "content": prompt}]
            if "gpt-3.5" not in selected_model and "gpt-4" not in selected_model : # Older models might not use this chat structure
                 # This part would need to be adapted if using very old models. Assuming current chat models.
                 pass

            completion_args = {
                "model": selected_model,
                "messages": messages,
                "temperature": 0.2, # Low temperature for factual extraction
                "max_tokens": 1000  # Adjust as needed based on expected output size
            }
            if response_format == "json_object":
                completion_args["response_format"] = {"type": "json_object"}
            
            response = self.openai_client.chat.completions.create(**completion_args)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling OpenAI LLM (model: {selected_model}, format: {response_format}): {e}")
            return None

    def analyze_transcript_detailed(self, transcript_text: str, client_name: Optional[str] = None) -> Dict:
        """
        Performs a comprehensive analysis of a single transcript using OpenAI
        to extract various structured data points.
        """
        results = {
            "session_complaints": [],
            "session_concerns": [],
            "session_action_items": [],
            "session_presentation_summary": None,
            "key_themes": [],
            "therapy_insights_summary": None, # More specific name
            "sentiment_score": None,
            "raw_openai_clinical_note": None # To store the general clinical note
        }

        if not self.openai_client:
            logger.error("OpenAI client not available for detailed transcript analysis.")
            return results # Return default empty results

        # 1. General Clinical Note (similar to existing _analyze_with_openai)
        try:
            clinical_note_prompt = f"{Config.THERAPY_ANALYSIS_PROMPT}\n\nTranscript:\n{transcript_text}"
            if client_name:
                clinical_note_prompt = f"Client Name: {client_name}\n{clinical_note_prompt}"
            
            # Using the main configured OpenAI model for this general note
            raw_note = self._call_openai_llm(clinical_note_prompt, model=Config.OPENAI_MODEL)
            if raw_note:
                results["raw_openai_clinical_note"] = raw_note
                # Simple way to get a summary for therapy_insights_summary from the note
                # This could be a separate, more targeted prompt if needed
                if len(raw_note) > 150: # Basic summary if long
                    results["therapy_insights_summary"] = raw_note[:147] + "..." 
                else:
                    results["therapy_insights_summary"] = raw_note
        except Exception as e:
            logger.error(f"Error generating general clinical note: {e}")


        # 2. Session Complaints (JSON list)
        try:
            complaints_prompt = (
                "Based on the following therapy session transcript, identify and list any specific problems "
                "or chief complaints explicitly stated by the client or identified by the therapist as primary issues for this session. "
                "Focus on direct statements of distress, problems, or symptoms. "
                "Format the output as a JSON object with a single key \"complaints\" containing a list of strings. "
                "Each string should be a concise summary of a distinct complaint. "
                "If no specific complaints are identified, return an empty list under the \"complaints\" key.\n\n"
                f"Transcript:\n{transcript_text}\n\nJSON Output:"
            )
            raw_complaints_json_str = self._call_openai_llm(complaints_prompt, response_format="json_object", model=Config.OPENAI_JSON_ extracción_MODEL or "gpt-3.5-turbo-0125")
            if raw_complaints_json_str:
                try:
                    complaints_data = json.loads(raw_complaints_json_str)
                    if isinstance(complaints_data.get("complaints"), list):
                        results["session_complaints"] = [str(item) for item in complaints_data["complaints"]]
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON for session_complaints: {raw_complaints_json_str}")
        except Exception as e:
            logger.error(f"Error extracting session complaints: {e}")

        # 3. Session Concerns (JSON list)
        try:
            concerns_prompt = (
                "From the therapy transcript provided, identify and list specific worries, anxieties, or significant concerns "
                "expressed by the client or noted by the therapist. These may be less formal than 'chief complaints' but represent active areas of distress or preoccupation for the client. "
                "Format the output as a JSON object with a single key \"concerns\" containing a list of strings. "
                "Each string should be a concise summary of a distinct concern. "
                "If none are clearly identified, return an empty list under the \"concerns\" key.\n\n"
                f"Transcript:\n{transcript_text}\n\nJSON Output:"
            )
            raw_concerns_json_str = self._call_openai_llm(concerns_prompt, response_format="json_object", model=Config.OPENAI_JSON_EXTRACTION_MODEL or "gpt-3.5-turbo-0125")
            if raw_concerns_json_str:
                try:
                    concerns_data = json.loads(raw_concerns_json_str)
                    if isinstance(concerns_data.get("concerns"), list):
                        results["session_concerns"] = [str(item) for item in concerns_data["concerns"]]
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON for session_concerns: {raw_concerns_json_str}")
        except Exception as e:
            logger.error(f"Error extracting session concerns: {e}")

        # 4. Session Action Items (JSON list)
        try:
            action_items_prompt = (
                "Review the following therapy session transcript and identify any clear action items, homework assignments, "
                "or tasks agreed upon by the client and therapist to be undertaken before the next session or as ongoing practices. "
                "Format the output as a JSON object with a single key \"action_items\" containing a list of strings. "
                "Each string should describe a distinct action item. "
                "If no action items are identified, return an empty list under the \"action_items\" key.\n\n"
                f"Transcript:\n{transcript_text}\n\nJSON Output:"
            )
            raw_action_items_json_str = self._call_openai_llm(action_items_prompt, response_format="json_object", model=Config.OPENAI_JSON_EXTRACTION_MODEL or "gpt-3.5-turbo-0125")
            if raw_action_items_json_str:
                try:
                    action_items_data = json.loads(raw_action_items_json_str)
                    if isinstance(action_items_data.get("action_items"), list):
                        results["session_action_items"] = [str(item) for item in action_items_data["action_items"]]
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON for session_action_items: {raw_action_items_json_str}")
        except Exception as e:
            logger.error(f"Error extracting session action items: {e}")

        # 5. Session Presentation Summary (Text)
        try:
            presentation_prompt = (
                "Based on the therapy transcript, provide a brief (2-4 sentences) summary of the client's overall presentation during this session. "
                "Comment on their mood, affect, engagement, and any notable behavioral observations. This should be a concise textual summary.\n\n"
                f"Transcript:\n{transcript_text}\n\nSummary:"
            )
            summary_text = self._call_openai_llm(presentation_prompt, response_format="text", model=Config.OPENAI_SUMMARY_MODEL or Config.OPENAI_MODEL)
            if summary_text:
                results["session_presentation_summary"] = summary_text
        except Exception as e:
            logger.error(f"Error extracting session presentation summary: {e}")

        # 6. Key Themes (JSON list) - Simplified extraction
        try:
            themes_prompt = (
                "Identify the top 3-5 key themes discussed in the following therapy transcript. "
                "Themes should be concise phrases or keywords. "
                "Format the output as a JSON object with a single key \"key_themes\" containing a list of strings. "
                "If no distinct themes are clear, return an empty list under the \"key_themes\" key.\n\n"
                f"Transcript:\n{transcript_text}\n\nJSON Output:"
            )
            raw_themes_json_str = self._call_openai_llm(themes_prompt, response_format="json_object", model=Config.OPENAI_JSON_EXTRACTION_MODEL or "gpt-3.5-turbo-0125")
            if raw_themes_json_str:
                try:
                    themes_data = json.loads(raw_themes_json_str)
                    if isinstance(themes_data.get("key_themes"), list):
                        results["key_themes"] = [str(item) for item in themes_data["key_themes"]]
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON for key_themes: {raw_themes_json_str}")
        except Exception as e:
            logger.error(f"Error extracting key themes: {e}")

        # 7. Sentiment Score (Float) - This is tricky, LLMs are not great at single scores.
        # A more robust approach might involve a dedicated sentiment model or a more complex prompt.
        # For now, a simple attempt.
        try:
            sentiment_prompt = (
                "Analyze the overall sentiment of the client expressed during this therapy session. "
                "Provide a numerical score between -1.0 (very negative) and 1.0 (very positive), with 0.0 being neutral. "
                "Format the output as a JSON object with a single key \"sentiment_score\" containing this numerical value. "
                "Base your score on the predominant emotional tone of the client's expressions.\n\n"
                f"Transcript:\n{transcript_text}\n\nJSON Output:"
            )
            raw_sentiment_json_str = self._call_openai_llm(sentiment_prompt, response_format="json_object", model=Config.OPENAI_JSON_EXTRACTION_MODEL or "gpt-3.5-turbo-0125")
            if raw_sentiment_json_str:
                try:
                    sentiment_data = json.loads(raw_sentiment_json_str)
                    if isinstance(sentiment_data.get("sentiment_score"), (float, int)):
                        results["sentiment_score"] = float(sentiment_data["sentiment_score"])
                    elif isinstance(sentiment_data.get("sentiment_score"), str): # Attempt to parse if string
                        results["sentiment_score"] = float(sentiment_data["sentiment_score"])
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Could not parse sentiment score: {raw_sentiment_json_str} - Error: {e}")
        except Exception as e:
            logger.error(f"Error extracting sentiment score: {e}")
            
        # Add provider and model info, assuming OpenAI is used for all these detailed extractions
        results['provider_detailed_analysis'] = 'openai'
        results['model_detailed_analysis'] = Config.OPENAI_MODEL # Or more specific if models vary by extraction type

        return results

    def _format_session_for_conceptualization_prompt(self, session_data: Dict) -> str:
        """Helper to create a concise summary of a session for the conceptualization prompt."""
        parts = []
        if session_data.get('session_date'):
            try:
                # Attempt to parse if it's a datetime object or ISO string
                if isinstance(session_data['session_date'], datetime):
                    date_str = session_data['session_date'].strftime('%Y-%m-%d')
                else: # Assuming string
                    date_str = datetime.fromisoformat(str(session_data['session_date']).replace('Z', '+00:00')).strftime('%Y-%m-%d')
                parts.append(f"- Session Date: {date_str}")
            except ValueError:
                parts.append(f"- Session Date: {session_data['session_date']} (raw)")

        if session_data.get('session_complaints'):
            parts.append(f"- Complaints Mentioned: {', '.join(session_data['session_complaints'])}")
        if session_data.get('session_concerns'):
            parts.append(f"- Concerns Expressed: {', '.join(session_data['session_concerns'])}")
        if session_data.get('key_themes'): # This might come from direct transcript analysis
            parts.append(f"- Key Themes: {', '.join(session_data['key_themes'])}")
        
        # Use session_presentation_summary if available (new field)
        if session_data.get('session_presentation_summary'):
            parts.append(f"- Client Presentation: {session_data['session_presentation_summary']}")
        
        # Simplified therapy insights summary for the prompt
        # 'therapy_insights' could be a simple string or a dict from consolidated_insights
        insights_data = session_data.get('therapy_insights') 
        insights_text = None

        if isinstance(insights_data, dict):
            # Prioritize narrative summary if insights_data is a dict (e.g. from consolidated insights)
            insights_text = insights_data.get('narrative_summary', json.dumps(insights_data))
        elif isinstance(insights_data, str):
            insights_text = insights_data
        
        if insights_text:
            if len(insights_text) > 250: # Max length for this part of prompt
                # This would ideally be another LLM call for a good summary.
                # For now, simple truncation for the prompt.
                insights_text = insights_text[:247] + "..."
            parts.append(f"- Key Insights/Events: {insights_text}")
            
        if session_data.get('session_action_items'):
            parts.append(f"- Action Items: {', '.join(session_data['session_action_items'])}")
        
        return "\n".join(parts)

    def update_case_conceptualization(
        self, 
        existing_conceptualization: Optional[str], 
        processed_sessions_data: List[Dict]  # Expects data from enhanced analyze_transcript
    ) -> Optional[str]:
        """
        Generates or updates a longitudinal case conceptualization for a client.
        Returns the conceptualization as a Markdown string, or None on failure.
        """
        if not self.openai_client: # Or preferred powerful LLM client
            logger.error("OpenAI client (or designated LLM for conceptualization) not available in AIService.")
            return None

        if not processed_sessions_data:
            logger.warning("No new session data provided for conceptualization update.")
            # If there's an existing conceptualization, return it. Otherwise, nothing to do.
            return existing_conceptualization

        formatted_new_sessions_input = "\n\n".join(
            [self._format_session_for_conceptualization_prompt(s_data) for s_data in processed_sessions_data]
        )

        prompt_sections = [
            "You are an expert clinical psychologist AI assistant. Your task is to write or update a longitudinal case conceptualization for a therapy client in Markdown format.",
            "Focus on synthesizing information, identifying trends, continuities, and significant changes. Maintain a professional, objective, and empathetic clinical tone. Be concise yet comprehensive."
        ]

        if existing_conceptualization:
            prompt_sections.append(
                "Below is the PREVIOUS Case Conceptualization. Review it and integrate the new session information to update it thoughtfully, ensuring continuity and highlighting changes in the 'Updates Since Last Review' section:"
            )
            prompt_sections.append("--- PREVIOUS CONCEPTUALIZATION START ---")
            prompt_sections.append(existing_conceptualization)
            prompt_sections.append("--- PREVIOUS CONCEPTUALIZATION END ---")
            prompt_sections.append("\nNew Session(s) Information to Integrate:")
        else:
            prompt_sections.append("This is the INITIAL Case Conceptualization. Generate it based on the following session information:")
        
        prompt_sections.append("--- NEW SESSION(S) INFORMATION START ---")
        prompt_sections.append(formatted_new_sessions_input)
        prompt_sections.append("--- NEW SESSION(S) INFORMATION END ---")

        prompt_sections.append("\nINSTRUCTIONS FOR RESPONSE:")
        prompt_sections.append("Output the ENTIRE updated case conceptualization in Markdown format. Ensure all relevant sections are present and updated. The sections should be:")
        prompt_sections.append("- ## Client Overview and Presenting Problem(s)")
        prompt_sections.append("  - (Brief summary of client, initial chief complaints, and how they presented initially. Update if new understanding emerges.)")
        prompt_sections.append("- ## History of Key Concerns & Symptom Development")
        prompt_sections.append("  - (Chronological or thematic summary of how key concerns have evolved. Integrate new session details.)")
        prompt_sections.append("- ## Strengths and Resources")
        prompt_sections.append("  - (Client's identified strengths, coping mechanisms, support systems. Update with new observations.)")
        prompt_sections.append("- ## Key Themes & Patterns Over Time")
        prompt_sections.append("  - (Dominant and recurring themes, how they shifted or remained consistent. Integrate new themes.)")
        prompt_sections.append("- ## Therapeutic Relationship Dynamics")
        prompt_sections.append("  - (Observations on engagement, rapport, etc. based on session presentation summaries. Update with new session observations.)")
        prompt_sections.append("- ## Progress Towards Goals & Action Item Review")
        prompt_sections.append("  - (Status of therapeutic goals and review of actionable items from current and past sessions.)")
        prompt_sections.append("- ## Overall Assessment & Current Conceptualization")
        prompt_sections.append("  - (Synthesized understanding of the client's current state, integrating all above. This section should reflect the latest understanding.)")
        prompt_sections.append("- ## Updates Since Last Review / Focus for Next Sessions")
        prompt_sections.append("  - (Specifically summarize what's new or changed based on the recent session(s) and suggest focus areas for upcoming sessions.)")
        
        final_prompt = "\n\n".join(prompt_sections)

        try:
            # Using OpenAI client as an example, assuming it's the most powerful for this task
            if hasattr(self.openai_client, 'chat') and hasattr(self.openai_client.chat, 'completions'): 
                 response = self.openai_client.chat.completions.create(
                     model=Config.OPENAI_CONCEPTUALIZATION_MODEL or "gpt-4o", # Use specific model from config or default
                     messages=[{"role": "system", "content": "You are an expert clinical psychologist AI assistant specializing in case conceptualization."},
                               {"role": "user", "content": final_prompt}],
                     temperature=0.5, 
                     max_tokens=3500  # Increased token limit for detailed conceptualizations
                 )
                 updated_conceptualization = response.choices[0].message.content.strip()
            else: 
                 logger.error("OpenAI client is not configured or is an older version. Cannot generate case conceptualization.")
                 # Fallback or placeholder for other LLM clients or older OpenAI client
                 # For testing, you can return a modified version of the input:
                 # updated_conceptualization = f"Updated Conceptualization based on: {formatted_new_sessions_input}\n\n{existing_conceptualization or 'No prior text.'}"
                 # This is NOT a real AI call.
                 # raise NotImplementedError("LLM call needs to be implemented for the specific client in AIService.")
                 return None # Explicitly return None if the client isn't usable


            logger.info(f"Case conceptualization updated successfully based on {len(processed_sessions_data)} new session(s).")
            return updated_conceptualization
        except Exception as e:
            logger.exception(f"Error calling LLM for case conceptualization: {e}")
            return None

    # --- Encapsulation/Availability Methods ---
    def is_openai_available(self) -> bool:
        """Check if OpenAI client is initialized and available."""
        return self.openai_client is not None

    def is_anthropic_available(self) -> bool:
        """Check if Anthropic client is initialized and available."""
        return self.anthropic_client is not None

    def is_gemini_available(self) -> bool:
        """Check if Gemini client is initialized and available."""
        return self.gemini_client is not None
