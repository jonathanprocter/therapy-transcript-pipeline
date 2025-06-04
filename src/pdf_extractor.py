import os
import logging
import tempfile
from datetime import datetime
import PyPDF2

class PDFExtractor:
    """
    Extracts text content from PDF files using PyPDF2.
    Also provides utilities for extracting client names and session dates.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, file_path):
        """
        Extract text from a file (PDF, TXT, or other supported formats).
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Extracted text content or None if extraction fails
        """
        try:
            # Check file extension to determine processing method
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.txt':
                # Handle text files
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            
            elif file_ext == '.pdf':
                # Handle PDF files
                text_content = ""
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        text_content += page.extract_text() + "\n\n"
                return text_content
            
            else:
                # Try to read as text file for other formats
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        return file.read()
                except UnicodeDecodeError:
                    # If UTF-8 fails, try other encodings
                    for encoding in ['latin-1', 'cp1252']:
                        try:
                            with open(file_path, 'r', encoding=encoding) as file:
                                return file.read()
                        except:
                            continue
                    raise ValueError(f"Unable to decode file with any supported encoding")
            
        except Exception as e:
            self.logger.error(f"Error extracting text from file {file_path}: {str(e)}")
            return None
    
    def extract_client_name(self, text_content):
        """
        Attempt to extract client name from text content.
        
        Args:
            text_content: Text content of the PDF
            
        Returns:
            str: Client name or None if not found
        """
        # Look for common patterns in therapy transcripts
        # Example: "Client: John Smith" or "Patient: John Smith"
        
        lines = text_content.split('\n')
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            
            # Check for "Client:" or "Patient:" prefix
            if line.lower().startswith("client:") and len(line) > 7:
                return line[7:].strip()
            
            if line.lower().startswith("patient:") and len(line) > 8:
                return line[8:].strip()
            
            # Check for "Name:" prefix
            if line.lower().startswith("name:") and len(line) > 5:
                return line[5:].strip()
        
        return None
    
    def extract_session_date(self, text_content, filename=None):
        """
        Attempt to extract session date from text content or filename.
        
        Args:
            text_content: Text content of the PDF
            filename: Optional filename to check for date
            
        Returns:
            str: Session date in ISO format or None if not found
        """
        # First try to extract from filename if provided
        if filename:
            date = self._extract_date_from_filename(filename)
            if date:
                return date
        
        # Then try to extract from content
        lines = text_content.split('\n')
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            
            # Check for "Date:" prefix
            if line.lower().startswith("date:") and len(line) > 5:
                date_str = line[5:].strip()
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
            
            # Check for "Session Date:" prefix
            if line.lower().startswith("session date:") and len(line) > 13:
                date_str = line[13:].strip()
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _extract_date_from_filename(self, filename):
        """
        Extract date from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            str: Date in ISO format or None if not found
        """
        # Remove extension
        name_part = os.path.splitext(filename)[0]
        
        # Look for date patterns
        import re
        
        # Pattern: MM-DD-YYYY or MM/DD/YYYY
        pattern1 = r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
        match = re.search(pattern1, name_part)
        if match:
            month, day, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern: YYYY-MM-DD or YYYY/MM/DD
        pattern2 = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        match = re.search(pattern2, name_part)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return None
    
    def _parse_date_string(self, date_str):
        """
        Parse a date string into ISO format.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            str: Date in ISO format or None if parsing fails
        """
        try:
            from dateutil import parser
            date_obj = parser.parse(date_str)
            return date_obj.strftime("%Y-%m-%d")
        except:
            return None
