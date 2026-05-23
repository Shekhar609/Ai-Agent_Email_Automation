import base64

from app.services.gmail import parse_message


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode()


def test_parse_simple_plain_message():
    raw = {
        "id": "abc123",
        "threadId": "thread-1",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "bob@example.com"},
                {"name": "Subject", "value": "Hello"},
                {"name": "Date", "value": "Tue, 21 May 2026 10:00:00 +0000"},
            ],
            "body": {"data": _b64("Hi there")},
        },
    }
    parsed = parse_message(raw)
    assert parsed["message_id"] == "abc123"
    assert parsed["thread_id"] == "thread-1"
    assert parsed["sender"] == "alice@example.com"
    assert parsed["recipient"] == "bob@example.com"
    assert parsed["subject"] == "Hello"
    assert parsed["body_plain"] == "Hi there"
    assert parsed["body_html"] is None
    assert parsed["received_at"] is not None


def test_parse_multipart_message():
    raw = {
        "id": "m2",
        "threadId": "t2",
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "me@example.com"},
                {"name": "Subject", "value": "Multipart test"},
            ],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": _b64("plain body")}},
                {"mimeType": "text/html", "body": {"data": _b64("<p>html body</p>")}},
            ],
        },
    }
    parsed = parse_message(raw)
    assert parsed["body_plain"] == "plain body"
    assert parsed["body_html"] == "<p>html body</p>"
    assert parsed["received_at"] is None


def test_parse_nested_multipart_message():
    raw = {
        "id": "m3",
        "threadId": "t3",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "From", "value": "x@example.com"},
                {"name": "To", "value": "y@example.com"},
                {"name": "Subject", "value": "Nested"},
            ],
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": _b64("inner plain")}},
                    ],
                },
                {
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "att1"},
                },
            ],
        },
    }
    parsed = parse_message(raw)
    assert parsed["body_plain"] == "inner plain"
