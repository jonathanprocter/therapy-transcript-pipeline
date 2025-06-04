import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import base64
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for generating visual analytics and insights"""
    
    def __init__(self):
        # Set up matplotlib style for healthcare dashboard
        plt.style.use('default')
        self.colors = {
            'primary': '#0066cc',
            'secondary': '#6c757d',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        }
    
    def generate_mood_trend_chart(self, sessions: List[Dict]) -> str:
        """Generate a mood trend chart over time"""
        try:
            if not sessions:
                return self._create_empty_chart("No mood data available")
            
            # Extract mood data
            dates = []
            mood_scores = []
            
            for session in sessions:
                if session.get('session_date') and session.get('sentiment_score'):
                    try:
                        date = session['session_date']
                        if isinstance(date, str):
                            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        dates.append(date)
                        mood_scores.append(float(session['sentiment_score']))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing session data: {e}")
                        continue
            
            if not dates or not mood_scores:
                return self._create_empty_chart("No valid mood data found")
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot mood trend
            ax.plot(dates, mood_scores, marker='o', linewidth=2, markersize=6, 
                   color=self.colors['primary'], label='Mood Score')
            
            # Add trend line
            if len(dates) > 2:
                z = np.polyfit(range(len(dates)), mood_scores, 1)
                p = np.poly1d(z)
                ax.plot(dates, p(range(len(dates))), "--", 
                       color=self.colors['secondary'], alpha=0.7, label='Trend')
            
            # Formatting
            ax.set_xlabel('Session Date')
            ax.set_ylabel('Mood Score (1-10)')
            ax.set_title('Client Mood Trend Over Time', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Set y-axis limits
            ax.set_ylim(0, 10)
            
            plt.tight_layout()
            
            # Convert to base64 string
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating mood trend chart: {str(e)}")
            return self._create_empty_chart("Error generating chart")
    
    def generate_theme_frequency_chart(self, sessions: List[Dict]) -> str:
        """Generate a chart showing frequency of therapy themes"""
        try:
            if not sessions:
                return self._create_empty_chart("No theme data available")
            
            # Count theme frequencies
            theme_counts = defaultdict(int)
            
            for session in sessions:
                themes = session.get('key_themes', [])
                if isinstance(themes, list):
                    for theme in themes:
                        if isinstance(theme, str) and theme.strip():
                            theme_counts[theme.strip().lower()] += 1
                elif isinstance(themes, str):
                    # Handle case where themes might be stored as JSON string
                    try:
                        themes_list = json.loads(themes)
                        for theme in themes_list:
                            if isinstance(theme, str) and theme.strip():
                                theme_counts[theme.strip().lower()] += 1
                    except json.JSONDecodeError:
                        pass
            
            if not theme_counts:
                return self._create_empty_chart("No themes found in sessions")
            
            # Get top 10 themes
            sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            themes, counts = zip(*sorted_themes)
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(12, 8))
            
            bars = ax.barh(range(len(themes)), counts, color=self.colors['info'])
            
            # Formatting
            ax.set_yticks(range(len(themes)))
            ax.set_yticklabels([theme.title() for theme in themes])
            ax.set_xlabel('Frequency')
            ax.set_title('Most Frequent Therapy Themes', fontsize=16, fontweight='bold')
            
            # Add value labels on bars
            for i, (bar, count) in enumerate(zip(bars, counts)):
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                       str(count), va='center', fontweight='bold')
            
            ax.grid(True, axis='x', alpha=0.3)
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating theme frequency chart: {str(e)}")
            return self._create_empty_chart("Error generating chart")
    
    def generate_progress_dashboard(self, sessions: List[Dict], longitudinal_data: Dict = None) -> Dict:
        """Generate a comprehensive progress dashboard"""
        try:
            dashboard_data = {
                'mood_chart': self.generate_mood_trend_chart(sessions),
                'theme_chart': self.generate_theme_frequency_chart(sessions),
                'sentiment_chart': self.generate_sentiment_distribution_chart(sessions),
                'session_summary': self._generate_session_summary(sessions),
                'progress_metrics': self._calculate_progress_metrics(sessions),
                'insights': self._generate_insights(sessions, longitudinal_data)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating progress dashboard: {str(e)}")
            return {}
    
    def generate_sentiment_distribution_chart(self, sessions: List[Dict]) -> str:
        """Generate a pie chart showing sentiment distribution"""
        try:
            if not sessions:
                return self._create_empty_chart("No sentiment data available")
            
            # Count sentiments
            sentiment_counts = defaultdict(int)
            
            for session in sessions:
                insights = session.get('therapy_insights', {})
                if isinstance(insights, dict):
                    sentiment = insights.get('sentiment_analysis', {}).get('overall_sentiment')
                elif isinstance(insights, str):
                    try:
                        insights_dict = json.loads(insights)
                        sentiment = insights_dict.get('sentiment_analysis', {}).get('overall_sentiment')
                    except json.JSONDecodeError:
                        sentiment = None
                else:
                    sentiment = None
                
                if sentiment:
                    sentiment_counts[sentiment.lower()] += 1
            
            if not sentiment_counts:
                return self._create_empty_chart("No sentiment data found")
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 8))
            
            labels = [label.title() for label in sentiment_counts.keys()]
            sizes = list(sentiment_counts.values())
            colors = [self.colors['success'], self.colors['warning'], self.colors['danger']][:len(labels)]
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            
            ax.set_title('Sentiment Distribution Across Sessions', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating sentiment distribution chart: {str(e)}")
            return self._create_empty_chart("Error generating chart")
    
    def generate_session_length_analysis(self, sessions: List[Dict]) -> str:
        """Generate analysis of session lengths over time"""
        try:
            if not sessions:
                return self._create_empty_chart("No session data available")
            
            # Extract session lengths (word counts as proxy)
            dates = []
            word_counts = []
            
            for session in sessions:
                if session.get('session_date') and session.get('raw_content'):
                    try:
                        date = session['session_date']
                        if isinstance(date, str):
                            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        dates.append(date)
                        
                        content = session['raw_content']
                        word_count = len(content.split()) if content else 0
                        word_counts.append(word_count)
                    except (ValueError, TypeError):
                        continue
            
            if not dates or not word_counts:
                return self._create_empty_chart("No valid session length data")
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(12, 6))
            
            bars = ax.bar(dates, word_counts, color=self.colors['secondary'], alpha=0.7)
            
            # Formatting
            ax.set_xlabel('Session Date')
            ax.set_ylabel('Word Count')
            ax.set_title('Session Length Analysis (Word Count)', fontsize=16, fontweight='bold')
            ax.grid(True, axis='y', alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Add average line
            avg_words = np.mean(word_counts)
            ax.axhline(y=avg_words, color=self.colors['danger'], linestyle='--', 
                      label=f'Average: {avg_words:.0f} words')
            ax.legend()
            
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating session length analysis: {str(e)}")
            return self._create_empty_chart("Error generating chart")
    
    def _generate_session_summary(self, sessions: List[Dict]) -> Dict:
        """Generate summary statistics for sessions"""
        if not sessions:
            return {}
        
        summary = {
            'total_sessions': len(sessions),
            'date_range': self._get_date_range(sessions),
            'avg_mood_score': self._calculate_avg_mood(sessions),
            'most_common_themes': self._get_top_themes(sessions, 5),
            'sentiment_breakdown': self._get_sentiment_breakdown(sessions)
        }
        
        return summary
    
    def _calculate_progress_metrics(self, sessions: List[Dict]) -> Dict:
        """Calculate progress metrics"""
        if len(sessions) < 2:
            return {}
        
        # Sort sessions by date
        sorted_sessions = sorted(sessions, key=lambda x: x.get('session_date', ''))
        
        # Calculate trends
        mood_scores = [s.get('sentiment_score', 0) for s in sorted_sessions if s.get('sentiment_score')]
        
        metrics = {}
        
        if len(mood_scores) >= 2:
            # Mood trend
            first_half = mood_scores[:len(mood_scores)//2]
            second_half = mood_scores[len(mood_scores)//2:]
            
            avg_first = np.mean(first_half) if first_half else 0
            avg_second = np.mean(second_half) if second_half else 0
            
            metrics['mood_trend'] = {
                'direction': 'improving' if avg_second > avg_first else 'declining' if avg_second < avg_first else 'stable',
                'change': round(avg_second - avg_first, 2),
                'first_half_avg': round(avg_first, 2),
                'second_half_avg': round(avg_second, 2)
            }
        
        # Session frequency
        if len(sorted_sessions) >= 2:
            first_date = sorted_sessions[0].get('session_date')
            last_date = sorted_sessions[-1].get('session_date')
            
            if first_date and last_date:
                try:
                    if isinstance(first_date, str):
                        first_date = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
                    if isinstance(last_date, str):
                        last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
                    
                    time_span = (last_date - first_date).days
                    if time_span > 0:
                        frequency = len(sessions) / (time_span / 7)  # Sessions per week
                        metrics['session_frequency'] = round(frequency, 2)
                except (ValueError, TypeError):
                    pass
        
        return metrics
    
    def _generate_insights(self, sessions: List[Dict], longitudinal_data: Dict = None) -> List[str]:
        """Generate textual insights based on data"""
        insights = []
        
        if not sessions:
            return ["No session data available for analysis"]
        
        # Mood insights
        mood_scores = [s.get('sentiment_score', 0) for s in sessions if s.get('sentiment_score')]
        if mood_scores:
            avg_mood = np.mean(mood_scores)
            if avg_mood >= 7:
                insights.append("Client demonstrates consistently positive mood across sessions")
            elif avg_mood <= 4:
                insights.append("Client shows signs of low mood that may need attention")
            else:
                insights.append("Client mood shows moderate levels with room for improvement")
        
        # Theme insights
        top_themes = self._get_top_themes(sessions, 3)
        if top_themes:
            theme_text = ", ".join([theme for theme, _ in top_themes])
            insights.append(f"Most discussed themes include: {theme_text}")
        
        # Progress insights
        if longitudinal_data:
            overall_progress = longitudinal_data.get('overall_progress', '')
            if overall_progress:
                insights.append(f"Longitudinal analysis indicates: {overall_progress}")
        
        # Session frequency insights
        if len(sessions) >= 4:
            insights.append("Good session consistency observed - regular attendance supports progress")
        elif len(sessions) < 2:
            insights.append("Limited session data - more sessions needed for comprehensive analysis")
        
        return insights if insights else ["Insufficient data for meaningful insights"]
    
    def _get_date_range(self, sessions: List[Dict]) -> str:
        """Get the date range of sessions"""
        dates = []
        for session in sessions:
            session_date = session.get('session_date')
            if session_date:
                try:
                    if isinstance(session_date, str):
                        date = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                    else:
                        date = session_date
                    dates.append(date)
                except (ValueError, TypeError):
                    continue
        
        if not dates:
            return "No valid dates found"
        
        min_date = min(dates)
        max_date = max(dates)
        
        return f"{min_date.strftime('%m/%d/%Y')} - {max_date.strftime('%m/%d/%Y')}"
    
    def _calculate_avg_mood(self, sessions: List[Dict]) -> Optional[float]:
        """Calculate average mood score"""
        mood_scores = [s.get('sentiment_score', 0) for s in sessions if s.get('sentiment_score')]
        return round(np.mean(mood_scores), 2) if mood_scores else None
    
    def _get_top_themes(self, sessions: List[Dict], limit: int = 5) -> List[Tuple[str, int]]:
        """Get top therapy themes"""
        theme_counts = defaultdict(int)
        
        for session in sessions:
            themes = session.get('key_themes', [])
            if isinstance(themes, list):
                for theme in themes:
                    if isinstance(theme, str) and theme.strip():
                        theme_counts[theme.strip().lower()] += 1
        
        return sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def _get_sentiment_breakdown(self, sessions: List[Dict]) -> Dict:
        """Get sentiment distribution"""
        sentiment_counts = defaultdict(int)
        
        for session in sessions:
            insights = session.get('therapy_insights', {})
            if isinstance(insights, dict):
                sentiment = insights.get('sentiment_analysis', {}).get('overall_sentiment')
            else:
                sentiment = None
            
            if sentiment:
                sentiment_counts[sentiment.lower()] += 1
        
        total = sum(sentiment_counts.values()) if sentiment_counts else 1
        return {k: round(v/total*100, 1) for k, v in sentiment_counts.items()}
    
    def _create_empty_chart(self, message: str) -> str:
        """Create an empty chart with a message"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, transform=ax.transAxes, 
               ha='center', va='center', fontsize=14, 
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        img_data = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        return base64.b64encode(img_data).decode('utf-8')
