# AGENTS Guidelines

This repository implements a Flask application for processing therapy transcripts. When updating or extending the code base, follow these conventions so that future automation agents can work consistently.

## API Design
- Organize routes using Flask Blueprints. Avoid putting new endpoints in `routes.py`; create or extend blueprint modules under `blueprints/` instead.
- Follow REST naming conventions for endpoints (e.g., `POST /api/clients` rather than `/api/create-client`).
- Validate request bodies with Pydantic models where possible. Return structured JSON errors using `make_error_response`.
- Protect API endpoints with the `require_api_key` decorator. New endpoints should respect this authentication mechanism unless noted otherwise.

## Documentation
- Update `README.md` when adding or changing endpoints. Document request/response formats and any new environment variables.

## Testing
- All new code should include unit tests. Use Flask's test client for API routes.
- Run `pytest -q` before committing to ensure the suite passes.
- Tests assume the following environment variables:
  - `DATABASE_URL=sqlite:///:memory:`
  - `API_KEY=testkey`

Following these guidelines will keep the project maintainable and make it easier for automated tools to contribute effectively.
