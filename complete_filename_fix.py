"""
Complete filename standardization with proper military time format
Fix all remaining filenames that don't follow the exact format: "Firstname Lastname MM-DD-YYYY HHMM hrs.ext"
"""
import os
import sys
import re
import logging
from datetime import datetime

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_military_time(filename):
    """Extract military time (HHMM) from filename"""
    # Pattern for military time followed by hrs
    time_patterns = [
        r'(\d{4})\s*hrs?',  # 1000 hrs, 0930 hrs
        r'(\d{1,2}):(\d{2})',  # 10:00, 9:30
        r'(\d{1,2})(\d{2})(?=\s*hrs?)',  # 1000hrs, 930hrs
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, filename)
        if match:
            if len(match.groups()) == 1:
                # Single group like "1000"
                time_str = match.group(1)
                if len(time_str) == 4:
                    return time_str
                elif len(time_str) <= 2:
                    # Just hour, add 00 minutes
                    return f"{int(time_str):02d}00"
                else:
                    return time_str.zfill(4)
            else:
                # Two groups like hour:minute
                hour, minute = match.groups()
                return f"{int(hour):02d}{minute}"
    
    # Default to 1200 (noon) if no time found
    return "1200"

def fix_remaining_filenames():
    """Fix all filenames that don't follow standard format"""
    with app.app_context():
        from sqlalchemy import text
        
        # Get all transcripts with non-standard filenames
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name, t.created_at
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL
            AND (
                t.original_filename LIKE '%_%' OR
                t.original_filename LIKE '%Appointment%' OR
                t.original_filename LIKE '%/%' OR
                t.original_filename NOT LIKE '% %-%-% % hrs.%'
            )
            ORDER BY c.name, t.created_at
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        logger.info(f"Fixing {len(transcripts)} non-standard filenames")
        
        fixed_count = 0
        
        for row in transcripts:
            transcript_id, original_filename, client_name, created_at = row
            
            # Extract date
            date_patterns = [
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            ]
            
            date_extracted = None
            for pattern in date_patterns:
                match = re.search(pattern, original_filename)
                if match:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # First group is year
                        year, month, day = groups
                    else:  # First group is month
                        month, day, year = groups
                    
                    date_extracted = f"{int(month):02d}-{int(day):02d}-{year}"
                    break
            
            # Use creation date if no date found
            if not date_extracted:
                date_extracted = created_at.strftime('%m-%d-%Y')
            
            # Extract military time
            time_extracted = extract_military_time(original_filename)
            
            # Get file extension
            ext_match = re.search(r'\.(pdf|txt|docx)$', original_filename.lower())
            extension = ext_match.group(1) if ext_match else 'pdf'
            
            # Create standardized filename with "Appointment"
            new_filename = f"{client_name} Appointment {date_extracted} {time_extracted} hrs.{extension}"
            
            if new_filename != original_filename:
                # Update in database
                transcript = db.session.get(Transcript, transcript_id)
                if transcript:
                    transcript.original_filename = new_filename
                    fixed_count += 1
                    logger.info(f"Fixed: {client_name}")
                    logger.info(f"  From: {original_filename}")
                    logger.info(f"  To:   {new_filename}")
        
        db.session.commit()
        logger.info(f"Filename standardization complete. Fixed {fixed_count} filenames.")
        
        return fixed_count

def verify_nancy_grossman():
    """Verify Nancy Grossman's files are properly formatted"""
    with app.app_context():
        from sqlalchemy import text
        
        query = text("""
            SELECT t.id, t.original_filename
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE c.name ILIKE '%nancy%' AND c.name ILIKE '%grossman%'
            ORDER BY t.original_filename
        """)
        
        result = db.session.execute(query)
        files = result.fetchall()
        
        logger.info("Nancy Grossman's current filenames:")
        for file_id, filename in files:
            logger.info(f"  {filename}")
        
        return files

def main():
    """Main execution function"""
    logger.info("Starting complete filename standardization")
    
    # Show Nancy's files before
    verify_nancy_grossman()
    
    # Fix all remaining non-standard filenames
    fixed_count = fix_remaining_filenames()
    
    # Show Nancy's files after
    logger.info(f"\nStandardization complete. Fixed {fixed_count} files.")
    verify_nancy_grossman()

if __name__ == "__main__":
    main()