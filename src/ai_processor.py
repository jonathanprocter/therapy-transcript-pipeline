import os
import logging
import json
import requests
from datetime import datetime

class AIProcessor:
    """
    Processes transcript text using AI services (OpenAI, Claude, Gemini)
    with intelligent fallback between services.
    """
    
    def __init__(self, openai_key=None, claude_key=None, gemini_key=None):
        """
        Initialize the AI processor with API keys.
        
        Args:
            openai_key: OpenAI API key
            claude_key: Claude API key
            gemini_key: Gemini API key
        """
        self.openai_key = openai_key
        self.claude_key = claude_key
        self.gemini_key = gemini_key
        self.logger = logging.getLogger(__name__)
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the prompt template from file or use default."""
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'prompt_template.txt')
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    return f.read()
        except Exception as e:
            self.logger.warning(f"Could not load prompt template: {str(e)}")
        
        # Default template if file not found
        return """You are a highly skilled and experienced therapist specializing in creating comprehensive and insightful clinical progress notes. Your task is to analyze a provided counseling session transcript and generate a detailed progress note, suitable for an Electronic Medical Record (EMR), that mirrors the depth, detail, and clinical sophistication of an expert human therapist.

Please analyze the following transcript and create a comprehensive clinical progress note using the SOAP format (Subjective, Objective, Assessment, Plan), along with supplemental analyses (Tonal, Thematic, Sentiment), key points, significant quotes, and a narrative summary.

TRANSCRIPT:
{transcript}

Please provide a detailed and clinically sophisticated analysis of this session."""
    
    def process_transcript(self, transcript_text):
        """
        Process a transcript using available AI services with fallback.
        
        Args:
            transcript_text: Text content of the transcript
            
        Returns:
            str: Processed content or error message
        """
        # Prepare prompt with transcript
        prompt = self.prompt_template.replace('{transcript}', transcript_text)
        
        # Try OpenAI first if available
        if self.openai_key:
            try:
                result = self._process_with_openai(prompt)
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"OpenAI processing failed: {str(e)}")
        
        # Try Claude as fallback
        if self.claude_key:
            try:
                result = self._process_with_claude(prompt)
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"Claude processing failed: {str(e)}")
        
        # Try Gemini as final fallback
        if self.gemini_key:
            try:
                result = self._process_with_gemini(prompt)
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"Gemini processing failed: {str(e)}")
        
        # If all services fail
        error_msg = "All AI services failed to process the transcript."
        self.logger.error(error_msg)
        return f"ERROR: {error_msg} Please check API keys and try again."
    
    def _process_with_openai(self, prompt):
        """
        Process transcript with OpenAI API.
        
        Args:
            prompt: Prompt to send to OpenAI
            
        Returns:
            str: Processed content or None if processing fails
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}"
        }
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a professional therapist creating detailed clinical notes."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def _process_with_claude(self, prompt):
        """
        Process transcript with Claude API.
        
        Args:
            prompt: Prompt to send to Claude
            
        Returns:
            str: Processed content or None if processing fails
        """
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_key,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
        except Exception as e:
            self.logger.error(f"Claude API error: {str(e)}")
            return None
    
    def _process_with_gemini(self, prompt):
        """
        Process transcript with Gemini API.
        
        Args:
            prompt: Prompt to send to Gemini
            
        Returns:
            str: Processed content or None if processing fails
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4000
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            return None
