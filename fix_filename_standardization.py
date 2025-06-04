"""
Fix filename standardization to follow exact format: "Firstname Lastname MM-DD-YYYY 2400 hrs"
"""
import os
import sys
import re
import logging
from datetime import datetime, timezone

sys.path.append('/home/runner/workspace')

from app import app, db
from models import Transcript, Client
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def standardize_filename(original_filename, client_name, created_at):
    """Standardize filename to exact format: 'Firstname Lastname MM-DD-YYYY 2400 hrs.ext'"""
    try:
        # Get file extension
        ext_match = re.search(r'\.(pdf|txt|docx)$', original_filename.lower())
        extension = ext_match.group(1) if ext_match else 'pdf'
        
        # Extract date from filename
        date_extracted = None
        
        # Try various date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',  # MM/DD/YY or MM-DD-YY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, original_filename)
            if match:
                groups = match.groups()
                if len(groups[2]) == 2:  # Two-digit year
                    year = f"20{groups[2]}"
                else:
                    year = groups[2]
                
                # Determine if it's MM/DD/YYYY or YYYY/MM/DD
                if len(groups[0]) == 4:  # First group is year
                    month, day = groups[1], groups[2]
                    year = groups[0]
                else:  # First group is month
                    month, day = groups[0], groups[1]
                
                # Format as MM-DD-YYYY
                date_extracted = f"{int(month):02d}-{int(day):02d}-{year}"
                break
        
        # If no date found in filename, use creation date
        if not date_extracted:
            date_extracted = created_at.strftime('%m-%d-%Y')
        
        # Extract time if available
        time_extracted = None
        time_patterns = [
            r'(\d{4})\s*hrs?',  # 1000 hrs, 0930 hrs
            r'(\d{1,2}):(\d{2})',  # 10:00, 9:30
            r'(\d{1,2})(\d{2})\s*hrs?',  # 1000hrs, 930hrs
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, original_filename)
            if match:
                if len(match.groups()) == 1:
                    # Single group like "1000" from "1000 hrs"
                    time_str = match.group(1)
                    if len(time_str) == 4:
                        time_extracted = time_str
                    elif len(time_str) <= 2:
                        # Just hour, assume 00 minutes
                        time_extracted = f"{int(time_str):02d}00"
                    else:
                        time_extracted = time_str.zfill(4)
                else:
                    # Two groups like hour:minute
                    hour, minute = match.groups()
                    time_extracted = f"{int(hour):02d}{minute}"
                break
        
        # Default to 1200 (noon) if no time found
        if not time_extracted:
            time_extracted = "1200"
        
        # Create standardized filename
        standardized = f"{client_name} {date_extracted} {time_extracted} hrs.{extension}"
        
        return standardized
        
    except Exception as e:
        logger.error(f"Filename standardization failed: {str(e)}")
        return original_filename

def fix_all_filenames():
    """Fix all filenames to follow standard format"""
    with app.app_context():
        from sqlalchemy import text
        
        # Get all transcripts
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name, t.created_at
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL
            ORDER BY c.name, t.created_at
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        logger.info(f"Processing {len(transcripts)} transcripts for filename standardization")
        
        fixed_count = 0
        
        for row in transcripts:
            transcript_id, original_filename, client_name, created_at = row
            
            # Standardize filename
            new_filename = standardize_filename(original_filename, client_name, created_at)
            
            if new_filename != original_filename:
                # Update in database
                transcript = db.session.get(Transcript, transcript_id)
                if transcript:
                    transcript.original_filename = new_filename
                    fixed_count += 1
                    logger.info(f"Fixed: {client_name}")
                    logger.info(f"  From: {original_filename}")
                    logger.info(f"  To:   {new_filename}")
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Standardization complete. Fixed {fixed_count} filenames.")

def show_nancy_grossman_files():
    """Show Nancy Grossman's files specifically"""
    with app.app_context():
        from sqlalchemy import text
        
        query = text("""
            SELECT t.id, t.original_filename, t.created_at
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE c.name ILIKE '%nancy%' AND c.name ILIKE '%grossman%'
            ORDER BY t.created_at
        """)
        
        result = db.session.execute(query)
        files = result.fetchall()
        
        logger.info("Nancy Grossman's files:")
        for file_id, filename, created_at in files:
            logger.info(f"  ID {file_id}: {filename}")

def main():
    """Main execution function"""
    logger.info("Starting filename standardization fix")
    
    # Show Nancy's files before
    show_nancy_grossman_files()
    
    # Fix all filenames
    fix_all_filenames()
    
    # Show Nancy's files after
    logger.info("\nAfter standardization:")
    show_nancy_grossman_files()

if __name__ == "__main__":
    main()