"""Slack Bot Template — transport-agnostic Slack bot framework.

Part of Slack Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from slack_bot_template.client import Client, FakeClient, SentMessage
from slack_bot_template.events import (
    EventKind,
    SlackEvent,
    parse_payload,
)
from slack_bot_template.router import Router
from slack_bot_template.verify import sign_request, verify_signature

__version__ = "0.1.0"

__all__ = [
    "Client",
    "EventKind",
    "FakeClient",
    "Router",
    "SentMessage",
    "SlackEvent",
    "__version__",
    "parse_payload",
    "sign_request",
    "verify_signature",
]
