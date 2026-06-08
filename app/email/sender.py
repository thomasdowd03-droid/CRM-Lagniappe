"""The swappable email-sending seam.

`get_sender()` returns a live Resend sender when an API key is configured, and a
no-delivery Outbox sender otherwise. Adding another provider later (Postmark, SES)
means writing one more class here — nothing else in the app changes.
"""
import json
import urllib.request

from .. import config


class BaseSender:
    name = "base"

    def send(self, to_email, subject, html, from_name, from_email) -> dict:
        raise NotImplementedError


class OutboxSender(BaseSender):
    """Default for local/test: records the send without delivering it."""

    name = "outbox"

    def send(self, to_email, subject, html, from_name, from_email) -> dict:
        print(f"[outbox] (not delivered) to={to_email} subject={subject!r}")
        return {"ok": True, "provider": "outbox", "id": None}


class ResendSender(BaseSender):
    """Real delivery via Resend (https://resend.com)."""

    name = "resend"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def send(self, to_email, subject, html, from_name, from_email) -> dict:
        payload = json.dumps(
            {
                "from": f"{from_name} <{from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        ).encode()
        request = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        return {"ok": True, "provider": "resend", "id": data.get("id")}


def get_sender() -> BaseSender:
    if config.RESEND_API_KEY:
        return ResendSender(config.RESEND_API_KEY)
    return OutboxSender()
