import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, timezone
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
        plt.style.use('seaborn-v0_8-whitegrid')
        self.colors = {
            'primary': '#4A90E2', 'secondary': '#6c757d', 'success': '#50C878',
            'warning': '#F5A623', 'danger': '#E85D75', 'info': '#7B68EE',
            'light_gray': '#f0f0f0', 'medium_gray': '#adb5bd', 'dark_gray': '#343a40',
            'neutral_tint': '#8E9AAF',
            'palette_mood_trend_line': '#4A90E2', 'palette_mood_trend_trendline': '#6c757d',
            'palette_emotions_distinct': ['#E85D75', '#F5A623', '#50C878', '#4A90E2', '#7B68EE', '#FF7F50', '#DA70D6'],
            'palette_intensity_gradient': ['#98FB98', '#FFD700', '#F5A623', '#E85D75'], # Light green to red
            'palette_progress_radar_main': '#4A90E2',
            'palette_progress_radar_fill': 'rgba(74, 144, 226, 0.25)'
        }
    
    def _fig_to_base64(self, fig) -> str:
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        img_data = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        return base64.b64encode(img_data).decode('utf-8')

    def _create_empty_chart_b64(self, message: str) -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, message, transform=ax.transAxes,
               ha='center', va='center', fontsize=14,
               bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors.get('light_gray', '#f0f0f0')))
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
        return self._fig_to_base64(fig)

    def _render_chart_image(self, chart_type: str, chart_data_payload: Optional[Dict]) -> str:
        """
        Renders a chart of a specific type using its data payload.
        Returns a base64 encoded PNG string or an empty chart image string on error/no data.
        """
        if not chart_data_payload:
            logger.warning(f"No chart data payload provided for chart type '{chart_type}'. Generating empty chart.")
            return self._create_empty_chart_b64(f"{chart_type.replace('_', ' ').title()} data unavailable")

        fig = None
        try:
            figsize = (12, 6) # Default for most line/bar charts
            if chart_type == 'progress_radar':
                figsize = (8, 8) # Radar often looks better square

            # For radar, a polar projection is needed.
            if chart_type == 'progress_radar':
                fig = plt.figure(figsize=figsize)
                ax = fig.add_subplot(111, projection='polar')
            else:
                fig, ax = plt.subplots(figsize=figsize)

            if chart_type == 'emotional_timeline':
                self._plot_emotional_timeline_internal(ax, chart_data_payload)
            elif chart_type == 'progress_radar':
                self._plot_progress_radar_internal(ax, chart_data_payload) # ax is already polar
            elif chart_type == 'intensity_heatmap':
                self._plot_intensity_heatmap_internal(ax, chart_data_payload)
            else:
                logger.warning(f"Unknown chart_type '{chart_type}' for _render_chart_image.")
                plt.close(fig)
                return self._create_empty_chart_b64(f"Chart type '{chart_type}' not recognized.")
            
            plt.tight_layout() # Apply tight_layout before saving
            return self._fig_to_base64(fig)

        except Exception as e:
            logger.exception(f"Error rendering chart type '{chart_type}': {e}")
            if fig: plt.close(fig)
            return self._create_empty_chart_b64(f"Error generating {chart_type.replace('_', ' ')} chart.")

    # --- Migrated Plotting Methods (Phase 3) ---
    def _plot_emotional_timeline_internal(self, ax: plt.Axes, chart_data_payload: Dict):
        labels = chart_data_payload.get('labels', [])
        intensities = chart_data_payload.get('intensities', [])
        point_colors = chart_data_payload.get('colors', [])

        if not labels or not intensities or len(labels) != len(intensities):
            logger.warning("Insufficient or mismatched data for emotional timeline plot."); return
        
        x_dates = []
        valid_intensities = []
        valid_point_colors = []

        for i, date_str in enumerate(labels):
            try:
                x_dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
                valid_intensities.append(intensities[i])
                if point_colors and len(point_colors) == len(labels):
                    valid_point_colors.append(point_colors[i])
            except (ValueError, TypeError):
                logger.warning(f"Invalid date format or data for emotional timeline plotting: {date_str}")
        
        if not x_dates or len(x_dates) != len(valid_intensities):
            logger.warning("Data point mismatch after date conversion for emotional timeline."); return

        scatter_colors = valid_point_colors if valid_point_colors else self.colors.get('palette_mood_trend_line')
        
        ax.scatter(x_dates, valid_intensities, c=scatter_colors, s=100, alpha=0.7, edgecolors='black', zorder=3)
        
        if len(x_dates) > 1:
            try:
                x_numeric = mdates.date2num(x_dates)
                # Ensure only finite values are used for polyfit
                finite_indices = np.isfinite(x_numeric) & np.isfinite(valid_intensities)
                if np.sum(finite_indices) > 1:
                    x_numeric_finite = x_numeric[finite_indices]
                    intensities_finite = np.array(valid_intensities)[finite_indices]
                    z = np.polyfit(x_numeric_finite, intensities_finite, 1); p = np.poly1d(z)
                    ax.plot(mdates.num2date(x_numeric_finite), p(x_numeric_finite), "--", color=self.colors.get('palette_mood_trend_trendline'), alpha=0.8, zorder=2)
            except Exception as e: logger.error(f"Trend line error in emotional timeline: {e}")

        ax.set_title('Emotional Intensity Timeline', fontsize=16, fontweight='bold'); ax.set_xlabel('Session Date', fontsize=12)
        ax.set_ylabel('Emotional Intensity (0-1)', fontsize=12); ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.5, zorder=0)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y'));
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=7))
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    def _plot_progress_radar_internal(self, ax: plt.Axes, chart_data_payload: Dict):
        categories = chart_data_payload.get('categories', [])
        metrics_values = chart_data_payload.get('metrics', {})
        if not categories or not metrics_values: logger.warning("Not enough data for progress radar."); return

        current_values = [metrics_values.get(cat, [0.5])[-1] if metrics_values.get(cat) else 0.5 for cat in categories]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        current_values += current_values[:1]; angles += angles[:1]

        ax.plot(angles, current_values, 'o-', linewidth=2, color=self.colors.get('palette_progress_radar_main'))
        ax.fill(angles, current_values, color=self.colors.get('palette_progress_radar_fill'), alpha=0.25)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels([c.replace('_', ' ').title() for c in categories])
        ax.set_yticks(np.arange(0, 1.1, 0.2)); ax.set_ylim(0, 1)
        # ax.set_title('Therapy Progress Indicators', fontsize=16, fontweight='bold', pad=20) # Title set by fig in _render_chart_image

    def _plot_intensity_heatmap_internal(self, ax: plt.Axes, chart_data_payload: Dict):
        weekly_data = chart_data_payload.get('weekly_data', {})
        if not weekly_data: logger.warning("No data for intensity heatmap."); return
        sorted_weeks = sorted(weekly_data.keys()); intensities = [weekly_data[w] for w in sorted_weeks]
        if not intensities: logger.warning("No intensity values for heatmap."); return
        
        gradient = self.colors.get('palette_intensity_gradient', ['#98FB98', '#FFD700', '#F5A623', '#E85D75'])
        bar_colors = [gradient[0] if i < 0.3 else gradient[1] if i < 0.6 else gradient[2] if i < 0.8 else gradient[3] for i in intensities]
        
        ax.bar(range(len(sorted_weeks)), intensities, color=bar_colors, alpha=0.8)
        ax.set_title('Weekly Emotional Intensity Patterns', fontsize=16, fontweight='bold')
        ax.set_xlabel('Week (YYYY-Www)', fontsize=12); ax.set_ylabel('Average Intensity (0-1)', fontsize=12)
        week_labels = [w.split('-W')[-1] if '-W' in w else w for w in sorted_weeks]
        ax.set_xticks(range(len(sorted_weeks))); ax.set_xticklabels(week_labels, rotation=45, ha="right")
        ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.5)

    # --- Existing Chart Generation Methods (Direct b64 generation) ---
    def generate_mood_trend_chart(self, sessions: List[Dict]) -> str:
        # This method should ideally be refactored to use get_emotional_timeline_data and _render_chart_image
        # For now, it remains a direct b64 generator.
        # Simplified for brevity, assuming its original implementation is functional with new colors.
        if not sessions: return self._create_empty_chart_b64("No mood data available")
        # ... (original plotting logic, adapted for self.colors) ...
        # Example: (taken from previous state, ensure it's complete and correct if used)
        dates, mood_scores = [], []
        for session in sessions:
            if session.get('session_date') and session.get('sentiment_score') is not None:
                try:
                    date_val = session['session_date']
                    date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00')) if isinstance(date_val, str) else date_val
                    dates.append(date_obj)
                    mood_scores.append(float(session['sentiment_score']))
                except (ValueError, TypeError) as e: logger.warning(f"Error parsing session data for mood trend: {e}")
        if not dates or not mood_scores: return self._create_empty_chart_b64("No valid mood data found")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, mood_scores, marker='o', linewidth=2, markersize=6, color=self.colors.get('palette_mood_trend_line', self.colors['primary']), label='Mood Score')
        if len(dates) > 2:
            try:
                x_numeric = mdates.date2num(dates)
                valid_idx = np.isfinite(x_numeric) & np.isfinite(mood_scores)
                if np.sum(valid_idx) > 1:
                    x_numeric_valid, mood_scores_valid = x_numeric[valid_idx], np.array(mood_scores)[valid_idx]
                    z = np.polyfit(x_numeric_valid, mood_scores_valid, 1); p = np.poly1d(z)
                    ax.plot(mdates.num2date(x_numeric_valid), p(x_numeric_valid), "--", color=self.colors.get('palette_mood_trend_trendline', self.colors['secondary']), alpha=0.7, label='Trend')
            except Exception as e: logger.error(f"Mood trend line error: {e}")
        ax.set_xlabel('Session Date'); ax.set_ylabel('Mood Score (0-1 scale)'); ax.set_title('Client Mood Trend Over Time', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3); ax.legend(); ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=10)); plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        ax.set_ylim(0, 1.05); plt.tight_layout(); return self._fig_to_base64(fig)


    def generate_theme_frequency_chart(self, sessions: List[Dict]) -> str: # Remains direct b64 generation
        if not sessions: return self._create_empty_chart_b64("No theme data available")
        theme_counts = defaultdict(int)
        for session in sessions:
            themes = session.get('key_themes', [])
            if isinstance(themes, str): themes = json.loads(themes or '[]')
            if isinstance(themes, list):
                for theme in themes:
                    if isinstance(theme, str) and theme.strip(): theme_counts[theme.strip().lower()] += 1
        if not theme_counts: return self._create_empty_chart_b64("No themes found in sessions")
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        themes, counts = zip(*sorted_themes)
        fig, ax = plt.subplots(figsize=(12, 8)); bars = ax.barh(range(len(themes)), counts, color=self.colors.get('info', '#7B68EE'))
        ax.set_yticks(range(len(themes))); ax.set_yticklabels([theme.title() for theme in themes])
        ax.set_xlabel('Frequency'); ax.set_title('Most Frequent Therapy Themes', fontsize=16, fontweight='bold')
        for i, (bar, count) in enumerate(zip(bars, counts)):
             ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, str(count), va='center', fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3); plt.tight_layout(); return self._fig_to_base64(fig)

    def generate_sentiment_distribution_chart(self, sessions: List[Dict]) -> str: # Remains direct b64 generation
        if not sessions: return self._create_empty_chart_b64("No sentiment data available")
        sentiment_counts = defaultdict(int)
        for session in sessions:
            insights = session.get('therapy_insights', {})
            current_sentiment = None
            if isinstance(insights, dict):
                current_sentiment = insights.get('sentiment_analysis', {}).get('overall_sentiment')
            elif isinstance(insights, str):
                try: insights_dict = json.loads(insights) if insights.strip() else {}
                except json.JSONDecodeError: insights_dict = {}
                current_sentiment = insights_dict.get('sentiment_analysis', {}).get('overall_sentiment')
            if current_sentiment and isinstance(current_sentiment, str): sentiment_counts[current_sentiment.lower()] += 1
        if not sentiment_counts: return self._create_empty_chart_b64("No sentiment data found")
        fig, ax = plt.subplots(figsize=(8, 8)); labels = [label.title() for label in sentiment_counts.keys()]
        sizes = list(sentiment_counts.values())
        chart_colors = self.colors.get('palette_emotions_distinct', [self.colors.get('success'), self.colors.get('warning'), self.colors.get('danger')])
        ax.pie(sizes, labels=labels, colors=chart_colors[:len(labels)], autopct='%1.1f%%', startangle=90)
        ax.set_title('Sentiment Distribution Across Sessions', fontsize=16, fontweight='bold'); plt.tight_layout(); return self._fig_to_base64(fig)

    def generate_session_length_analysis(self, sessions: List[Dict]) -> str: # Remains direct b64 generation
        if not sessions: return self._create_empty_chart_b64("No session data available")
        dates, word_counts = [], []
        for session in sessions:
            if session.get('session_date') and session.get('raw_content'):
                try:
                    date_val = session['session_date']
                    date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00')) if isinstance(date_val, str) else date_val
                    dates.append(date_obj)
                    word_counts.append(len(str(session['raw_content']).split()))
                except (ValueError, TypeError) as e: logger.warning(f"Error parsing session data for length analysis: {e}")
        if not dates or not word_counts: return self._create_empty_chart_b64("No valid session length data")
        fig, ax = plt.subplots(figsize=(12, 6)); ax.bar(dates, word_counts, color=self.colors.get('secondary', '#6c757d'), alpha=0.7)
        ax.set_xlabel('Session Date'); ax.set_ylabel('Word Count'); ax.set_title('Session Length Analysis (Word Count)', fontsize=16, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3); ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=10)); plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        if word_counts: avg_words = np.mean(word_counts); ax.axhline(y=avg_words, color=self.colors.get('danger', '#E85D75'), linestyle='--', label=f'Average: {avg_words:.0f} words'); ax.legend()
        plt.tight_layout(); return self._fig_to_base64(fig)
    
    # --- Helper methods for dashboard data (textual) ---
    def _generate_session_summary(self, sessions: List[Dict]) -> Dict:
        if not sessions: return {}
        return {'total_sessions': len(sessions), 'date_range': self._get_date_range(sessions),
                'avg_mood_score': self._calculate_avg_mood(sessions),
                'most_common_themes': self._get_top_themes(sessions, 5),
                'sentiment_breakdown': self._get_sentiment_breakdown(sessions)}

    def _calculate_progress_metrics(self, sessions: List[Dict]) -> Dict: # Original AnalyticsService version
        if len(sessions) < 2: return {}
        def get_safe_date(s):
            date_val = s.get('session_date');
            if isinstance(date_val, str):
                try: return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                except ValueError: return datetime.min
            return date_val if isinstance(date_val, datetime) else datetime.min
        
        sorted_sessions = sorted([s for s in sessions if s.get('session_date')], key=get_safe_date)
        sorted_sessions = [s for s in sorted_sessions if get_safe_date(s) != datetime.min] # Filter out invalid dates
        if not sorted_sessions or len(sorted_sessions) < 2 : return {} # Need at least 2 valid dates
        
        mood_scores = [s.get('sentiment_score') for s in sorted_sessions if s.get('sentiment_score') is not None]
        metrics = {}
        if len(mood_scores) >= 2: # Check if enough mood scores are available
            valid_mood_scores = [float(s) for s in mood_scores if isinstance(s, (int, float))]
            if len(valid_mood_scores) >=2: # Check again after filtering non-float scores
                mid_point = len(valid_mood_scores)//2
                first_half_mood = valid_mood_scores[:mid_point] if mid_point > 0 else [] # Ensure slices are not empty
                second_half_mood = valid_mood_scores[mid_point:] if mid_point <= len(valid_mood_scores) else []

                avg_first = np.mean(first_half_mood) if first_half_mood else 0
                avg_second = np.mean(second_half_mood) if second_half_mood else avg_first if not first_half_mood and second_half_mood else 0 # Handle cases with few data points

                direction = 'stable'
                if avg_second > avg_first + 0.05: direction = 'improving'
                elif avg_second < avg_first - 0.05: direction = 'declining'
                metrics['mood_trend'] = {'direction': direction, 'change': round(avg_second - avg_first, 2), 'first_half_avg': round(avg_first, 2), 'second_half_avg': round(avg_second, 2)}
        
        dates = [get_safe_date(s) for s in sorted_sessions]
        if len(dates) >= 2:
            time_span_days = (dates[-1] - dates[0]).days
            if time_span_days > 0: metrics['session_frequency'] = round(len(sorted_sessions) / (time_span_days / 7), 2)
        return metrics

    def _generate_insights(self, sessions: List[Dict], longitudinal_data: Optional[Dict] = None) -> List[str]:
        insights = [];
        if not sessions: return ["No session data available for analysis."]
        mood_scores = [s.get('sentiment_score') for s in sessions if s.get('sentiment_score') is not None]
        valid_mood_scores = [float(s) for s in mood_scores if isinstance(s, (int,float))]
        if valid_mood_scores:
            avg_mood = np.mean(valid_mood_scores)
            if avg_mood >= 0.7: insights.append("Client demonstrates consistently positive mood (average > 0.7 on 0-1 scale).")
            elif avg_mood <= 0.3: insights.append("Client shows signs of low mood (average < 0.3 on 0-1 scale) that may need attention.")
            else: insights.append("Client mood is moderate (0.3-0.7 on 0-1 scale).")
        else: insights.append("Mood scores are not consistently available for trend analysis.")

        top_themes = self._get_top_themes(sessions, 3)
        if top_themes: insights.append(f"Most discussed themes: {', '.join([t[0].title() for t in top_themes])}.")
        else: insights.append("Key themes are yet to be identified consistently.")

        if longitudinal_data and longitudinal_data.get('overall_progress'): insights.append(f"Longitudinal: {longitudinal_data['overall_progress']}")
        
        if len(sessions) >= 4: insights.append("Sufficient session data for initial trend observation.")
        elif len(sessions) > 0 and len(sessions) < 2 : insights.append("Limited data; more sessions needed for robust analysis.")
        
        return insights if insights else ["Awaiting more data to generate specific insights."]

    def _get_date_range(self, sessions: List[Dict]) -> str:
        dates = []
        for session in sessions:
            sd_str = session.get('session_date')
            if sd_str:
                try: date_obj = datetime.fromisoformat(sd_str.replace('Z', '+00:00')) if isinstance(sd_str, str) else sd_str
                except ValueError: continue
                if isinstance(date_obj, datetime): dates.append(date_obj)
        if not dates: return "N/A"
        return f"{min(dates).strftime('%m/%d/%Y')} - {max(dates).strftime('%m/%d/%Y')}"

    def _calculate_avg_mood(self, sessions: List[Dict]) -> Optional[float]:
        mood_scores = [s.get('sentiment_score') for s in sessions if s.get('sentiment_score') is not None]
        valid_scores = [float(s) for s in mood_scores if isinstance(s, (int,float))]
        return round(np.mean(valid_scores), 2) if valid_scores else None

    def _get_top_themes(self, sessions: List[Dict], limit: int = 5) -> List[Tuple[str, int]]:
        theme_counts = defaultdict(int)
        for session in sessions:
            themes = session.get('key_themes', [])
            if isinstance(themes, str):
                try: themes = json.loads(themes) if themes.strip() else []
                except json.JSONDecodeError: themes = []
            if isinstance(themes, list):
                for theme in themes:
                    if isinstance(theme, str) and theme.strip(): theme_counts[theme.strip().lower()] += 1
        return sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def _get_sentiment_breakdown(self, sessions: List[Dict]) -> Dict:
        sentiment_counts = defaultdict(int)
        for session in sessions:
            insights = session.get('therapy_insights', {})
            current_sentiment = None
            if isinstance(insights, dict): current_sentiment = insights.get('sentiment_analysis', {}).get('overall_sentiment')
            elif isinstance(insights, str):
                try: insights_dict = json.loads(insights) if insights.strip() else {}
                except json.JSONDecodeError: insights_dict = {}
                current_sentiment = insights_dict.get('sentiment_analysis', {}).get('overall_sentiment')
            if current_sentiment and isinstance(current_sentiment, str): sentiment_counts[current_sentiment.lower()] += 1
        total = sum(sentiment_counts.values())
        return {k: round(v / total * 100, 1) for k, v in sentiment_counts.items()} if total > 0 else {}

    # --- Main Public Dashboard Generation Method ---
    def generate_progress_dashboard(self, sessions: List[Dict], client_data: Dict, longitudinal_data: Optional[Dict] = None) -> Dict:
        logger.info(f"Generating progress dashboard for client: {client_data.get('name', 'Unknown') if client_data else 'Unknown'}")
        output = {
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        try:
            output['mood_trend_chart_b64'] = self.generate_mood_trend_chart(sessions)
            output['theme_frequency_chart_b64'] = self.generate_theme_frequency_chart(sessions)
            output['sentiment_distribution_chart_b64'] = self.generate_sentiment_distribution_chart(sessions)
            output['session_length_chart_b64'] = self.generate_session_length_analysis(sessions)

            emotional_timeline_full_data = self.get_emotional_timeline_data(sessions)
            output['emotional_timeline_chart_b64'] = self._render_chart_image('emotional_timeline', emotional_timeline_full_data.get('chart_data'))

            progress_indicators_full_data = self.get_progress_indicators_data(sessions)
            output['progress_radar_chart_b64'] = self._render_chart_image('progress_radar', progress_indicators_full_data.get('chart_data'))

            intensity_heatmap_full_data = self.get_session_intensity_heatmap_data(sessions)
            output['intensity_heatmap_chart_b64'] = self._render_chart_image('intensity_heatmap', intensity_heatmap_full_data.get('chart_data'))

            output['session_summary'] = self._generate_session_summary(sessions)
            output['progress_indicators_summary'] = progress_indicators_full_data.get('metrics',{})

            main_as_insights = self._generate_insights(sessions, longitudinal_data)
            vis_timeline_insights = emotional_timeline_full_data.get('insights', [])
            vis_heatmap_patterns = intensity_heatmap_full_data.get('patterns', [])

            output['generated_insights'] = {
                'main_analytics_insights': main_as_insights,
                'emotional_trend_insights': vis_timeline_insights,
                'intensity_pattern_insights': vis_heatmap_patterns
            }
            
            vis_themes_and_insights = self.get_visualization_service_derived_themes_and_insights(sessions)
            output['visualization_themes'] = vis_themes_and_insights.get('themes')
            output['visualization_insights'] = vis_themes_and_insights.get('insights')

            output['client_summary_for_visuals'] = self.get_visualization_service_client_summary(client_data, sessions)
            return output
        except Exception as e:
            logger.exception(f"Error generating full progress dashboard for client {client_data.get('name', 'Unknown')}: {e}")
            error_info = {"error": "Failed to generate complete progress dashboard."}
            return {**output, **error_info}

    # --- Migrated Data Generation Methods (Phase 2) ---
    def get_emotional_timeline_data(self, sessions: List[Dict]) -> Dict:
        if not sessions: logger.info("No sessions for emotional timeline."); return {'chart_data': None, 'insights': [], 'total_sessions': 0}
        def get_date_obj(s):
            val = s.get('session_date');
            if isinstance(val, str):
                try: return datetime.fromisoformat(val.replace('Z', '+00:00'))
                except ValueError: return datetime.min
            return val if isinstance(val, datetime) else datetime.min
        
        valid_sessions = [s for s in sessions if s.get('session_date')]
        sorted_sessions = sorted(valid_sessions, key=get_date_obj)
        sorted_sessions = [s for s in sorted_sessions if get_date_obj(s) != datetime.min]

        if not sorted_sessions: return {'chart_data': None, 'insights': [], 'total_sessions': 0}
        
        data = {'labels':[], 'emotions':[], 'intensities':[], 'colors':[]}
        for s in sorted_sessions:
            s_date_iso = get_date_obj(s).isoformat()
            e_data = s.get('emotional_analysis', {});
            if isinstance(e_data, str): e_data = json.loads(e_data or '{}')
            if not isinstance(e_data, dict): e_data = {}
            data['labels'].append(s_date_iso); data['emotions'].append(e_data.get('primary_emotion', 'neutral'))
            try: data['intensities'].append(float(e_data.get('intensity', 0.5)))
            except (ValueError, TypeError): data['intensities'].append(0.5)
            palette = e_data.get('color_palette', {}); data['colors'].append(palette.get('primary', self.colors.get('neutral_tint')))

        insights = self._analyze_emotional_trends(data['emotions'], data['intensities'])
        return {'chart_data': data, 'insights': insights, 'total_sessions': len(data['labels'])}

    def get_progress_indicators_data(self, sessions: List[Dict]) -> Dict:
        if not sessions: return {'chart_data': None, 'metrics': {}, 'sessions_analyzed': 0}
        keywords = {'emotional_regulation': ['emotion regulation', 'coping skills'], 'insight_development': ['insight', 'awareness'],
                    'behavioral_changes': ['behavior change', 'skill application'], 'engagement_levels': ['engagement', 'motivation'],
                    'goal_progression': ['goal progress', 'objective met']}
        metrics_vals = {k: [] for k in keywords}; dates = []
        def get_date(s): val=s.get('session_date');
            if isinstance(val,str):
                try: return datetime.fromisoformat(val.replace('Z','+00:00'))
                except ValueError: return datetime.min
            return val if isinstance(val,datetime) else datetime.min
        
        valid_s = [s for s in sessions if s.get('session_date')]
        sorted_sessions = sorted(valid_s,key=get_date)
        sorted_sessions = [s for s in sorted_sessions if get_date(s) != datetime.min]

        if not sorted_sessions: return {'chart_data':None,'metrics':{},'sessions_analyzed':0}

        for s in sorted_sessions:
            dates.append(get_date(s).isoformat())
            txt = ""; insight_data=s.get('therapy_insights','');
            if isinstance(insight_data,dict): txt += insight_data.get('narrative_summary','') + " " + " ".join(insight_data.get('key_themes',[]))
            elif isinstance(insight_data,str): txt += insight_data
            if len(txt)<100 and s.get('raw_content'): txt += str(s.get('raw_content',''))
            for metric, kw_list in keywords.items():
                score=0.5; found=sum(1 for kw in kw_list if kw.lower() in txt.lower())
                if found==0:score=0.3; elif found==1:score=0.6; elif found>=2:score=0.8
                metrics_vals[metric].append(score)

        summary={};
        for metric,vals in metrics_vals.items():
            if vals: cur=vals[-1];avg=sum(vals)/len(vals);trend='stable'
            if len(vals)>1: first=vals[0];
            if cur>first+0.1:trend='improving'; elif cur<first-0.1:trend='declining'
            summary[metric]={'current':round(cur,2),'average':round(avg,2),'trend':trend,'history':[round(v,2) for v in vals]}

        return {'chart_data':{'labels':dates,'metrics':metrics_vals,'categories':list(keywords.keys()),'chart_type':'progress_radar'},
                'metrics':summary,'sessions_analyzed':len(dates)}

    def get_session_intensity_heatmap_data(self, sessions: List[Dict]) -> Dict:
        if not sessions: return {'chart_data': None, 'patterns': [], 'weeks_analyzed': 0}
        intensity_map = defaultdict(list)
        for session in sessions:
            s_date_str = session.get('session_date')
            if not s_date_str: continue
            try:
                date_obj = datetime.fromisoformat(s_date_str.replace('Z','+00:00')) if isinstance(s_date_str,str) else s_date_str if isinstance(s_date_str, datetime) else None
                if not date_obj: continue
                week_key = date_obj.strftime('%Y-W%W')
                e_data = session.get('emotional_analysis',{});
                if isinstance(e_data,str): e_data=json.loads(e_data or '{}')
                if not isinstance(e_data,dict): e_data={}
                intensity_map[week_key].append(float(e_data.get('intensity',0.5)))
            except Exception as e: logger.warning(f"Error processing session for heatmap {s_date_str}: {e}")

        if not intensity_map: return {'chart_data': None, 'patterns': [], 'weeks_analyzed': 0}
        weekly_avg = {wk:sum(val)/len(val) for wk,val in intensity_map.items() if val}
        sorted_weekly_avg = dict(sorted(weekly_avg.items()))
        patterns = self._identify_intensity_patterns(sorted_weekly_avg)
        return {'chart_data':{'weekly_data':sorted_weekly_avg,'chart_type':'intensity_heatmap'},
                'patterns':patterns,'weeks_analyzed':len(sorted_weekly_avg)}

    def get_visualization_service_derived_themes_and_insights(self, sessions: List[Dict]) -> Dict:
        if not sessions: return {'themes':[],'insights':[],'total_distinct_themes':0}
        theme_freq=defaultdict(int); insights_list=[]
        for s in sessions:
            t_insights=s.get('therapy_insights',{});
            if isinstance(t_insights,str): t_insights=json.loads(t_insights or '{}')
            if not isinstance(t_insights,dict): t_insights={}

            for theme in t_insights.get('key_themes',[]):
                if isinstance(theme,str) and theme.strip():theme_freq[theme.strip().lower()]+=1
            consolidated=t_insights.get('consolidated_insights',{})
            if isinstance(consolidated,dict):
                for topic in consolidated.get('key_topics',[]):
                    if isinstance(topic,str) and topic.strip(): insights_list.append(topic.strip())
            transcript_themes = s.get('key_themes', [])
            if isinstance(transcript_themes, str):
                try: transcript_themes = json.loads(transcript_themes) if transcript_themes.strip() else []
                except: transcript_themes = []
            if isinstance(transcript_themes, list):
                 for theme in transcript_themes:
                     if isinstance(theme,str) and theme.strip(): theme_freq[theme.strip().lower()]+=1

        sorted_themes=sorted(theme_freq.items(),key=lambda x:x[1],reverse=True)[:15]
        unique_insights = list(dict.fromkeys(insights_list))[:20]
        return {'themes':sorted_themes,'insights':unique_insights,'total_distinct_themes':len(theme_freq)}

    def get_visualization_service_client_summary(self, client_data: Dict, sessions: List[Dict]) -> Dict:
        if not sessions: return {'client_name':client_data.get('name','Client'),'total_sessions':0,'treatment_duration_days':0,
                                'current_emotional_state':'N/A','current_intensity':'N/A','latest_session_date':None,
                                'summary_generated':datetime.now(timezone.utc).isoformat(),'notes':"No session data."}
        total_s = len(sessions)
        def get_date(s):
            val=s.get('session_date');
            if isinstance(val,str):
                try: return datetime.fromisoformat(val.replace('Z','+00:00'))
                except ValueError: return datetime.min
            return val if isinstance(val,datetime) else datetime.min

        valid_s = [s for s in sessions if s.get('session_date')]
        sorted_valid_s = sorted(valid_s, key=get_date)
        sorted_valid_s = [s for s in sorted_valid_s if get_date(s) != datetime.min]

        if not sorted_valid_s: latest_s_obj=None; dates=[]
        else: latest_s_obj=sorted_valid_s[-1]; dates=[get_date(s) for s in sorted_valid_s]

        duration=0
        if dates: duration=(dates[-1]-dates[0]).days

        emotion,intensity,latest_date_iso = 'N/A','N/A',None
        if latest_s_obj:
            latest_date_iso = get_date(latest_s_obj).isoformat() if get_date(latest_s_obj) != datetime.min else None
            e_data=latest_s_obj.get('emotional_analysis',{});
            if isinstance(e_data,str): e_data=json.loads(e_data or '{}')
            if not isinstance(e_data,dict): e_data={}
            emotion=e_data.get('primary_emotion','unknown'); intensity_val=e_data.get('intensity')
            try: intensity=float(intensity_val) if intensity_val is not None else 'N/A'
            except (ValueError, TypeError): intensity='N/A'

        return {'client_name':client_data.get('name','Client'),'total_sessions':total_s,'treatment_duration_days':duration,
                'current_emotional_state':emotion,'current_intensity':intensity,'latest_session_date':latest_date_iso,
                'summary_generated':datetime.now(timezone.utc).isoformat()}

    # --- Migrated Helper Methods (from Phase 2) ---

    def _analyze_emotional_trends(self, emotions: List[str], intensities: List[float]) -> List[str]:
        """
        Analyzes emotional trends from a list of emotions and intensities.
        (Migrated from VisualizationService._analyze_emotional_trends)
        """
        insights = []
        if not emotions or not intensities:
            return insights

        unique_emotions = len(set(emotions))
        if unique_emotions <= 2 and len(emotions) > 1:
            insights.append("Shows emotional consistency across sessions.")
        elif unique_emotions >= 5:
            insights.append("Experiencing varied emotional states, which may indicate active processing or exploration.")

        if len(intensities) >= 3:
            recent_avg = sum(intensities[-3:]) / 3 if len(intensities[-3:]) > 0 else 0
            early_avg = sum(intensities[:3]) / 3 if len(intensities[:3]) > 0 else 0

            if recent_avg < early_avg - 0.2:
                insights.append("Emotional intensity appears to be decreasing over recent sessions, potentially indicating progress in regulation.")
            elif recent_avg > early_avg + 0.2:
                insights.append("Emotional intensity appears to be increasing over recent sessions, which may warrant further attention.")

        if emotions:
            emotion_counts = defaultdict(int)
            for emotion in emotions:
                emotion_counts[emotion] += 1

            if emotion_counts:
                most_common_emotion, count = max(emotion_counts.items(), key=lambda x: x[1])
                if count >= len(emotions) * 0.4 and len(emotions) > 1:
                    insights.append(f"The emotion '{most_common_emotion}' is predominantly experienced, suggesting a consistent emotional pattern.")

        if not insights and len(emotions) > 1 :
            insights.append("Emotional patterns are present but require more specific analysis or more data for clear trends.")
        elif not insights and len(emotions) == 1:
            insights.append("Single session data available; longitudinal trends will become clearer with more sessions.")

        return insights

    def _identify_intensity_patterns(self, weekly_data: Dict) -> List[str]:
        """
        Identifies patterns in emotional intensity over time from weekly data.
        (Migrated from VisualizationService._identify_intensity_patterns)
        """
        patterns = []
        if not weekly_data or len(weekly_data) < 3:
            logger.info("Not enough weekly data to identify intensity patterns.")
            return patterns

        intensities = list(weekly_data.values())
        num_weeks = len(intensities)

        high_intensity_threshold = 0.7
        low_intensity_threshold = 0.3

        high_weeks_count = sum(1 for intensity in intensities if intensity >= high_intensity_threshold)
        low_weeks_count = sum(1 for intensity in intensities if intensity <= low_intensity_threshold)

        if high_weeks_count / num_weeks >= 0.3:
            patterns.append("Recurring periods of high emotional intensity noted.")

        if low_weeks_count / num_weeks >= 0.3:
            patterns.append("Recurring periods of lower emotional intensity or stability observed.")

        if num_weeks >= 4:
            first_half_len = num_weeks // 2
            second_half_len = num_weeks - first_half_len

            if first_half_len > 0 and second_half_len > 0:
                first_half_avg = sum(intensities[:first_half_len]) / first_half_len
                second_half_avg = sum(intensities[first_half_len:]) / second_half_len

                if second_half_avg < first_half_avg - 0.15:
                    patterns.append("Overall trend suggests a decrease in average emotional intensity over time.")
                elif second_half_avg > first_half_avg + 0.15:
                    patterns.append("Overall trend suggests an increase in average emotional intensity over time.")
                else:
                    patterns.append("Average emotional intensity appears relatively stable over the observed period.")

        if not patterns and num_weeks >=3 :
            patterns.append("Emotional intensity shows some fluctuation without forming strong, identifiable long-term patterns from current data.")
        elif not patterns:
            patterns.append("Insufficient data to identify specific intensity patterns, or patterns are not prominent.")

        return patterns

[end of services/analytics_service.py]
