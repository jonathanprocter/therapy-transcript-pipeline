import os
import json
import logging
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
            
            # Initialize without organization header to avoid mismatch
            client = openai.OpenAI(
                api_key=api_key,
                organization=None  # Remove organization header
            )
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
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI client is initialized and available."""
        return self.openai_client is not None
    
    def is_anthropic_available(self) -> bool:
        """Check if Anthropic client is initialized and available."""
        return self.anthropic_client is not None
    
    def is_gemini_available(self) -> bool:
        """Check if Gemini client is initialized and available."""
        return self.gemini_client is not None
