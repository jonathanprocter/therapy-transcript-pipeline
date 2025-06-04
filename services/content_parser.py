"""
Content parsing service for extracting client names and dates from transcripts
"""

import re
import logging
from datetime import datetime, date
from typing import Dict, Optional, Tuple
import dateutil.parser

logger = logging.getLogger(__name__)

class ContentParser:
    """Service for parsing client information and dates from transcript content"""
    
    def __init__(self):
        # Common name patterns in therapy transcripts
        self.name_patterns = [
            r"Client[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Patient[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[:\s]+(?:I|My|The|Today)",
            r"Session with[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Therapy session[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Progress note for[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s therapy session",
            r"Comprehensive Clinical Progress Note for[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s",
        ]
        
        # Date patterns for various formats
        self.date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
            r"(\d{2}/\d{2}/\d{4})",  # MM/DD/YYYY
            r"(\d{2}-\d{2}-\d{4})",  # MM-DD-YYYY
            r"(\d{1,2}/\d{1,2}/\d{4})",  # M/D/YYYY
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}",
            r"Session on[:\s]+([^.\n]+)",
            r"Date[:\s]+([^.\n]+)",
            r"Therapy Session on[:\s]+([^.\n]+)",
        ]
    
    def extract_client_and_date_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[date]]:
        """Extract client name and date from filename"""
        client_name = None
        session_date = None
        
        # Remove file extension
        name_part = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Common filename patterns: "ClientName_YYYY-MM-DD", "YYYY-MM-DD_ClientName", etc.
        patterns = [
            r"([A-Z][a-z]+(?:_[A-Z][a-z]+)*)[_\s-]+(\d{4}-\d{2}-\d{2})",
            r"(\d{4}-\d{2}-\d{2})[_\s-]+([A-Z][a-z]+(?:_[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[_\s-]+(\d{4}-\d{2}-\d{2})",
            r"(\d{4}-\d{2}-\d{2})[_\s-]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name_part)
            if match:
                part1, part2 = match.groups()
                # Determine which part is the name and which is the date
                if re.match(r'\d{4}-\d{2}-\d{2}', part1):
                    session_date = self._parse_date(part1)
                    client_name = part2.replace('_', ' ')
                elif re.match(r'\d{4}-\d{2}-\d{2}', part2):
                    client_name = part1.replace('_', ' ')
                    session_date = self._parse_date(part2)
                break
        
        # If no structured pattern, try to extract any date and name separately
        if not client_name or not session_date:
            # Look for dates in filename
            for pattern in self.date_patterns:
                match = re.search(pattern, name_part)
                if match and not session_date:
                    session_date = self._parse_date(match.group(1))
                    break
            
            # Look for potential names (capitalized words)
            if not client_name:
                name_match = re.search(r'([A-Z][a-z]+(?:[_\s][A-Z][a-z]+)*)', name_part)
                if name_match:
                    client_name = name_match.group(1).replace('_', ' ')
        
        return client_name, session_date
    
    def extract_client_and_date_from_content(self, content: str) -> Tuple[Optional[str], Optional[date]]:
        """Extract client name and date from transcript content"""
        client_name = None
        session_date = None
        
        # Look for client name in content
        for pattern in self.name_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                potential_name = match.group(1).strip()
                # Validate it looks like a real name (not common words)
                if self._is_valid_name(potential_name):
                    client_name = potential_name
                    break
        
        # Look for session date in content
        for pattern in self.date_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                date_str = match.group(1) if match.groups() else match.group(0)
                session_date = self._parse_date(date_str)
                if session_date:
                    break
        
        return client_name, session_date
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if a string looks like a person's name"""
        if not name or len(name) < 2:
            return False
        
        # Exclude common therapy-related words that might be capitalized
        excluded_words = {
            'Therapist', 'Client', 'Patient', 'Session', 'Today', 'The', 'This', 
            'Therapy', 'Treatment', 'Progress', 'Note', 'Assessment', 'Plan',
            'Objective', 'Subjective', 'Clinical', 'Comprehensive', 'Analysis'
        }
        
        words = name.split()
        for word in words:
            if word in excluded_words:
                return False
        
        # Must contain only letters, spaces, and common name characters
        if not re.match(r'^[A-Za-z\s\'-]+$', name):
            return False
        
        # Should start with capital letter
        if not name[0].isupper():
            return False
        
        return True
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse various date formats into a date object"""
        if not date_str:
            return None
        
        try:
            # Clean up the date string
            date_str = date_str.strip()
            
            # Try parsing with dateutil (handles most formats)
            parsed_date = dateutil.parser.parse(date_str, fuzzy=True)
            return parsed_date.date()
            
        except Exception as e:
            logger.debug(f"Could not parse date '{date_str}': {str(e)}")
            return None
    
    def extract_comprehensive_info(self, filename: str, content: str) -> Dict:
        """Extract all available information from filename and content"""
        # Try filename first
        filename_client, filename_date = self.extract_client_and_date_from_filename(filename)
        
        # Then try content
        content_client, content_date = self.extract_client_and_date_from_content(content)
        
        # Prioritize filename info, fall back to content
        final_client = filename_client or content_client
        final_date = filename_date or content_date
        
        # If still no date, use today as fallback
        if not final_date:
            final_date = date.today()
        
        return {
            'client_name': final_client,
            'session_date': final_date,
            'filename_client': filename_client,
            'filename_date': filename_date,
            'content_client': content_client,
            'content_date': content_date,
            'extraction_source': {
                'client': 'filename' if filename_client else 'content' if content_client else 'unknown',
                'date': 'filename' if filename_date else 'content' if content_date else 'default'
            }
        }