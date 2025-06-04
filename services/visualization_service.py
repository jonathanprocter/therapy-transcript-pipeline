"""
Dynamic longitudinal visualization service for therapy progress tracking
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import io
import base64

logger = logging.getLogger(__name__)

class VisualizationService:
    """Service for generating dynamic therapy progress visualizations"""
    
    def __init__(self):
        # Set up matplotlib for web output
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Therapeutic color schemes
        self.color_schemes = {
            'progress': ['#50C878', '#4A90E2', '#7B68EE', '#F5A623'],
            'emotions': ['#E85D75', '#F5A623', '#50C878', '#4A90E2', '#7B68EE'],
            'intensity': ['#98FB98', '#FFD700', '#F5A623', '#E85D75']
        }
    
    def generate_longitudinal_dashboard(self, client_data: Dict, sessions: List[Dict]) -> Dict:
        """Generate comprehensive longitudinal visualization dashboard"""
        
        dashboard_data = {
            'emotional_timeline': self._create_emotional_timeline(sessions),
            'progress_indicators': self._create_progress_visualization(sessions),
            'session_intensity_map': self._create_intensity_heatmap(sessions),
            'therapeutic_insights': self._create_insights_visualization(sessions),
            'client_summary': self._generate_client_summary(client_data, sessions),
            'generated_at': datetime.now().isoformat()
        }
        
        return dashboard_data
    
    def _create_emotional_timeline(self, sessions: List[Dict]) -> Dict:
        """Create emotional progression timeline visualization"""
        
        if not sessions:
            return {'chart_data': None, 'insights': []}
        
        # Sort sessions by date
        sorted_sessions = sorted(sessions, key=lambda x: x.get('session_date', ''))
        
        dates = []
        emotions = []
        intensities = []
        colors = []
        
        for session in sorted_sessions:
            emotional_data = session.get('emotional_analysis', {})
            
            if emotional_data:
                dates.append(session.get('session_date'))
                primary_emotion = emotional_data.get('primary_emotion', 'neutral')
                emotions.append(primary_emotion)
                intensities.append(emotional_data.get('intensity', 0.5))
                
                color_palette = emotional_data.get('color_palette', {})
                colors.append(color_palette.get('primary', '#8E9AAF'))
        
        # Generate chart data
        chart_data = {
            'labels': dates,
            'emotions': emotions,
            'intensities': intensities,
            'colors': colors,
            'chart_type': 'emotional_timeline'
        }
        
        # Generate insights
        insights = self._analyze_emotional_trends(emotions, intensities)
        
        return {
            'chart_data': chart_data,
            'insights': insights,
            'total_sessions': len(sessions)
        }
    
    def _create_progress_visualization(self, sessions: List[Dict]) -> Dict:
        """Create therapy progress indicators visualization"""
        
        if not sessions:
            return {'chart_data': None, 'metrics': {}}
        
        progress_metrics = {
            'emotional_regulation': [],
            'insight_development': [],
            'behavioral_changes': [],
            'engagement_levels': []
        }
        
        dates = []
        
        for session in sorted(sessions, key=lambda x: x.get('session_date', '')):
            dates.append(session.get('session_date'))
            
            # Extract progress indicators from AI analysis
            progress_data = session.get('progress_indicators', {})
            
            for metric in progress_metrics:
                # Look for metric in various AI provider analyses
                metric_value = 0.5  # Default neutral value
                
                for provider in ['openai_analysis', 'anthropic_analysis', 'gemini_analysis']:
                    provider_data = progress_data.get(provider, {})
                    if metric in provider_data:
                        # Convert text assessments to numeric values
                        assessment = provider_data[metric].lower() if isinstance(provider_data[metric], str) else ''
                        
                        if 'excellent' in assessment or 'significant' in assessment:
                            metric_value = 0.9
                        elif 'good' in assessment or 'improving' in assessment:
                            metric_value = 0.7
                        elif 'moderate' in assessment or 'stable' in assessment:
                            metric_value = 0.5
                        elif 'poor' in assessment or 'declining' in assessment:
                            metric_value = 0.3
                        
                        break
                
                progress_metrics[metric].append(metric_value)
        
        # Calculate overall progress trends
        overall_metrics = {}
        for metric, values in progress_metrics.items():
            if values:
                overall_metrics[metric] = {
                    'current': values[-1],
                    'average': sum(values) / len(values),
                    'trend': 'improving' if len(values) > 1 and values[-1] > values[0] else 'stable'
                }
        
        chart_data = {
            'labels': dates,
            'metrics': progress_metrics,
            'chart_type': 'progress_radar'
        }
        
        return {
            'chart_data': chart_data,
            'metrics': overall_metrics,
            'sessions_analyzed': len(sessions)
        }
    
    def _create_intensity_heatmap(self, sessions: List[Dict]) -> Dict:
        """Create session intensity heatmap visualization"""
        
        if not sessions:
            return {'chart_data': None, 'patterns': []}
        
        # Create weekly intensity mapping
        intensity_map = {}
        session_count_map = {}
        
        for session in sessions:
            session_date = session.get('session_date')
            if not session_date:
                continue
            
            try:
                date_obj = datetime.fromisoformat(session_date) if isinstance(session_date, str) else session_date
                week_key = date_obj.strftime('%Y-W%W')
                
                emotional_data = session.get('emotional_analysis', {})
                intensity = emotional_data.get('intensity', 0.5)
                
                if week_key not in intensity_map:
                    intensity_map[week_key] = 0
                    session_count_map[week_key] = 0
                
                intensity_map[week_key] += intensity
                session_count_map[week_key] += 1
                
            except (ValueError, AttributeError):
                continue
        
        # Calculate average intensity per week
        weekly_averages = {}
        for week, total_intensity in intensity_map.items():
            count = session_count_map[week]
            weekly_averages[week] = total_intensity / count if count > 0 else 0
        
        # Identify patterns
        patterns = self._identify_intensity_patterns(weekly_averages)
        
        chart_data = {
            'weekly_data': weekly_averages,
            'chart_type': 'intensity_heatmap'
        }
        
        return {
            'chart_data': chart_data,
            'patterns': patterns,
            'weeks_analyzed': len(weekly_averages)
        }
    
    def _create_insights_visualization(self, sessions: List[Dict]) -> Dict:
        """Create therapeutic insights and themes visualization"""
        
        if not sessions:
            return {'themes': [], 'insights': []}
        
        # Aggregate themes across sessions
        theme_frequency = {}
        key_insights = []
        
        for session in sessions:
            # Extract themes from therapy insights
            therapy_insights = session.get('therapy_insights', {})
            
            if isinstance(therapy_insights, dict):
                themes = therapy_insights.get('key_themes', [])
                if isinstance(themes, list):
                    for theme in themes:
                        theme_frequency[theme] = theme_frequency.get(theme, 0) + 1
                
                # Extract consolidated insights
                consolidated = therapy_insights.get('consolidated_insights', {})
                if consolidated:
                    key_topics = consolidated.get('key_topics', [])
                    if key_topics:
                        key_insights.extend(key_topics)
        
        # Sort themes by frequency
        sorted_themes = sorted(theme_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'themes': sorted_themes,
            'insights': list(set(key_insights))[:15],  # Remove duplicates and limit
            'total_themes': len(theme_frequency)
        }
    
    def _generate_client_summary(self, client_data: Dict, sessions: List[Dict]) -> Dict:
        """Generate comprehensive client summary for visualization"""
        
        if not sessions:
            return {'summary': 'No session data available', 'metrics': {}}
        
        total_sessions = len(sessions)
        latest_session = max(sessions, key=lambda x: x.get('session_date', ''))
        
        # Calculate time span
        dates = [s.get('session_date') for s in sessions if s.get('session_date')]
        if dates:
            first_session = min(dates)
            last_session = max(dates)
            
            try:
                first_date = datetime.fromisoformat(first_session) if isinstance(first_session, str) else first_session
                last_date = datetime.fromisoformat(last_session) if isinstance(last_session, str) else last_session
                treatment_duration = (last_date - first_date).days
            except (ValueError, AttributeError):
                treatment_duration = 0
        else:
            treatment_duration = 0
        
        # Extract latest emotional state
        latest_emotional = latest_session.get('emotional_analysis', {})
        current_emotion = latest_emotional.get('primary_emotion', 'unknown')
        current_intensity = latest_emotional.get('intensity', 0.5)
        
        summary = {
            'client_name': client_data.get('name', 'Client'),
            'total_sessions': total_sessions,
            'treatment_duration_days': treatment_duration,
            'current_emotional_state': current_emotion,
            'current_intensity': current_intensity,
            'latest_session_date': latest_session.get('session_date'),
            'summary_generated': datetime.now().isoformat()
        }
        
        return summary
    
    def _analyze_emotional_trends(self, emotions: List[str], intensities: List[float]) -> List[str]:
        """Analyze emotional trends and generate insights"""
        
        insights = []
        
        if not emotions or not intensities:
            return insights
        
        # Analyze emotional stability
        unique_emotions = len(set(emotions))
        if unique_emotions <= 2:
            insights.append("Shows emotional consistency across sessions")
        elif unique_emotions >= 5:
            insights.append("Experiencing varied emotional states - may indicate processing")
        
        # Analyze intensity trends
        if len(intensities) >= 3:
            recent_avg = sum(intensities[-3:]) / 3
            early_avg = sum(intensities[:3]) / 3
            
            if recent_avg < early_avg - 0.2:
                insights.append("Emotional intensity decreasing - positive therapeutic progress")
            elif recent_avg > early_avg + 0.2:
                insights.append("Emotional intensity increasing - may need attention")
        
        # Analyze most frequent emotions
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        most_common = max(emotion_counts.items(), key=lambda x: x[1])
        if most_common[1] >= len(emotions) * 0.4:
            insights.append(f"Predominantly experiencing {most_common[0]} - consistent emotional pattern")
        
        return insights
    
    def _identify_intensity_patterns(self, weekly_data: Dict) -> List[str]:
        """Identify patterns in emotional intensity over time"""
        
        patterns = []
        
        if len(weekly_data) < 3:
            return patterns
        
        intensities = list(weekly_data.values())
        
        # Look for cyclical patterns
        high_weeks = sum(1 for i in intensities if i > 0.7)
        low_weeks = sum(1 for i in intensities if i < 0.3)
        
        if high_weeks > len(intensities) * 0.3:
            patterns.append("Periods of high emotional intensity identified")
        
        if low_weeks > len(intensities) * 0.3:
            patterns.append("Consistent periods of emotional stability")
        
        # Look for improvement trends
        recent_weeks = intensities[-4:] if len(intensities) >= 4 else intensities
        early_weeks = intensities[:4] if len(intensities) >= 4 else intensities
        
        if recent_weeks and early_weeks:
            recent_avg = sum(recent_weeks) / len(recent_weeks)
            early_avg = sum(early_weeks) / len(early_weeks)
            
            if recent_avg < early_avg - 0.15:
                patterns.append("Overall intensity decreasing over time")
            elif recent_avg > early_avg + 0.15:
                patterns.append("Intensity levels increasing - needs monitoring")
        
        return patterns
    
    def generate_chart_image(self, chart_data: Dict, chart_type: str) -> str:
        """Generate base64 encoded chart image for web display"""
        
        try:
            plt.figure(figsize=(12, 8))
            
            if chart_type == 'emotional_timeline':
                self._plot_emotional_timeline(chart_data)
            elif chart_type == 'progress_radar':
                self._plot_progress_radar(chart_data)
            elif chart_type == 'intensity_heatmap':
                self._plot_intensity_heatmap(chart_data)
            
            # Save to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            plt.close()
            return ""
    
    def _plot_emotional_timeline(self, data: Dict):
        """Plot emotional timeline chart"""
        
        labels = data.get('labels', [])
        emotions = data.get('emotions', [])
        intensities = data.get('intensities', [])
        colors = data.get('colors', [])
        
        if not labels:
            return
        
        # Convert dates for plotting
        x_dates = [datetime.fromisoformat(date) if isinstance(date, str) else date for date in labels]
        
        # Create the plot
        plt.scatter(x_dates, intensities, c=colors, s=100, alpha=0.7, edgecolors='black')
        
        # Add trend line
        if len(intensities) > 1:
            x_numeric = mdates.date2num(x_dates)
            z = np.polyfit(x_numeric, intensities, 1)
            p = np.poly1d(z)
            plt.plot(x_dates, p(x_numeric), "r--", alpha=0.8, linewidth=2)
        
        plt.title('Emotional Intensity Timeline', fontsize=16, fontweight='bold')
        plt.xlabel('Session Date', fontsize=12)
        plt.ylabel('Emotional Intensity', fontsize=12)
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator())
        plt.xticks(rotation=45)
    
    def _plot_progress_radar(self, data: Dict):
        """Plot progress metrics radar chart"""
        
        metrics = data.get('metrics', {})
        
        if not metrics:
            return
        
        categories = list(metrics.keys())
        values = [metrics[cat][-1] if metrics[cat] else 0.5 for cat in categories]
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
        values += values[:1]  # Complete the circle
        angles = np.concatenate((angles, [angles[0]]))
        
        ax = plt.subplot(111, projection='polar')
        ax.plot(angles, values, 'o-', linewidth=2, color='#4A90E2')
        ax.fill(angles, values, alpha=0.25, color='#4A90E2')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories])
        ax.set_ylim(0, 1)
        
        plt.title('Therapy Progress Indicators', fontsize=16, fontweight='bold', pad=20)
    
    def _plot_intensity_heatmap(self, data: Dict):
        """Plot intensity heatmap"""
        
        weekly_data = data.get('weekly_data', {})
        
        if not weekly_data:
            return
        
        weeks = list(weekly_data.keys())
        intensities = list(weekly_data.values())
        
        # Create color map
        colors = ['#98FB98' if i < 0.3 else '#FFD700' if i < 0.6 else '#F5A623' if i < 0.8 else '#E85D75' 
                 for i in intensities]
        
        plt.bar(range(len(weeks)), intensities, color=colors, alpha=0.8)
        plt.title('Weekly Emotional Intensity Patterns', fontsize=16, fontweight='bold')
        plt.xlabel('Week', fontsize=12)
        plt.ylabel('Average Intensity', fontsize=12)
        plt.xticks(range(len(weeks)), [w.split('-W')[1] for w in weeks], rotation=45)
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)