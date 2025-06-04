"""
Rich text formatting service for comprehensive clinical progress notes
"""

import re
from typing import Dict, Any

class RichTextFormatter:
    """Service for formatting clinical progress notes with rich text elements"""
    
    def __init__(self):
        pass
    
    def format_clinical_progress_note(self, content: str, client_name: str, session_date: str) -> Dict[str, Any]:
        """Format comprehensive clinical progress note with rich text formatting"""
        
        # Parse the content and add proper formatting
        formatted_content = self._add_rich_text_formatting(content)
        
        # Create structured blocks for Notion
        notion_blocks = self._create_notion_blocks(formatted_content, client_name, session_date)
        
        return {
            'formatted_content': formatted_content,
            'notion_blocks': notion_blocks,
            'plain_text': content,
            'title': f"Comprehensive Clinical Progress Note for {client_name}'s Therapy Session on {session_date}"
        }
    
    def _add_rich_text_formatting(self, content: str) -> str:
        """Add rich text formatting to clinical progress note"""
        
        # Add title formatting
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Format section headers (major sections)
            if self._is_major_section_header(line):
                formatted_lines.append(f"## {line}")
            
            # Format subsection headers
            elif self._is_subsection_header(line):
                formatted_lines.append(f"### {line}")
            
            # Format analysis subsections
            elif self._is_analysis_subsection(line):
                formatted_lines.append(f"#### {line}")
            
            # Format key points and lists
            elif line.startswith('•') or line.startswith('-'):
                formatted_lines.append(f"• {line[1:].strip()}")
            
            # Format quotes (keep as is but ensure proper spacing)
            elif line.startswith('"') and line.endswith('"'):
                formatted_lines.append(f"> {line}")
            
            # Regular content
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _is_major_section_header(self, line: str) -> bool:
        """Check if line is a major section header"""
        major_sections = [
            'Subjective', 'Objective', 'Assessment', 'Plan',
            'Supplemental Analyses', 'Key Points', 'Significant Quotes',
            'Comprehensive Narrative Summary', 'Tonal Analysis',
            'Thematic Analysis'
        ]
        
        # Check if line matches any major section
        for section in major_sections:
            if line.lower().strip() == section.lower():
                return True
            if line.lower().startswith(section.lower()) and len(line) < len(section) + 10:
                return True
        
        return False
    
    def _is_subsection_header(self, line: str) -> bool:
        """Check if line is a subsection header"""
        subsection_patterns = [
            r'^Shift \d+:',
            r'^Theme \d+:',
            r'^Example:',
            r'^\d+\.\s+\*\*',
            r'^\d+\.\s+[A-Z]'
        ]
        
        for pattern in subsection_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _is_analysis_subsection(self, line: str) -> bool:
        """Check if line is an analysis subsection"""
        analysis_patterns = [
            'Dynamic Case Conceptualization Summary',
            'Longitudinal Progress Analysis',
            'Recurring Themes and Patterns',
            'Treatment Effectiveness Assessment',
            'Risk Assessment and Safety Considerations',
            'Updated Treatment Planning and Recommendations',
            'Therapeutic Relationship Dynamics',
            'Functional Improvement Indicators'
        ]
        
        for pattern in analysis_patterns:
            if pattern.lower() in line.lower():
                return True
        
        return False
    
    def _create_notion_blocks(self, formatted_content: str, client_name: str, session_date: str) -> list:
        """Create Notion-compatible rich text blocks"""
        
        blocks = []
        
        # Add title block
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"Comprehensive Clinical Progress Note for {client_name}'s Therapy Session on {session_date}"
                        },
                        "annotations": {
                            "bold": True,
                            "color": "blue"
                        }
                    }
                ]
            }
        })
        
        # Process content line by line
        lines = formatted_content.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line - finish current paragraph if any
                if current_paragraph:
                    blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
                    current_paragraph = []
                continue
            
            # Handle headers
            if line.startswith('## '):
                # Finish current paragraph
                if current_paragraph:
                    blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
                    current_paragraph = []
                
                # Add heading_2 block
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[3:]  # Remove '## '
                                },
                                "annotations": {
                                    "bold": True,
                                    "color": "default"
                                }
                            }
                        ]
                    }
                })
            
            elif line.startswith('### '):
                # Finish current paragraph
                if current_paragraph:
                    blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
                    current_paragraph = []
                
                # Add heading_3 block
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[4:]  # Remove '### '
                                },
                                "annotations": {
                                    "bold": True,
                                    "color": "default"
                                }
                            }
                        ]
                    }
                })
            
            elif line.startswith('#### '):
                # Finish current paragraph
                if current_paragraph:
                    blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
                    current_paragraph = []
                
                # Add heading_3 block (Notion doesn't have heading_4)
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[5:]  # Remove '#### '
                                },
                                "annotations": {
                                    "bold": True,
                                    "italic": True,
                                    "color": "gray"
                                }
                            }
                        ]
                    }
                })
            
            elif line.startswith('• '):
                # Finish current paragraph
                if current_paragraph:
                    blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
                    current_paragraph = []
                
                # Add bulleted list item
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[2:]  # Remove '• '
                                }
                            }
                        ]
                    }
                })
            
            elif line.startswith('> '):
                # Finish current paragraph
                if current_paragraph:
                    blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
                    current_paragraph = []
                
                # Add quote block
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[2:]  # Remove '> '
                                },
                                "annotations": {
                                    "italic": True,
                                    "color": "gray"
                                }
                            }
                        ]
                    }
                })
            
            else:
                # Regular content - add to current paragraph
                current_paragraph.append(line)
        
        # Add final paragraph if any
        if current_paragraph:
            blocks.append(self._create_paragraph_block('\n'.join(current_paragraph)))
        
        return blocks
    
    def _create_paragraph_block(self, content: str) -> Dict[str, Any]:
        """Create a paragraph block for Notion with proper content chunking"""
        # Notion has a 2000 character limit per rich text block
        # Split long content into multiple text objects within the same paragraph
        max_chunk_size = 1900  # Leave some buffer
        
        if len(content) <= max_chunk_size:
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        
        # Split content into chunks
        chunks = []
        remaining_content = content
        
        while remaining_content:
            if len(remaining_content) <= max_chunk_size:
                chunks.append(remaining_content)
                break
            
            # Find a good break point (sentence end, paragraph break, or space)
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
            
            chunks.append(remaining_content[:break_point])
            remaining_content = remaining_content[break_point:]
        
        # Create rich text objects for each chunk
        rich_text_objects = []
        for chunk in chunks:
            if chunk.strip():  # Only add non-empty chunks
                rich_text_objects.append({
                    "type": "text",
                    "text": {
                        "content": chunk
                    }
                })
        
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": rich_text_objects
            }
        }