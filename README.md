# Therapy Transcript Pipeline

This project processes therapy session transcripts using multiple AI services. It integrates Dropbox for file intake, extracts content from uploaded documents, generates analyses with OpenAI, Anthropic, and Google Gemini, and stores results in Notion.

## Setup
1. Install dependencies:
   ```bash
   pip install -e .
   ```
2. Create a `.env` file or set the following environment variables:
   - `DROPBOX_ACCESS_TOKEN`
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `GEMINI_API_KEY`
   - `NOTION_API_KEY`
   - `NOTION_PARENT_ID`
   - Database settings for Flask SQLAlchemy

## Running
Several scripts are provided for batch processing and maintenance tasks. The main Flask app can be started with:

```bash
python app.py
```

Background utilities are consolidated under `maintenance.py` and can be invoked as CLI commands. For example:

```bash
python maintenance.py --fix-duplicates
python maintenance.py --standardize-filenames
```

## Testing
After installing dependencies, run the test suite with:

```bash
pytest -q
```

Tests mock external services and do not require real API credentials.
