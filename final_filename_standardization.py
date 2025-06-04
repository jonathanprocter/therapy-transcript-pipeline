"""
Final filename standardization to ensure ALL files follow exact format:
"Firstname Lastname Appointment MM-DD-YYYY HHMM hrs.ext"
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

def standardize_all_filenames():
    """Standardize ALL filenames to exact format"""
    with app.app_context():
        from sqlalchemy import text
        
        # Get ALL transcripts
        query = text("""
            SELECT t.id, t.original_filename, c.name as client_name, t.created_at
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL
            ORDER BY c.name, t.created_at
        """)
        
        result = db.session.execute(query)
        transcripts = result.fetchall()
        
        logger.info(f"Standardizing {len(transcripts)} filenames")
        
        fixed_count = 0
        
        for row in transcripts:
            transcript_id, original_filename, client_name, created_at = row
            
            # Skip if already in perfect format
            if re.match(r'^[A-Za-z]+ [A-Za-z]+ Appointment \d{2}-\d{2}-\d{4} \d{4} hrs\.(pdf|txt|docx)$', original_filename):
                continue
            
            # Extract date from filename
            date_extracted = None
            date_patterns = [
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, original_filename)
                if match:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # First group is year (YYYY-MM-DD)
                        year, month, day = groups
                    else:  # First group is month (MM-DD-YYYY)
                        month, day, year = groups
                    
                    date_extracted = f"{int(month):02d}-{int(day):02d}-{year}"
                    break
            
            # Use creation date if no date found
            if not date_extracted:
                date_extracted = created_at.strftime('%m-%d-%Y')
            
            # Extract time (military format HHMM)
            time_extracted = "1200"  # Default to noon
            time_patterns = [
                r'(\d{4})\s*hrs?',  # 1000 hrs, 0930 hrs
                r'(\d{1,2}):(\d{2})',  # 10:00, 9:30
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, original_filename)
                if match:
                    if len(match.groups()) == 1:
                        time_str = match.group(1)
                        if len(time_str) == 4:
                            time_extracted = time_str
                        elif len(time_str) <= 2:
                            time_extracted = f"{int(time_str):02d}00"
                        else:
                            time_extracted = time_str.zfill(4)
                    else:
                        hour, minute = match.groups()
                        time_extracted = f"{int(hour):02d}{minute}"
                    break
            
            # Get file extension
            ext_match = re.search(r'\.(pdf|txt|docx)$', original_filename.lower())
            extension = ext_match.group(1) if ext_match else 'pdf'
            
            # Create standardized filename
            new_filename = f"{client_name} Appointment {date_extracted} {time_extracted} hrs.{extension}"
            
            if new_filename != original_filename:
                # Update in database
                transcript = db.session.get(Transcript, transcript_id)
                if transcript:
                    transcript.original_filename = new_filename
                    fixed_count += 1
                    logger.info(f"Fixed #{transcript_id}: {client_name}")
                    logger.info(f"  From: {original_filename}")
                    logger.info(f"  To:   {new_filename}")
        
        db.session.commit()
        logger.info(f"Final standardization complete. Fixed {fixed_count} filenames.")
        
        return fixed_count

def verify_all_standardized():
    """Verify all filenames are now properly standardized"""
    with app.app_context():
        from sqlalchemy import text
        
        # Check for any remaining non-standard filenames
        query = text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN t.original_filename ~ '^[A-Za-z]+ [A-Za-z]+ Appointment \\d{2}-\\d{2}-\\d{4} \\d{4} hrs\\.(pdf|txt|docx)$' THEN 1 END) as standardized
            FROM transcript t
            JOIN client c ON t.client_id = c.id
            WHERE t.raw_content IS NOT NULL
        """)
        
        result = db.session.execute(query)
        row = result.fetchone()
        total, standardized = row
        
        logger.info(f"Verification: {standardized}/{total} files properly standardized")
        
        if standardized < total:
            # Show remaining non-standard files
            query2 = text("""
                SELECT t.original_filename, c.name
                FROM transcript t
                JOIN client c ON t.client_id = c.id
                WHERE t.raw_content IS NOT NULL
                AND NOT (t.original_filename ~ '^[A-Za-z]+ [A-Za-z]+ Appointment \\d{2}-\\d{2}-\\d{4} \\d{4} hrs\\.(pdf|txt|docx)$')
                LIMIT 10
            """)
            
            result2 = db.session.execute(query2)
            remaining = result2.fetchall()
            
            logger.info("Remaining non-standard files:")
            for filename, client in remaining:
                logger.info(f"  {client}: {filename}")
        
        return standardized == total

def main():
    """Main execution function"""
    logger.info("Starting final filename standardization")
    
    # Standardize all filenames
    fixed_count = standardize_all_filenames()
    
    # Verify all are standardized
    all_good = verify_all_standardized()
    
    if all_good:
        logger.info("✓ All filenames are now properly standardized!")
    else:
        logger.warning("Some files still need standardization")

if __name__ == "__main__":
    main()