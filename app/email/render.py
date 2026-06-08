"""Assemble the final outgoing email: compliance footer, click tracking, open pixel.

The order matters: we rewrite links in the *body* first (so only the user's links
become click-tracked), then append the footer — whose unsubscribe link must point
straight at the unsubscribe route, not through the click tracker.
"""
import re
import secrets
from urllib.parse import urlencode

from .. import config


def new_token() -> str:
    """Unguessable per-recipient token used in tracking + unsubscribe URLs."""
    return secrets.token_urlsafe(18)


def tracking_pixel(token: str) -> str:
    url = f"{config.BASE_URL}/t/open/{token}.gif"
    return f'<img src="{url}" width="1" height="1" alt="" style="display:none">'


_LINK_RE = re.compile(r'href="(https?://[^"]+)"', re.IGNORECASE)


def rewrite_links(html: str, token: str) -> str:
    def repl(match: "re.Match[str]") -> str:
        original = match.group(1)
        wrapped = f'{config.BASE_URL}/t/click/{token}?{urlencode({"u": original})}'
        return f'href="{wrapped}"'

    return _LINK_RE.sub(repl, html)


def compliance_footer(token: str) -> str:
    unsubscribe_url = f"{config.BASE_URL}/u/{token}"
    return (
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0">'
        '<div style="font-size:12px;color:#94a3b8;line-height:1.5">'
        f"{config.COMPANY_NAME} &middot; {config.COMPANY_ADDRESS}<br>"
        f"You're receiving this because we believe {config.COMPANY_NAME} may be "
        "relevant to your business. "
        f'<a href="{unsubscribe_url}" style="color:#94a3b8">Unsubscribe</a>.'
        "</div>"
    )


def render_email(body_html: str, token: str) -> str:
    body = rewrite_links(body_html or "", token)
    return body + compliance_footer(token) + tracking_pixel(token)
