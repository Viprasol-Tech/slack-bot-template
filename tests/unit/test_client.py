from __future__ import annotations

from slack_bot_template.client import Client, FakeClient, SentMessage


def test_fake_client_records_messages() -> None:
    client = FakeClient()
    client.post_message("C1", "hello")
    client.post_message("C2", "world", thread_ts="123.45")

    assert len(client.sent) == 2
    assert client.sent[0] == SentMessage(channel="C1", text="hello")
    assert client.last() == SentMessage(channel="C2", text="world", thread_ts="123.45")


def test_fake_client_last_is_none_when_empty() -> None:
    assert FakeClient().last() is None


def test_fake_client_satisfies_protocol() -> None:
    assert isinstance(FakeClient(), Client)
