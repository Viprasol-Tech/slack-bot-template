"""Pluggable Slack client transport with a deterministic fake.

Handlers post follow-up messages through a :class:`Client`. The real transport
(an HTTP call to ``chat.postMessage``) is intentionally *not* bundled — wire up
your own ``requests``/``httpx`` call behind the :class:`Client` protocol. The
included :class:`FakeClient` records everything in memory so demos and tests
run with no network and no tokens.

Part of Slack Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SentMessage:
    """A single message handed to a :class:`Client`.

    Attributes:
        channel: The destination channel id.
        text: The message text.
        thread_ts: The parent message timestamp, when replying in a thread.
    """

    channel: str
    text: str
    thread_ts: str | None = None


@runtime_checkable
class Client(Protocol):
    """Minimal transport a bot uses to post messages back to Slack."""

    def post_message(self, channel: str, text: str, *, thread_ts: str | None = None) -> SentMessage:
        """Post a message to a channel.

        Args:
            channel: The destination channel id.
            text: The message text.
            thread_ts: Optional parent timestamp to reply in a thread.

        Returns:
            The :class:`SentMessage` that was delivered.
        """
        ...


@dataclass
class FakeClient:
    """In-memory :class:`Client` that records messages instead of sending them.

    Attributes:
        sent: Every :class:`SentMessage` posted, in call order.
    """

    sent: list[SentMessage] = field(default_factory=list)

    def post_message(self, channel: str, text: str, *, thread_ts: str | None = None) -> SentMessage:
        """Record a message and return it.

        Args:
            channel: The destination channel id.
            text: The message text.
            thread_ts: Optional parent timestamp to reply in a thread.

        Returns:
            The recorded :class:`SentMessage`.
        """
        message = SentMessage(channel=channel, text=text, thread_ts=thread_ts)
        self.sent.append(message)
        return message

    def last(self) -> SentMessage | None:
        """Return the most recently posted message, or ``None`` if none."""
        return self.sent[-1] if self.sent else None
