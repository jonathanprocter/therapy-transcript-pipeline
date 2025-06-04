"""
Emotional analysis service for adaptive color therapy and longitudinal visualization
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import re

logger = logging.getLogger(__name__)

class EmotionalAnalysis:
    """Service for analyzing emotional content and generating adaptive visualizations"""
    
    def __init__(self):
        # Emotional color mapping based on therapeutic color theory
        self.emotion_colors = {
            'calm': '#4A90E2',       # Soft blue - promotes calm and trust
            'anxious': '#F5A623',    # Warm orange - energizing but not overwhelming
            'depressed': '#7B68EE',  # Medium slate blue - gentle and supportive
            'angry': '#E85D75',      # Soft red - acknowledges intensity without aggression
            'hopeful': '#50C878',    # Emerald green - growth and renewal
            'fearful': '#DDA0DD',    # Plum - gentle and protective
            'joyful': '#FFD700',     # Gold - warm and uplifting
            'sad': '#6495ED',        # Cornflower blue - soothing and supportive
            'neutral': '#8E9AAF',    # Gray-blue - balanced and stable
            'confused': '#D8BFD8',   # Thistle - soft and non-threatening
            'overwhelmed': '#F0E68C', # Khaki - grounding and earthy
            'content': '#98FB98'     # Pale green - peaceful and restorative
        }
        
        # Emotional intensity levels
        self.intensity_levels = {
            'low': 0.3,
            'moderate': 0.6,
            'high': 0.9
        }
        
        # Emotional keywords for analysis
        self.emotion_keywords = {
            'anxious': ['anxious', 'worried', 'nervous', 'panic', 'stress', 'tension', 'restless', 'uneasy'],
            'depressed': ['sad', 'hopeless', 'empty', 'worthless', 'despair', 'down', 'low', 'heavy'],
            'angry': ['angry', 'furious', 'rage', 'irritated', 'frustrated', 'mad', 'resentful', 'hostile'],
            'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'composed', 'balanced'],
            'hopeful': ['hopeful', 'optimistic', 'positive', 'encouraged', 'confident', 'better', 'improving'],
            'fearful': ['afraid', 'scared', 'terrified', 'frightened', 'fear', 'phobia', 'dread'],
            'joyful': ['happy', 'joyful', 'excited', 'elated', 'cheerful', 'delighted', 'thrilled'],
            'overwhelmed': ['overwhelmed', 'too much', 'can\'t cope', 'drowning', 'buried', 'swamped'],
            'confused': ['confused', 'lost', 'uncertain', 'unclear', 'mixed up', 'puzzled'],
            'content': ['content', 'satisfied', 'fulfilled', 'at peace', 'comfortable', 'stable']
        }
    
    def analyze_session_emotions(self, transcript_content: str, ai_analysis: Dict) -> Dict:
        """Analyze emotional content of a therapy session"""
        
        # Extract emotions from transcript content
        detected_emotions = self._extract_emotions_from_text(transcript_content)
        
        # Extract emotions from AI analysis if available
        ai_emotions = self._extract_emotions_from_ai_analysis(ai_analysis)
        
        # Combine and weight the emotional analysis
        combined_emotions = self._combine_emotional_data(detected_emotions, ai_emotions)
        
        # Determine primary and secondary emotions
        primary_emotion, secondary_emotion = self._determine_primary_emotions(combined_emotions)
        
        # Calculate emotional intensity
        intensity = self._calculate_emotional_intensity(transcript_content, combined_emotions)
        
        # Generate adaptive color palette
        color_palette = self._generate_adaptive_colors(primary_emotion, secondary_emotion, intensity)
        
        return {
            'primary_emotion': primary_emotion,
            'secondary_emotion': secondary_emotion,
            'intensity': intensity,
            'detected_emotions': combined_emotions,
            'color_palette': color_palette,
            'emotional_keywords_found': self._get_keywords_found(transcript_content),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _extract_emotions_from_text(self, text: str) -> Dict[str, float]:
        """Extract emotions directly from transcript text"""
        emotions = {}
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences with context weighting
                occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                
                # Weight based on context (client speech vs therapist speech)
                if 'client:' in text_lower or 'patient:' in text_lower:
                    # Give more weight to client expressions
                    client_context = re.findall(r'client:[^:]*?' + re.escape(keyword), text_lower)
                    score += len(client_context) * 2
                
                score += occurrences
            
            if score > 0:
                # Normalize score based on text length
                emotions[emotion] = min(score / (len(text.split()) / 100), 1.0)
        
        return emotions
    
    def _extract_emotions_from_ai_analysis(self, ai_analysis: Dict) -> Dict[str, float]:
        """Extract emotional data from AI analysis results"""
        emotions = {}
        
        if not ai_analysis:
            return emotions
        
        # Extract from different AI providers
        for provider in ['openai_analysis', 'anthropic_analysis', 'gemini_analysis']:
            provider_data = ai_analysis.get(provider, {})
            
            if isinstance(provider_data, dict):
                # Look for sentiment analysis
                sentiment = provider_data.get('sentiment_analysis', {})
                if sentiment:
                    emotion_tone = sentiment.get('emotional_tone', '').lower()
                    if emotion_tone in self.emotion_keywords:
                        emotions[emotion_tone] = emotions.get(emotion_tone, 0) + 0.7
                
                # Look for mood assessment
                mood = provider_data.get('client_mood')
                if mood and isinstance(mood, (int, float)):
                    # Convert mood scale to emotions
                    if mood <= 3:
                        emotions['depressed'] = emotions.get('depressed', 0) + 0.8
                    elif mood <= 5:
                        emotions['neutral'] = emotions.get('neutral', 0) + 0.6
                    elif mood <= 7:
                        emotions['content'] = emotions.get('content', 0) + 0.7
                    else:
                        emotions['hopeful'] = emotions.get('hopeful', 0) + 0.8
        
        return emotions
    
    def _combine_emotional_data(self, text_emotions: Dict, ai_emotions: Dict) -> Dict[str, float]:
        """Combine emotional data from multiple sources"""
        combined = {}
        
        # Merge both dictionaries with weighted averaging
        all_emotions = set(text_emotions.keys()) | set(ai_emotions.keys())
        
        for emotion in all_emotions:
            text_score = text_emotions.get(emotion, 0) * 0.6  # Text analysis weight
            ai_score = ai_emotions.get(emotion, 0) * 0.4     # AI analysis weight
            combined[emotion] = text_score + ai_score
        
        return combined
    
    def _determine_primary_emotions(self, emotions: Dict[str, float]) -> Tuple[str, Optional[str]]:
        """Determine primary and secondary emotions"""
        if not emotions:
            return 'neutral', None
        
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_emotions[0][0]
        secondary = sorted_emotions[1][0] if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0.3 else None
        
        return primary, secondary
    
    def _calculate_emotional_intensity(self, text: str, emotions: Dict[str, float]) -> float:
        """Calculate overall emotional intensity"""
        if not emotions:
            return 0.3
        
        # Base intensity from emotion scores
        max_emotion_score = max(emotions.values()) if emotions else 0
        
        # Adjust based on language intensity markers
        intensity_markers = [
            'very', 'extremely', 'really', 'so', 'incredibly', 'absolutely',
            'completely', 'totally', 'entirely', 'utterly', 'deeply'
        ]
        
        text_lower = text.lower()
        intensity_boost = sum(1 for marker in intensity_markers if marker in text_lower) * 0.1
        
        # Calculate final intensity
        intensity = min(max_emotion_score + intensity_boost, 1.0)
        
        return max(intensity, 0.3)  # Minimum intensity for visibility
    
    def _generate_adaptive_colors(self, primary: str, secondary: Optional[str], intensity: float) -> Dict:
        """Generate adaptive color palette for therapy UI"""
        
        primary_color = self.emotion_colors.get(primary, self.emotion_colors['neutral'])
        
        # Adjust color intensity based on emotional intensity
        primary_rgb = self._hex_to_rgb(primary_color)
        primary_adjusted = self._adjust_color_intensity(primary_rgb, intensity)
        
        # Generate complementary colors
        secondary_color = None
        if secondary:
            secondary_color = self.emotion_colors.get(secondary, self.emotion_colors['neutral'])
        
        # Create therapeutic color palette
        palette = {
            'primary': self._rgb_to_hex(primary_adjusted),
            'primary_light': self._rgb_to_hex(self._lighten_color(primary_adjusted, 0.3)),
            'primary_dark': self._rgb_to_hex(self._darken_color(primary_adjusted, 0.2)),
            'secondary': secondary_color,
            'background': self._generate_therapeutic_background(primary_adjusted),
            'text': self._generate_optimal_text_color(primary_adjusted),
            'accent': self._generate_accent_color(primary_adjusted),
            'intensity_level': intensity
        }
        
        return palette
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def _adjust_color_intensity(self, rgb: Tuple[int, int, int], intensity: float) -> Tuple[int, int, int]:
        """Adjust color intensity while maintaining therapeutic properties"""
        r, g, b = rgb
        
        # Gentle intensity adjustment to avoid harsh colors
        factor = 0.7 + (intensity * 0.3)  # Range from 0.7 to 1.0
        
        return (
            int(min(255, r * factor)),
            int(min(255, g * factor)),
            int(min(255, b * factor))
        )
    
    def _lighten_color(self, rgb: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
        """Lighten a color by a given amount"""
        r, g, b = rgb
        return (
            int(min(255, r + (255 - r) * amount)),
            int(min(255, g + (255 - g) * amount)),
            int(min(255, b + (255 - b) * amount))
        )
    
    def _darken_color(self, rgb: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
        """Darken a color by a given amount"""
        r, g, b = rgb
        return (
            int(max(0, r * (1 - amount))),
            int(max(0, g * (1 - amount))),
            int(max(0, b * (1 - amount)))
        )
    
    def _generate_therapeutic_background(self, primary_rgb: Tuple[int, int, int]) -> str:
        """Generate a therapeutic background color"""
        # Create a very light, desaturated version of the primary color
        light_bg = self._lighten_color(primary_rgb, 0.85)
        return self._rgb_to_hex(light_bg)
    
    def _generate_optimal_text_color(self, bg_rgb: Tuple[int, int, int]) -> str:
        """Generate optimal text color for readability"""
        # Calculate luminance
        r, g, b = bg_rgb
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return high contrast color
        return '#2C3E50' if luminance > 0.5 else '#FFFFFF'
    
    def _generate_accent_color(self, primary_rgb: Tuple[int, int, int]) -> str:
        """Generate a complementary accent color"""
        r, g, b = primary_rgb
        
        # Generate complementary color
        complement = (255 - r, 255 - g, 255 - b)
        
        # Adjust to be therapeutically appropriate
        adjusted = self._adjust_color_intensity(complement, 0.7)
        
        return self._rgb_to_hex(adjusted)
    
    def _get_keywords_found(self, text: str) -> Dict[str, List[str]]:
        """Get specific emotional keywords found in text"""
        found = {}
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            emotion_keywords = []
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    emotion_keywords.append(keyword)
            
            if emotion_keywords:
                found[emotion] = emotion_keywords
        
        return found
    
    def generate_longitudinal_emotional_data(self, client_sessions: List[Dict]) -> Dict:
        """Generate longitudinal emotional analysis across sessions"""
        
        if not client_sessions:
            return {}
        
        # Sort sessions by date
        sorted_sessions = sorted(client_sessions, key=lambda x: x.get('session_date', ''))
        
        emotional_timeline = []
        emotion_trends = {}
        intensity_timeline = []
        
        for session in sorted_sessions:
            session_emotions = session.get('emotional_analysis', {})
            
            if session_emotions:
                emotional_timeline.append({
                    'date': session.get('session_date'),
                    'primary_emotion': session_emotions.get('primary_emotion'),
                    'secondary_emotion': session_emotions.get('secondary_emotion'),
                    'intensity': session_emotions.get('intensity', 0.5),
                    'color_palette': session_emotions.get('color_palette', {})
                })
                
                # Track emotion trends
                primary = session_emotions.get('primary_emotion')
                if primary:
                    emotion_trends[primary] = emotion_trends.get(primary, 0) + 1
                
                intensity_timeline.append(session_emotions.get('intensity', 0.5))
        
        # Calculate trends and patterns
        dominant_emotions = sorted(emotion_trends.items(), key=lambda x: x[1], reverse=True)[:3]
        average_intensity = sum(intensity_timeline) / len(intensity_timeline) if intensity_timeline else 0.5
        
        # Detect emotional patterns
        patterns = self._detect_emotional_patterns(emotional_timeline)
        
        return {
            'emotional_timeline': emotional_timeline,
            'dominant_emotions': dominant_emotions,
            'average_intensity': average_intensity,
            'emotional_patterns': patterns,
            'total_sessions': len(sorted_sessions),
            'analysis_generated': datetime.now().isoformat()
        }
    
    def _detect_emotional_patterns(self, timeline: List[Dict]) -> Dict:
        """Detect patterns in emotional progression"""
        patterns = {
            'improvement_trend': False,
            'stability_periods': [],
            'emotional_cycles': [],
            'intensity_trend': 'stable'
        }
        
        if len(timeline) < 3:
            return patterns
        
        # Analyze intensity trend
        recent_intensities = [session.get('intensity', 0.5) for session in timeline[-5:]]
        early_intensities = [session.get('intensity', 0.5) for session in timeline[:5]]
        
        if recent_intensities and early_intensities:
            recent_avg = sum(recent_intensities) / len(recent_intensities)
            early_avg = sum(early_intensities) / len(early_intensities)
            
            if recent_avg < early_avg - 0.1:
                patterns['intensity_trend'] = 'improving'
                patterns['improvement_trend'] = True
            elif recent_avg > early_avg + 0.1:
                patterns['intensity_trend'] = 'concerning'
        
        return patterns