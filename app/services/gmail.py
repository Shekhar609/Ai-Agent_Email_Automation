import asyncio
import base64
from datetime import timezone
from email.mime.text import MIMEText
from email.utils import parseaddr, parsedate_to_datetime
from typing import Any

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import get_settings
from app.services.oauth import GMAIL_SCOPES


def _credentials_from_refresh(refresh_token: str) -> Credentials:
    s = get_settings()
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=s.google_client_id,
        client_secret=s.google_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=GMAIL_SCOPES,
    )
    creds.refresh(GoogleAuthRequest())
    return creds


def _service(refresh_token: str):
    return build(
        "gmail",
        "v1",
        credentials=_credentials_from_refresh(refresh_token),
        cache_discovery=False,
    )


async def list_recent_message_ids(
    refresh_token: str, *, max_results: int = 20, query: str = "in:inbox"
) -> list[str]:
    def _do() -> list[str]:
        svc = _service(refresh_token)
        resp = (
            svc.users().messages().list(userId="me", maxResults=max_results, q=query).execute()
        )
        return [m["id"] for m in resp.get("messages", [])]

    return await asyncio.to_thread(_do)


async def fetch_message(refresh_token: str, message_id: str) -> dict[str, Any]:
    def _do() -> dict[str, Any]:
        svc = _service(refresh_token)
        return svc.users().messages().get(userId="me", id=message_id, format="full").execute()

    return await asyncio.to_thread(_do)


def parse_message(raw: dict) -> dict:
    """Convert a Gmail API message dict into a flat dict matching our Email columns."""
    headers = {h["name"].lower(): h["value"] for h in raw.get("payload", {}).get("headers", [])}

    _, sender_addr = parseaddr(headers.get("from", ""))
    _, recipient_addr = parseaddr(headers.get("to", ""))

    received_at = None
    date_hdr = headers.get("date")
    if date_hdr:
        try:
            received_at = parsedate_to_datetime(date_hdr).astimezone(timezone.utc)
        except (ValueError, TypeError):
            received_at = None

    body_plain, body_html = _extract_bodies(raw.get("payload", {}))

    return {
        "message_id": raw["id"],
        "thread_id": raw.get("threadId"),
        "sender": sender_addr or headers.get("from", ""),
        "recipient": recipient_addr or headers.get("to", ""),
        "subject": headers.get("subject"),
        "body_plain": body_plain,
        "body_html": body_html,
        "received_at": received_at,
    }


def _extract_bodies(payload: dict) -> tuple[str | None, str | None]:
    plain: str | None = None
    html: str | None = None

    def _walk(part: dict) -> None:
        nonlocal plain, html
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            if mime == "text/plain" and plain is None:
                plain = decoded
            elif mime == "text/html" and html is None:
                html = decoded
        for sub in part.get("parts") or []:
            _walk(sub)

    _walk(payload)
    return plain, html


async def send_message(
    refresh_token: str,
    *,
    to: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    def _do() -> dict[str, Any]:
        svc = _service(refresh_token)
        msg = MIMEText(body, "plain", "utf-8")
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        payload: dict[str, Any] = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return svc.users().messages().send(userId="me", body=payload).execute()

    return await asyncio.to_thread(_do)
