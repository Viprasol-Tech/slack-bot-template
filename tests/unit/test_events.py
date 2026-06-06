from __future__ import annotations

from slack_bot_template.events import EventKind, parse_payload


def test_parse_slash_command() -> None:
    event = parse_payload(
        {
            "command": "/deploy",
            "text": "prod now",
            "user_id": "U1",
            "channel_id": "C1",
            "team_id": "T1",
        }
    )
    assert event.kind is EventKind.SLASH_COMMAND
    assert event.command == "/deploy"
    assert event.text == "prod now"
    assert event.user == "U1"
    assert event.channel == "C1"
    assert event.team == "T1"


def test_parse_slash_command_adds_leading_slash() -> None:
    event = parse_payload({"command": "deploy", "user_id": "U1"})
    assert event.command == "/deploy"


def test_parse_message_event() -> None:
    event = parse_payload(
        {
            "type": "event_callback",
            "team_id": "T1",
            "event": {
                "type": "message",
                "user": "U9",
                "channel": "C9",
                "text": "hello world",
            },
        }
    )
    assert event.kind is EventKind.MESSAGE
    assert event.user == "U9"
    assert event.channel == "C9"
    assert event.text == "hello world"


def test_parse_app_mention_event() -> None:
    event = parse_payload(
        {
            "type": "event_callback",
            "event": {"type": "app_mention", "user": "U2", "channel": "C2"},
        }
    )
    assert event.kind is EventKind.APP_MENTION


def test_parse_url_verification() -> None:
    event = parse_payload({"type": "url_verification", "challenge": "abc123"})
    assert event.kind is EventKind.URL_VERIFICATION
    assert event.challenge == "abc123"


def test_parse_unknown() -> None:
    assert parse_payload({"type": "mystery"}).kind is EventKind.UNKNOWN
    assert parse_payload({"type": "event_callback"}).kind is EventKind.UNKNOWN
