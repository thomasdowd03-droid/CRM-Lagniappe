"""Public tracking endpoints hit by recipients' email clients and browsers.

These are intentionally outside the app's auth/UI chrome — they're called by mail
clients (the open pixel), by browsers following links (click redirect), and by
recipients unsubscribing.
"""
from datetime import datetime

from flask import Blueprint, Response, abort, redirect, render_template, request

from ..database import SessionLocal
from ..models import EmailEvent, EmailMessage, Suppression

bp = Blueprint("tracking", __name__)

# A 1x1 transparent GIF.
_PIXEL = bytes.fromhex(
    "47494638396101000100800000000000ffffff21f90401000000002c"
    "00000000010001000002024401003b"
)


@bp.route("/t/open/<token>.gif")
def track_open(token: str):
    db = SessionLocal()
    message = db.query(EmailMessage).filter_by(token=token).first()
    if message is not None:
        if message.opened_at is None:
            message.opened_at = datetime.utcnow()
        message.open_count = (message.open_count or 0) + 1
        db.add(EmailEvent(message_id=message.id, type="open",
                          user_agent=request.headers.get("User-Agent")))
        db.commit()
    return Response(_PIXEL, mimetype="image/gif", headers={"Cache-Control": "no-store"})


@bp.route("/t/click/<token>")
def track_click(token: str):
    url = request.args.get("u", "")
    if not (url.startswith("http://") or url.startswith("https://")):
        abort(400)  # only ever redirect to real web links
    db = SessionLocal()
    message = db.query(EmailMessage).filter_by(token=token).first()
    if message is not None:
        if message.first_clicked_at is None:
            message.first_clicked_at = datetime.utcnow()
        message.click_count = (message.click_count or 0) + 1
        db.add(EmailEvent(message_id=message.id, type="click", url=url[:1000],
                          user_agent=request.headers.get("User-Agent")))
        db.commit()
    return redirect(url)


@bp.route("/u/<token>")
def unsubscribe(token: str):
    db = SessionLocal()
    message = db.query(EmailMessage).filter_by(token=token).first()
    email = message.to_email if message else None
    if message is not None and email:
        if db.query(Suppression).filter_by(email=email).first() is None:
            db.add(Suppression(email=email, reason="unsubscribe"))
        db.add(EmailEvent(message_id=message.id, type="unsubscribe"))
        db.commit()
    return render_template("unsubscribed.html", email=email)
