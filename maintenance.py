"""Utility commands for database cleanup and filename fixes."""

import logging
from datetime import datetime, timezone
from typing import List
import re

from app import app, db
from models import Client, Transcript, ProcessingLog
from config import Config
import openai

logger = logging.getLogger(__name__)

# ---------------------- Duplicate Client Fix ----------------------

def fix_duplicate_clients() -> None:
    """Consolidate clients with the same name into a single entry."""
    with app.app_context():
        query = db.text(
            "SELECT name, ARRAY_AGG(id ORDER BY id) as client_ids "
            "FROM client GROUP BY name HAVING COUNT(*) > 1"
        )
        duplicates = db.session.execute(query).fetchall()
        logger.info("Found %s clients with duplicates", len(duplicates))

        for client_name, client_ids in duplicates:
            primary_id = client_ids[0]
            for dup_id in client_ids[1:]:
                db.session.execute(
                    db.text("UPDATE transcript SET client_id = :p WHERE client_id = :d"),
                    {"p": primary_id, "d": dup_id},
                )
                db.session.execute(
                    db.text("DELETE FROM client WHERE id = :id"), {"id": dup_id}
                )
            db.session.commit()
            logger.info("Consolidated %s into id %s", client_name, primary_id)

        final_count = db.session.execute(db.text("SELECT COUNT(*) FROM client")).scalar()
        log_entry = ProcessingLog(
            activity_type="database_cleanup",
            status="success",
            message=f"Consolidated {len(duplicates)} duplicate clients, final count: {final_count}",
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(log_entry)
        db.session.commit()

# ---------------------- Filename Standardization ----------------------

def standardize_filename(original: str, client_name: str, created_at: datetime) -> str:
    """Return filename in 'Firstname Lastname MM-DD-YYYY 2400 hrs.ext' format."""
    ext_match = re.search(r"\.(pdf|txt|docx)$", original.lower())
    extension = ext_match.group(1) if ext_match else "pdf"

    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2})",
    ]
    date_extracted = None
    for pattern in date_patterns:
        match = re.search(pattern, original)
        if match:
            groups = match.groups()
            year = f"20{groups[2]}" if len(groups[2]) == 2 else groups[2]
            if len(groups[0]) == 4:
                month, day, year = groups[1], groups[2], groups[0]
            else:
                month, day = groups[0], groups[1]
            date_extracted = f"{int(month):02d}-{int(day):02d}-{year}"
            break
    if not date_extracted:
        date_extracted = created_at.strftime("%m-%d-%Y")

    time_patterns = [r"(\d{4})\s*hrs?", r"(\d{1,2}):(\d{2})", r"(\d{1,2})(\d{2})\s*hrs?"]
    time_extracted = None
    for pattern in time_patterns:
        match = re.search(pattern, original)
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
    if not time_extracted:
        time_extracted = "1200"

    return f"{client_name} {date_extracted} {time_extracted} hrs.{extension}"

def standardize_all_filenames() -> None:
    """Update every transcript filename to the standard format."""
    with app.app_context():
        query = db.text(
            "SELECT t.id, t.original_filename, c.name, t.created_at "
            "FROM transcript t JOIN client c ON t.client_id = c.id "
            "WHERE t.raw_content IS NOT NULL ORDER BY c.name, t.created_at"
        )
        rows = db.session.execute(query).fetchall()
        logger.info("Processing %s transcripts for filename standardization", len(rows))
        fixed = 0
        for tid, original, client_name, created_at in rows:
            new_name = standardize_filename(original, client_name, created_at)
            if new_name != original:
                transcript = db.session.get(Transcript, tid)
                if transcript:
                    transcript.original_filename = new_name
                    fixed += 1
        db.session.commit()
        logger.info("Standardization complete. Fixed %s filenames", fixed)

# ---------------------- AI Analysis Fix ----------------------

def fix_transcript_analysis(limit: int = 5) -> None:
    """Generate OpenAI analyses for transcripts missing them."""
    with app.app_context():
        transcripts = Transcript.query.filter(Transcript.openai_analysis.is_(None)).all()
        logger.info("Found %s transcripts needing AI analysis", len(transcripts))
        if not transcripts:
            return

        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        for i, transcript in enumerate(transcripts[:limit]):
            cli = db.session.get(Client, transcript.client_id)
            prompt = (
                f"Create a comprehensive clinical progress note for {cli.name}'s therapy session.\n"
                f"Session transcript content:\n{transcript.raw_content[:8000]}"
            )
            try:
                response = client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{"role": "system", "content": "You are an expert clinical therapist."}, {"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.7,
                )
                analysis = response.choices[0].message.content
                transcript.openai_analysis = {"comprehensive_clinical_analysis": analysis}
                transcript.processed_at = datetime.now()
                db.session.commit()
                logger.info("Processed %s", cli.name)
            except Exception as exc:
                logger.error("Error processing %s: %s", cli.name, exc)
        count = Transcript.query.filter(Transcript.openai_analysis.isnot(None)).count()
        total = Transcript.query.count()
        logger.info("Status: %s/%s transcripts analyzed", count, total)

# ---------------------- CLI ----------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Maintenance utilities")
    parser.add_argument("--fix-duplicates", action="store_true", help="Consolidate duplicate clients")
    parser.add_argument("--standardize-filenames", action="store_true", help="Fix transcript filenames")
    parser.add_argument("--fix-analysis", action="store_true", help="Generate AI analysis for missing transcripts")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.fix_duplicates:
        fix_duplicate_clients()
    if args.standardize_filenames:
        standardize_all_filenames()
    if args.fix_analysis:
        fix_transcript_analysis()
    if not any(vars(args).values()):
        parser.print_help()
