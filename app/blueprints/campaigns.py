"""Email campaigns: list, compose, view stats, send."""
import re
from datetime import datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for

from .. import config
from ..database import SessionLocal
from ..email.render import new_token, render_email
from ..email.sender import get_sender
from ..models import Campaign, Contact, EmailMessage, Suppression

bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")

STARTER_BODY = """<p>Hi there,</p>
<p>I'm reaching out from Lagniappe Foods. We make value-added seafood and run
custom / private-label programs for distributors and brands across the Northeast.</p>
<p>Would you be open to a quick conversation about your seafood program?</p>
<p>Best,<br>The Lagniappe Foods team</p>
"""


def _parse_emails(raw: str) -> list:
    if not raw:
        return []
    seen, out = set(), []
    for part in re.split(r"[\s,;]+", raw.strip()):
        email = part.strip().lower()
        if email and "@" in email and email not in seen:
            seen.add(email)
            out.append(email)
    return out


@bp.route("/")
def list_campaigns():
    db = SessionLocal()
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    return render_template("campaigns/list.html", campaigns=campaigns)


@bp.route("/new", methods=["GET", "POST"])
def new_campaign():
    db = SessionLocal()
    if request.method == "POST":
        form = request.form
        emails = _parse_emails(form.get("test_recipients", ""))
        if form.get("include_contacts"):
            emails += [
                c.email.lower()
                for c in db.query(Contact).filter(Contact.email.isnot(None)).all()
                if c.email
            ]

        suppressed = {s.email for s in db.query(Suppression).all()}
        recipients, seen = [], set()
        for email in emails:
            if email not in seen and email not in suppressed:
                seen.add(email)
                recipients.append(email)

        campaign = Campaign(
            name=form.get("name", "").strip() or "Untitled campaign",
            subject=form.get("subject", "").strip(),
            from_name=form.get("from_name", "").strip() or config.FROM_NAME,
            from_email=form.get("from_email", "").strip() or config.FROM_EMAIL,
            body=form.get("body", "").strip(),
            status="draft",
        )
        db.add(campaign)
        db.flush()  # assign campaign.id
        for email in recipients:
            db.add(
                EmailMessage(
                    campaign_id=campaign.id,
                    to_email=email,
                    token=new_token(),
                    status="queued",
                )
            )
        db.commit()
        return redirect(url_for("campaigns.campaign_detail", campaign_id=campaign.id))

    return render_template(
        "campaigns/new.html",
        starter_body=STARTER_BODY,
        config=config,
        sender_mode=get_sender().name,
    )


@bp.route("/<int:campaign_id>")
def campaign_detail(campaign_id: int):
    db = SessionLocal()
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        abort(404)
    return render_template(
        "campaigns/detail.html", campaign=campaign, sender_mode=get_sender().name
    )


@bp.route("/<int:campaign_id>/send", methods=["POST"])
def send_campaign(campaign_id: int):
    db = SessionLocal()
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        abort(404)

    sender = get_sender()
    suppressed = {s.email for s in db.query(Suppression).all()}
    for message in campaign.messages:
        if message.status == "sent":
            continue
        if message.to_email in suppressed:
            message.status = "skipped"
            continue
        html = render_email(campaign.body or "", message.token)
        try:
            result = sender.send(
                message.to_email,
                campaign.subject or "",
                html,
                campaign.from_name,
                campaign.from_email,
            )
            message.status = "sent"
            message.provider_id = result.get("id")
            message.sent_at = datetime.utcnow()
        except Exception as exc:  # noqa: BLE001 - record any provider failure
            message.status = "failed"
            message.error = str(exc)[:500]

    campaign.status = "sent"
    campaign.sent_at = datetime.utcnow()
    db.commit()
    return redirect(url_for("campaigns.campaign_detail", campaign_id=campaign.id))
