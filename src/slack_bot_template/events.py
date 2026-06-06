"""Parse raw Slack payloads into typed events.

Slack delivers two broad shapes to a bot endpoint:

* **Slash commands** — ``application/x-www-form-urlencoded`` form fields such as
  ``command``, ``text``, ``user_id`` and ``channel_id``.
* **Events API** — a JSON envelope with a nested ``event`` object describing a
  message, app mention, reaction, etc.

:func:`parse_payload` normalises both into a single :class:`SlackEvent` so the
router never has to care which wire format was used.

Part of Slack Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventKind(str, Enum):
    """The category of an incoming Slack interaction."""

    SLASH_COMMAND = "slash_command"
    MESSAGE = "message"
    APP_MENTION = "app_mention"
    URL_VERIFICATION = "url_verification"
    UNKNOWN = "unknown"


class SlackEvent(BaseModel):
    """A normalised Slack interaction.

    Attributes:
        kind: Which :class:`EventKind` this payload represents.
        user: The Slack user id that triggered the event, if any.
        channel: The channel id the event occurred in, if any.
        text: Free-form message text (for messages) or the slash-command
            argument string (for slash commands).
        command: The slash command including its leading ``/`` (slash commands
            only), e.g. ``"/deploy"``.
        team: The Slack workspace (team) id, if present.
        challenge: The challenge token for Events API URL verification.
        raw: The original payload, preserved for handlers needing extra fields.
    """

    model_config = ConfigDict(frozen=True)

    kind: EventKind
    user: str | None = None
    channel: str | None = None
    text: str | None = None
    command: str | None = None
    team: str | None = None
    challenge: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


def parse_payload(payload: dict[str, Any]) -> SlackEvent:
    """Normalise a raw Slack payload into a :class:`SlackEvent`.

    The wire format is inferred from the payload's shape:

    * A ``command`` key indicates a slash command (form-encoded).
    * A ``type`` of ``"url_verification"`` indicates the Events API handshake.
    * An ``event`` envelope indicates an Events API callback; its inner
      ``type`` selects :class:`EventKind`.

    Args:
        payload: A decoded slash-command form dict or Events API JSON dict.

    Returns:
        The corresponding :class:`SlackEvent`. Unrecognised payloads yield an
        event with :attr:`EventKind.UNKNOWN` rather than raising.
    """
    if "command" in payload:
        return _parse_slash_command(payload)

    envelope_type = payload.get("type")
    if envelope_type == "url_verification":
        return SlackEvent(
            kind=EventKind.URL_VERIFICATION,
            challenge=_as_str(payload.get("challenge")),
            raw=payload,
        )
    if envelope_type == "event_callback":
        return _parse_event_callback(payload)

    return SlackEvent(kind=EventKind.UNKNOWN, raw=payload)


def _parse_slash_command(payload: dict[str, Any]) -> SlackEvent:
    """Build a slash-command event from a form-encoded payload."""
    return SlackEvent(
        kind=EventKind.SLASH_COMMAND,
        user=_as_str(payload.get("user_id")),
        channel=_as_str(payload.get("channel_id")),
        text=_as_str(payload.get("text")),
        command=_normalise_command(_as_str(payload.get("command"))),
        team=_as_str(payload.get("team_id")),
        raw=payload,
    )


def _parse_event_callback(payload: dict[str, Any]) -> SlackEvent:
    """Build a message/app-mention event from an Events API envelope."""
    inner = payload.get("event")
    if not isinstance(inner, dict):
        return SlackEvent(kind=EventKind.UNKNOWN, raw=payload)

    inner_type = inner.get("type")
    kind = {
        "message": EventKind.MESSAGE,
        "app_mention": EventKind.APP_MENTION,
    }.get(str(inner_type), EventKind.UNKNOWN)

    return SlackEvent(
        kind=kind,
        user=_as_str(inner.get("user")),
        channel=_as_str(inner.get("channel")),
        text=_as_str(inner.get("text")),
        team=_as_str(payload.get("team_id")),
        raw=payload,
    )


def _normalise_command(command: str | None) -> str | None:
    """Ensure a slash command carries exactly one leading ``/``."""
    if command is None:
        return None
    command = command.strip()
    if not command:
        return None
    return command if command.startswith("/") else f"/{command}"


def _as_str(value: Any) -> str | None:
    """Coerce a payload field to ``str`` while preserving ``None``."""
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)
