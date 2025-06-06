import os
import logging
from functools import wraps
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app import db
from models import Client, ProcessingLog
from services.notion_service import NotionService

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")

notion_service = NotionService()


def make_success_response(data=None, message=None, status_code=200):
    response_dict = {"success": True}
    if data is not None:
        response_dict["data"] = data
    if message is not None:
        response_dict["message"] = message
    return jsonify(response_dict), status_code


def make_error_response(message, error_code=None, details=None, status_code=400):
    error_payload = {"message": message}
    if error_code is not None:
        error_payload["code"] = error_code
    if details is not None:
        error_payload["details"] = details
    response_dict = {"success": False, "error": error_payload}
    return jsonify(response_dict), status_code


def require_api_key(func):
    """Simple API key authentication decorator."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        expected = os.environ.get("API_KEY")
        provided = request.headers.get("X-API-KEY")
        if expected and expected != provided:
            return make_error_response(
                "Invalid API key", error_code="UNAUTHORIZED", status_code=401
            )
        return func(*args, **kwargs)

    return wrapper


class CreateClientRequest(BaseModel):
    name: str


@api_bp.post("/clients")
@require_api_key
def create_client():
    """Create a new client."""
    try:
        data = request.get_json() or {}
        model = CreateClientRequest(**data)
        client_name = model.name.strip()

        existing_client = db.session.query(Client).filter(
            Client.name.ilike(client_name)
        ).first()
        if existing_client:
            return make_error_response(
                "Client with this name already exists.",
                error_code="DUPLICATE_RESOURCE",
                status_code=409,
            )

        client = Client(name=client_name)
        db.session.add(client)
        db.session.flush()
        notion_db_id = None
        if notion_service:
            try:
                notion_db_id = notion_service.create_client_database(client_name)
                if notion_db_id:
                    client.notion_database_id = notion_db_id
            except Exception as e:  # pragma: no cover - network
                logger.warning(
                    f"Failed to create Notion database for {client_name}: {str(e)}"
                )
        db.session.commit()
        return make_success_response(
            message=f"Client {client_name} created successfully",
            data={"client_id": client.id, "notion_database_id": notion_db_id},
            status_code=201,
        )
    except ValidationError as ve:
        return make_error_response(
            "Invalid request",
            error_code="VALIDATION_ERROR",
            details=ve.errors(),
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        db.session.rollback()
        return make_error_response(
            str(e), error_code="INTERNAL_SERVER_ERROR", status_code=500
        )


@api_bp.get("/processing-logs")
@require_api_key
def get_processing_logs():
    """Return recent processing logs."""
    try:
        logs = (
            db.session.query(ProcessingLog)
            .order_by(ProcessingLog.created_at.desc())
            .limit(50)
            .all()
        )
        log_data = [
            {
                "id": log.id,
                "activity_type": log.activity_type or "unknown",
                "status": log.status or "info",
                "message": log.message or "No message",
                "created_at": log.created_at.isoformat()
                if log.created_at
                else datetime.now(timezone.utc).isoformat(),
                "transcript_id": log.transcript_id,
            }
            for log in logs
        ]
        return make_success_response(data=log_data)
    except Exception as e:
        logger.error(f"Critical error getting processing logs: {str(e)}")
        return make_error_response(
            "Critical error getting processing logs.",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500,
        )

