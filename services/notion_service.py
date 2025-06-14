import os
import json
import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime, timezone
from config import Config

logger = logging.getLogger(__name__)

class NotionService:
    """Service for integrating with Notion API"""
    
    def __init__(self):
        self.integration_secret = Config.NOTION_INTEGRATION_SECRET
        if not self.integration_secret:
            logger.warning("Notion integration secret not found")
            self.headers = None
        else:
            self.headers = {
                "Authorization": f"Bearer {self.integration_secret}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
        
        self.base_url = "https://api.notion.com/v1"
    
    def test_connection(self) -> bool:
        """Test the Notion connection"""
        if not self.headers:
            logger.error("Notion integration secret not configured")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/users/me", headers=self.headers)
            if response.status_code == 200:
                logger.info("Notion connection successful")
                return True
            else:
                logger.error(f"Notion connection failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Notion connection error: {str(e)}")
            return False
    
    def create_progress_note(self, client_name: str, session_date: str, content: str, 
                           rich_text_blocks: List[Dict] = None, emotional_data: Dict = None, 
                           ai_analysis: Dict = None) -> Dict:
        """Create a progress note page in Notion database"""
        if not self.headers:
            logger.error("Notion not configured")
            return {"success": False, "error": "Notion not configured"}
        
        # Try to get client-specific database ID first, then fall back to config
        from models import Client
        client = Client.query.filter_by(name=client_name).first()
        database_id = client.notion_database_id if client and client.notion_database_id else Config.NOTION_DATABASE_ID
        
        if not database_id:
            logger.error("Notion database ID not configured")
            return {"success": False, "error": "Database ID not configured"}
        
        try:
            # Create page properties for the therapy session database
            properties = {
                "Session Title": {
                    "title": [
                        {
                            "text": {
                                "content": f"Session {session_date} - {client_name}"
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": session_date if session_date.count('-') == 2 else self._convert_date_format(session_date)
                    }
                },
                "Session Type": {
                    "select": {
                        "name": "Individual"
                    }
                },
                "Status": {
                    "select": {
                        "name": "Completed"
                    }
                }
            }
            
            # Add emotional analysis data if available
            if emotional_data:
                primary_emotion = emotional_data.get('primary_emotion', 'neutral')
                intensity = emotional_data.get('intensity', 0.5)
                
                properties["Primary Emotion"] = {
                    "select": {
                        "name": primary_emotion.title()
                    }
                }
                
                properties["Intensity"] = {
                    "number": intensity
                }
                
                # Add themes
                themes = [primary_emotion.title()]
                if emotional_data.get('secondary_emotion'):
                    themes.append(emotional_data.get('secondary_emotion').title())
                
                properties["Key Themes"] = {
                    "multi_select": [{"name": theme} for theme in themes]
                }
            
            # Add content to Progress Notes and Action Items
            if content:
                # Split content for Progress Notes (first part)
                progress_content = content[:1900] if len(content) > 1900 else content
                properties["Progress Notes"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": progress_content
                            }
                        }
                    ]
                }
                
                # Add action items summary
                action_summary = f"Follow-up on therapeutic progress. Continue emotional work with {emotional_data.get('primary_emotion', 'neutral')} emotion focus."
                properties["Action Items"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": action_summary
                            }
                        }
                    ]
                }
            
            # Create content blocks with complete content transfer (no truncation)
            content_blocks = []
            if rich_text_blocks:
                # Use the rich text blocks as-is - they're already properly chunked by RichTextFormatter
                content_blocks = rich_text_blocks
            else:
                # Split long content into multiple paragraphs without truncation
                text_chunks = []
                remaining_content = content
                max_chunk_size = 1900
                
                while remaining_content:
                    if len(remaining_content) <= max_chunk_size:
                        text_chunks.append(remaining_content)
                        break
                    
                    # Find the best break point (sentence, paragraph, or space)
                    chunk = remaining_content[:max_chunk_size]
                    break_point = max_chunk_size
                    
                    # Try to break at sentence end
                    for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
                        if chunk[i] in '.!?':
                            break_point = i + 1
                            break
                    
                    # If no sentence break, try paragraph break
                    if break_point == max_chunk_size:
                        for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
                            if chunk[i] == '\n':
                                break_point = i + 1
                                break
                    
                    # If no paragraph break, try space
                    if break_point == max_chunk_size:
                        for i in range(len(chunk) - 1, max(0, len(chunk) - 100), -1):
                            if chunk[i] == ' ':
                                break_point = i + 1
                                break
                    
                    text_chunks.append(remaining_content[:break_point])
                    remaining_content = remaining_content[break_point:]
                
                # Create paragraph blocks for each chunk (complete content, no truncation)
                for chunk in text_chunks:
                    if chunk.strip():  # Only add non-empty chunks
                        content_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": chunk
                                        }
                                    }
                                ]
                            }
                        })

            # Create the page
            page_data = {
                "parent": {"database_id": database_id},
                "properties": properties,
                "children": content_blocks
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                page_id = response.json().get('id')
                logger.info(f"Created Notion page for {client_name}: {page_id}")
                return {"success": True, "page_id": page_id}
            else:
                error_msg = f"Failed to create page: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"Error creating Notion page: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def create_client_database(self, client_name: str) -> Optional[str]:
        """Create a new database for a client in the parent page"""
        if not self.headers:
            logger.error("Notion not configured")
            return None
        
        from config import Config
        parent_page_id = Config.NOTION_PARENT_PAGE_ID
        if not parent_page_id:
            logger.error("Parent page ID not configured")
            return None
        
        try:
            # Create database structure for therapy sessions
            database_data = {
                "parent": {"page_id": parent_page_id},
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"{client_name} - Therapy Sessions"
                        }
                    }
                ],
                "properties": {
                    "Session Title": {
                        "title": {}
                    },
                    "Date": {
                        "date": {}
                    },
                    "Session Type": {
                        "select": {
                            "options": [
                                {"name": "Individual", "color": "blue"},
                                {"name": "Group", "color": "green"},
                                {"name": "Family", "color": "purple"},
                                {"name": "Assessment", "color": "orange"}
                            ]
                        }
                    },
                    "Primary Emotion": {
                        "select": {
                            "options": [
                                {"name": "Hopeful", "color": "green"},
                                {"name": "Anxious", "color": "yellow"},
                                {"name": "Sad", "color": "blue"},
                                {"name": "Angry", "color": "red"},
                                {"name": "Content", "color": "default"},
                                {"name": "Frustrated", "color": "orange"},
                                {"name": "Confused", "color": "gray"}
                            ]
                        }
                    },
                    "Intensity": {
                        "number": {
                            "format": "percent"
                        }
                    },
                    "Key Themes": {
                        "multi_select": {
                            "options": [
                                {"name": "Trauma", "color": "red"},
                                {"name": "Relationships", "color": "pink"},
                                {"name": "Anxiety", "color": "yellow"},
                                {"name": "Depression", "color": "blue"},
                                {"name": "Self-Esteem", "color": "purple"},
                                {"name": "Coping Skills", "color": "green"},
                                {"name": "Family", "color": "orange"}
                            ]
                        }
                    },
                    "Progress Notes": {
                        "rich_text": {}
                    },
                    "Action Items": {
                        "rich_text": {}
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Completed", "color": "green"},
                                {"name": "In Progress", "color": "yellow"},
                                {"name": "Cancelled", "color": "red"},
                                {"name": "Rescheduled", "color": "orange"}
                            ]
                        }
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/databases",
                headers=self.headers,
                json=database_data
            )
            
            if response.status_code == 200:
                database_id = response.json().get('id')
                logger.info(f"Created client database for {client_name}: {database_id}")
                return database_id
            else:
                error_msg = f"Failed to create database: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return None
                
        except Exception as e:
            logger.error(f"Error creating client database: {str(e)}")
            return None

    def create_transcript_page(self, database_id: str, transcript_data: Dict) -> Optional[str]:
        """Create a transcript page in the specified Notion database"""
        if not self.headers:
            logger.error("Notion not configured")
            return None
        
        try:
            # Extract data from transcript_data
            client_name = transcript_data.get('client_name', 'Unknown Client')
            session_date = transcript_data.get('session_date')
            filename = transcript_data.get('filename', 'Unknown File')
            openai_analysis = transcript_data.get('openai_analysis', {})
            anthropic_analysis = transcript_data.get('anthropic_analysis', {})
            gemini_analysis = transcript_data.get('gemini_analysis', {})
            therapy_insights = transcript_data.get('therapy_insights', {})
            sentiment_score = transcript_data.get('sentiment_score', 0.5)
            key_themes = transcript_data.get('key_themes', [])
            
            # Format session date
            if session_date:
                if isinstance(session_date, str):
                    formatted_date = session_date
                else:
                    formatted_date = session_date.strftime('%Y-%m-%d')
            else:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
            # Create page properties
            properties = {
                "Session Title": {
                    "title": [
                        {
                            "text": {
                                "content": f"Session {formatted_date} - {client_name}"
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": formatted_date
                    }
                },
                "Session Type": {
                    "select": {
                        "name": "Individual"
                    }
                },
                "Status": {
                    "select": {
                        "name": "Completed"
                    }
                }
            }
            
            # Add sentiment and themes if available
            if key_themes:
                properties["Key Themes"] = {
                    "multi_select": [{"name": theme} for theme in key_themes[:5]]  # Limit to 5 themes
                }
            
            if sentiment_score:
                properties["Intensity"] = {
                    "number": float(sentiment_score)
                }
            
            # Determine primary emotion from therapy insights
            primary_emotion = "Content"
            if therapy_insights and isinstance(therapy_insights, dict):
                emotion_data = therapy_insights.get('emotional_state', {})
                if emotion_data and isinstance(emotion_data, dict):
                    primary_emotion = emotion_data.get('primary_emotion', 'Content').title()
            
            properties["Primary Emotion"] = {
                "select": {
                    "name": primary_emotion
                }
            }
            
            # Create content blocks from AI analyses
            content_blocks = []
            
            # Add OpenAI Analysis
            if openai_analysis and isinstance(openai_analysis, dict):
                openai_content = openai_analysis.get('clinical_progress_note', 
                                                   openai_analysis.get('analysis', 
                                                                      str(openai_analysis)))
                if openai_content:
                    content_blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "OpenAI Clinical Analysis"}}]
                        }
                    })
                    
                    # Split content into chunks
                    chunks = self._split_content_into_chunks(str(openai_content))
                    for chunk in chunks:
                        content_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        })
            
            # Add Anthropic Analysis
            if anthropic_analysis and isinstance(anthropic_analysis, dict):
                anthropic_content = anthropic_analysis.get('clinical_progress_note', 
                                                         anthropic_analysis.get('analysis', 
                                                                               str(anthropic_analysis)))
                if anthropic_content:
                    content_blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Anthropic Clinical Analysis"}}]
                        }
                    })
                    
                    chunks = self._split_content_into_chunks(str(anthropic_content))
                    for chunk in chunks:
                        content_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        })
            
            # Add Gemini Analysis
            if gemini_analysis and isinstance(gemini_analysis, dict):
                gemini_content = gemini_analysis.get('clinical_progress_note', 
                                                   gemini_analysis.get('analysis', 
                                                                      str(gemini_analysis)))
                if gemini_content:
                    content_blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Gemini Clinical Analysis"}}]
                        }
                    })
                    
                    chunks = self._split_content_into_chunks(str(gemini_content))
                    for chunk in chunks:
                        content_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        })
            
            # Create the page
            page_data = {
                "parent": {"database_id": database_id},
                "properties": properties,
                "children": content_blocks
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                page_id = response.json().get('id')
                logger.info(f"Created transcript page: {page_id}")
                return page_id
            else:
                error_msg = f"Failed to create transcript page: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return None
                
        except Exception as e:
            logger.error(f"Error creating transcript page: {str(e)}")
            return None

    def _split_content_into_chunks(self, content: str, max_chunk_size: int = 1900) -> List[str]:
        """Split content into chunks suitable for Notion blocks"""
        if len(content) <= max_chunk_size:
            return [content]
        
        chunks = []
        remaining = content
        
        while remaining:
            if len(remaining) <= max_chunk_size:
                chunks.append(remaining)
                break
            
            # Find good break point
            chunk = remaining[:max_chunk_size]
            break_point = max_chunk_size
            
            # Try to break at sentence end
            for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
                if chunk[i] in '.!?':
                    break_point = i + 1
                    break
            
            # If no sentence break, try paragraph
            if break_point == max_chunk_size:
                for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
                    if chunk[i] == '\n':
                        break_point = i + 1
                        break
            
            # If no paragraph break, try space
            if break_point == max_chunk_size:
                for i in range(len(chunk) - 1, max(0, len(chunk) - 100), -1):
                    if chunk[i] == ' ':
                        break_point = i + 1
                        break
            
            chunks.append(remaining[:break_point])
            remaining = remaining[break_point:]
        
        return chunks
        
        try:
            # First, we need a parent page. For this example, we'll assume there's a main workspace page
            # In practice, you'd need to specify the parent page ID
            
            database_data = {
                "parent": {
                    "type": "page_id",
                    "page_id": "your-parent-page-id"  # This would need to be configured
                },
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"{client_name} - Therapy Sessions"
                        }
                    }
                ],
                "properties": {
                    "Session Date": {
                        "date": {}
                    },
                    "Session Summary": {
                        "rich_text": {}
                    },
                    "Mood Score": {
                        "number": {
                            "format": "number"
                        }
                    },
                    "Key Topics": {
                        "multi_select": {
                            "options": []
                        }
                    },
                    "Therapeutic Techniques": {
                        "multi_select": {
                            "options": []
                        }
                    },
                    "Progress Indicators": {
                        "rich_text": {}
                    },
                    "Sentiment": {
                        "select": {
                            "options": [
                                {"name": "Positive", "color": "green"},
                                {"name": "Neutral", "color": "gray"},
                                {"name": "Negative", "color": "red"}
                            ]
                        }
                    },
                    "File Name": {
                        "rich_text": {}
                    },
                    "Processing Date": {
                        "date": {}
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/databases",
                headers=self.headers,
                json=database_data
            )
            
            if response.status_code == 200:
                database_id = response.json()["id"]
                logger.info(f"Created Notion database for {client_name}: {database_id}")
                return database_id
            else:
                logger.error(f"Failed to create Notion database: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Notion database: {str(e)}")
            return None
    
    def add_session_to_database(self, database_id: str, session_data: Dict) -> Optional[str]:
        """Add a therapy session to a Notion database"""
        if not self.headers:
            logger.error("Notion not configured")
            return None
        
        try:
            # Extract data from session
            analysis = session_data.get('consolidated_insights', {})
            
            page_data = {
                "parent": {
                    "database_id": database_id
                },
                "properties": {
                    "Session Date": {
                        "date": {
                            "start": session_data.get('session_date', datetime.now(timezone.utc).isoformat())
                        }
                    },
                    "Session Summary": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": analysis.get('session_summary', 'No summary available')[:2000]  # Notion limit
                                }
                            }
                        ]
                    },
                    "Mood Score": {
                        "number": analysis.get('client_mood', 0)
                    },
                    "Key Topics": {
                        "multi_select": [
                            {"name": topic[:100]} for topic in analysis.get('key_topics', [])[:10]  # Limit topics
                        ]
                    },
                    "Therapeutic Techniques": {
                        "multi_select": [
                            {"name": technique[:100]} for technique in analysis.get('therapeutic_techniques', [])[:10]
                        ]
                    },
                    "Progress Indicators": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": self._format_progress_indicators(analysis)
                                }
                            }
                        ]
                    },
                    "Sentiment": {
                        "select": {
                            "name": analysis.get('sentiment_analysis', {}).get('overall_sentiment', 'Neutral').title()
                        }
                    },
                    "File Name": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": session_data.get('original_filename', 'Unknown')
                                }
                            }
                        ]
                    },
                    "Processing Date": {
                        "date": {
                            "start": datetime.now(timezone.utc).isoformat()
                        }
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                page_id = response.json()["id"]
                logger.info(f"Added session to Notion database: {page_id}")
                return page_id
            else:
                logger.error(f"Failed to add session to Notion: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding session to Notion: {str(e)}")
            return None
    
    def update_session_page(self, page_id: str, updates: Dict) -> bool:
        """Update an existing session page in Notion"""
        if not self.headers:
            logger.error("Notion not configured")
            return False
        
        try:
            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json={"properties": updates}
            )
            
            if response.status_code == 200:
                logger.info(f"Updated Notion page: {page_id}")
                return True
            else:
                logger.error(f"Failed to update Notion page: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Notion page: {str(e)}")
            return False
    
    def query_database(self, database_id: str, filter_params: Dict = None) -> List[Dict]:
        """Query a Notion database"""
        if not self.headers:
            logger.error("Notion not configured")
            return []
        
        try:
            query_data = {}
            if filter_params:
                query_data["filter"] = filter_params
            
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=query_data
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                logger.info(f"Retrieved {len(results)} pages from Notion database")
                return results
            else:
                logger.error(f"Failed to query Notion database: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error querying Notion database: {str(e)}")
            return []

    def _convert_date_format(self, date_str: str) -> str:
        """Convert MM/DD/YYYY format to YYYY-MM-DD ISO format"""
        try:
            from datetime import datetime
            if '/' in date_str:
                dt = datetime.strptime(date_str, '%m/%d/%Y')
                return dt.strftime('%Y-%m-%d')
            return date_str
        except:
            return date_str
    
    def create_longitudinal_report(self, database_id: str, longitudinal_analysis: Dict) -> Optional[str]:
        """Create a longitudinal progress report page"""
        if not self.headers:
            logger.error("Notion not configured")
            return None
        
        try:
            report_content = self._format_longitudinal_report(longitudinal_analysis)
            
            page_data = {
                "parent": {
                    "database_id": database_id
                },
                "properties": {
                    "Session Date": {
                        "date": {
                            "start": datetime.now(timezone.utc).isoformat()
                        }
                    },
                    "Session Summary": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Longitudinal Progress Report"
                                }
                            }
                        ]
                    },
                    "File Name": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Automated Progress Report"
                                }
                            }
                        ]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Longitudinal Progress Analysis"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": report_content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                page_id = response.json()["id"]
                logger.info(f"Created longitudinal report: {page_id}")
                return page_id
            else:
                logger.error(f"Failed to create longitudinal report: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating longitudinal report: {str(e)}")
            return None
    
    def _format_progress_indicators(self, analysis: Dict) -> str:
        """Format progress indicators for Notion"""
        indicators = []
        
        mood = analysis.get('client_mood')
        if mood:
            indicators.append(f"Mood: {mood}/10")
        
        sentiment = analysis.get('sentiment_analysis', {})
        if sentiment:
            indicators.append(f"Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
            if sentiment.get('engagement_level'):
                indicators.append(f"Engagement: {sentiment.get('engagement_level')}")
        
        confidence = analysis.get('confidence_scores', {})
        if confidence:
            indicators.append(f"Analysis Confidence: {confidence.get('overall_confidence', 0)*100:.0f}%")
        
        return " | ".join(indicators) if indicators else "No indicators available"
    
    def _format_longitudinal_report(self, analysis: Dict) -> str:
        """Format longitudinal analysis for Notion"""
        report_parts = []
        
        if analysis.get('overall_progress'):
            report_parts.append(f"Overall Progress: {analysis['overall_progress']}")
        
        trends = analysis.get('trend_analysis', {})
        if trends:
            report_parts.append("Trends:")
            for trend_type, trend_value in trends.items():
                report_parts.append(f"- {trend_type.replace('_', ' ').title()}: {trend_value}")
        
        if analysis.get('recurring_themes'):
            themes = ', '.join(analysis['recurring_themes'])
            report_parts.append(f"Recurring Themes: {themes}")
        
        if analysis.get('areas_for_focus'):
            focus_areas = ', '.join(analysis['areas_for_focus'])
            report_parts.append(f"Areas for Focus: {focus_areas}")
        
        return '\n\n'.join(report_parts) if report_parts else "No longitudinal data available"
    
    def get_database_info(self, database_id: str) -> Optional[Dict]:
        """Get information about a Notion database"""
        if not self.headers:
            logger.error("Notion not configured")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/databases/{database_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get database info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return None
