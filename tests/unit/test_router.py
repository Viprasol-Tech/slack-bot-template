from __future__ import annotations

from typing import Any

from slack_bot_template.events import EventKind, SlackEvent
from slack_bot_template.router import Router


def _router() -> Router:
    router = Router()

    @router.command("/ping")
    def ping(event: SlackEvent) -> dict[str, Any]:
        return {"text": "pong"}

    @router.event(EventKind.MESSAGE)
    def message(event: SlackEvent) -> dict[str, Any]:
        return {"text": f"echo: {event.text}"}

    @router.default
    def default(event: SlackEvent) -> dict[str, Any]:
        return {"text": "default"}

    return router


def test_routes_slash_command() -> None:
    response = _router().route({"command": "/ping", "user_id": "U1"})
    assert response == {"text": "pong"}


def test_routes_message_event() -> None:
    response = _router().route(
        {
            "type": "event_callback",
            "event": {"type": "message", "text": "hi", "user": "U1"},
        }
    )
    assert response == {"text": "echo: hi"}


def test_unmatched_command_falls_through_to_default() -> None:
    response = _router().route({"command": "/unknown", "user_id": "U1"})
    assert response == {"text": "default"}


def test_url_verification_echoes_challenge() -> None:
    response = _router().route({"type": "url_verification", "challenge": "xyz"})
    assert response == {"challenge": "xyz"}


def test_empty_when_no_default() -> None:
    router = Router()
    assert router.route({"type": "mystery"}) == {}
