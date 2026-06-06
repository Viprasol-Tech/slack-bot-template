"""Register handlers and route parsed Slack events to them.

A :class:`Router` maps slash commands and event kinds to handler callables.
Each handler receives the typed :class:`~slack_bot_template.events.SlackEvent`
and returns a response ``dict`` — the JSON body Slack expects back from the
request (e.g. ``{"response_type": "ephemeral", "text": "..."}``).

The router is transport-agnostic: it does no I/O. Pair it with a
:class:`~slack_bot_template.client.Client` when a handler needs to post a
follow-up message.

Part of Slack Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from slack_bot_template.events import EventKind, SlackEvent, parse_payload

Handler = Callable[[SlackEvent], dict[str, Any]]
"""A handler takes a :class:`SlackEvent` and returns a Slack response dict."""


class Router:
    """Dispatches Slack events to registered handlers.

    Slash commands are matched first by their exact command string (e.g.
    ``"/deploy"``). Other events are matched by :class:`EventKind`. When no
    specific handler matches, the registered default is used.
    """

    def __init__(self) -> None:
        self._commands: dict[str, Handler] = {}
        self._events: dict[EventKind, Handler] = {}
        self._default: Handler | None = None

    def command(self, name: str) -> Callable[[Handler], Handler]:
        """Register a handler for a slash command.

        Args:
            name: The slash command, with or without a leading ``/``
                (``"deploy"`` and ``"/deploy"`` are equivalent).

        Returns:
            A decorator that registers and returns the handler unchanged.
        """
        key = name if name.startswith("/") else f"/{name}"

        def decorator(handler: Handler) -> Handler:
            self._commands[key] = handler
            return handler

        return decorator

    def event(self, kind: EventKind) -> Callable[[Handler], Handler]:
        """Register a handler for a non-slash :class:`EventKind`.

        Args:
            kind: The event kind to handle (e.g. :attr:`EventKind.MESSAGE`).

        Returns:
            A decorator that registers and returns the handler unchanged.
        """

        def decorator(handler: Handler) -> Handler:
            self._events[kind] = handler
            return handler

        return decorator

    def default(self, handler: Handler) -> Handler:
        """Register the fallback handler used when nothing else matches.

        Args:
            handler: The handler to invoke for unmatched events.

        Returns:
            The handler, unchanged, so this can be used as a decorator.
        """
        self._default = handler
        return handler

    def route(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Parse a raw payload and dispatch it to the matching handler.

        Args:
            payload: A raw slash-command form dict or Events API JSON dict.

        Returns:
            The response dict from the selected handler. For the Events API URL
            verification handshake, the ``challenge`` is echoed automatically.
            If nothing matches and no default is registered, an empty dict is
            returned (Slack treats this as an acknowledged no-op).
        """
        return self.dispatch(parse_payload(payload))

    def dispatch(self, event: SlackEvent) -> dict[str, Any]:
        """Dispatch an already-parsed :class:`SlackEvent`.

        Args:
            event: The normalised event to route.

        Returns:
            The handler's response dict, an automatic challenge echo for URL
            verification, or the default handler's output.
        """
        if event.kind is EventKind.URL_VERIFICATION:
            return {"challenge": event.challenge or ""}

        if event.kind is EventKind.SLASH_COMMAND and event.command is not None:
            handler = self._commands.get(event.command)
            if handler is not None:
                return handler(event)

        event_handler = self._events.get(event.kind)
        if event_handler is not None:
            return event_handler(event)

        if self._default is not None:
            return self._default(event)
        return {}
