#!/usr/bin/env python3
"""
Fix duplicate client entries in the database
"""
import sys
sys.path.append('.')

from app import app, db
from models import Client, Transcript, ProcessingLog
from datetime import datetime, timezone

def fix_duplicate_clients():
    """Consolidate duplicate client entries"""
    
    with app.app_context():
        # Get all duplicate client names
        duplicates_query = """
        SELECT name, ARRAY_AGG(id ORDER BY id) as client_ids
        FROM client 
        GROUP BY name 
        HAVING COUNT(*) > 1
        """
        
        result = db.session.execute(db.text(duplicates_query))
        duplicates = result.fetchall()
        
        print(f"Found {len(duplicates)} clients with duplicates")
        
        for duplicate in duplicates:
            client_name = duplicate[0]
            client_ids = duplicate[1]
            
            # Keep the first client (lowest ID), merge others into it
            primary_client_id = client_ids[0]
            duplicate_ids = client_ids[1:]
            
            print(f"Consolidating {client_name}: keeping ID {primary_client_id}, removing {duplicate_ids}")
            
            # Move all transcripts from duplicate clients to primary client
            for dup_id in duplicate_ids:
                # Update transcripts to point to primary client
                update_query = db.text("UPDATE transcript SET client_id = :primary WHERE client_id = :duplicate")
                db.session.execute(update_query, {'primary': primary_client_id, 'duplicate': dup_id})
                
                # Delete the duplicate client
                delete_query = db.text("DELETE FROM client WHERE id = :client_id")
                db.session.execute(delete_query, {'client_id': dup_id})
            
            db.session.commit()
            print(f"Consolidated {client_name}")
        
        # Verify the fix
        final_count = db.session.execute(db.text("SELECT COUNT(*) FROM client")).scalar()
        print(f"Final client count: {final_count}")
        
        # Log the fix
        log_entry = ProcessingLog(
            activity_type='database_cleanup',
            status='success',
            message=f'Consolidated {len(duplicates)} duplicate client entries, final count: {final_count}',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()

if __name__ == "__main__":
    fix_duplicate_clients()