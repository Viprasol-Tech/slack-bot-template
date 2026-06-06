"""Command-line interface for Slack Bot Template.

``slack-bot-template demo`` builds a small router, signs a fake ``/weather``
slash-command request, verifies the signature, and routes it — all offline with
no Slack tokens.

Part of Slack Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console

from slack_bot_template import __version__
from slack_bot_template.client import FakeClient
from slack_bot_template.events import EventKind, SlackEvent
from slack_bot_template.router import Router
from slack_bot_template.verify import sign_request, verify_signature

app = typer.Typer(add_completion=False, help="Slack Bot Template — by Viprasol Tech.")
console = Console()


def _build_router(client: FakeClient) -> Router:
    """Construct a demo router with one slash command and a default."""
    router = Router()

    @router.command("/weather")
    def weather(event: SlackEvent) -> dict[str, Any]:
        city = (event.text or "your area").strip()
        client.post_message(event.channel or "C0", f"Forecast for {city}: sunny.")
        return {"response_type": "ephemeral", "text": f"Weather requested for {city}."}

    @router.event(EventKind.APP_MENTION)
    def mention(event: SlackEvent) -> dict[str, Any]:
        return {"text": f"Hi <@{event.user}>! How can I help?"}

    @router.default
    def fallback(event: SlackEvent) -> dict[str, Any]:
        return {"text": f"Unhandled event: {event.kind.value}"}

    return router


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"slack-bot-template [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo(
    command: str = typer.Option("/weather", help="Slash command to route."),
    text: str = typer.Option("London", help="Slash-command argument text."),
) -> None:
    """Sign, verify, and route a slash command offline using the fake client."""
    signing_secret = "demo-signing-secret"  # demo only
    timestamp = "1700000000"
    body = f"command={command}&text={text}&user_id=U123&channel_id=C456&team_id=T789"

    signature = sign_request(signing_secret, timestamp, body)
    ok = verify_signature(signing_secret, timestamp, body, signature, max_skew_seconds=0)
    console.print(f"Signature:    {signature[:24]}...")
    console.print(f"Verified:     [bold green]{ok}[/]" if ok else "[red]invalid[/]")

    payload = {
        "command": command,
        "text": text,
        "user_id": "U123",
        "channel_id": "C456",
        "team_id": "T789",
    }
    client = FakeClient()
    router = _build_router(client)
    response = router.route(payload)

    console.print(f"Routed:       [bold]{command}[/]")
    console.print(f"Response:     {response}")
    posted = client.last()
    if posted is not None:
        console.print(f"Posted:       [cyan]{posted.text}[/] -> {posted.channel}")


if __name__ == "__main__":
    app()
