"""Application factory for Lagniappe CRM."""
from flask import Flask, redirect, request, session, url_for

from . import config
from .database import SessionLocal, init_db
from .seed import seed_demo

# Reachable without logging in: the login page, the public email-tracking routes
# (hit by recipients' mail clients / browsers), and static files.
PUBLIC_ENDPOINTS = {
    "auth.login",
    "tracking.track_open",
    "tracking.track_click",
    "tracking.unsubscribe",
    "static",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    init_db()

    # Seed demo prospects on first run.
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        SessionLocal.remove()

    from .blueprints.auth import bp as auth_bp
    from .blueprints.campaigns import bp as campaigns_bp
    from .blueprints.companies import bp as companies_bp
    from .blueprints.contacts import bp as contacts_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.tracking import bp as tracking_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(tracking_bp)

    @app.before_request
    def require_login():
        # Auth is enforced only when a team password is configured.
        if not config.APP_PASSWORD:
            return None
        if session.get("authed"):
            return None
        if request.endpoint in PUBLIC_ENDPOINTS:
            return None
        return redirect(url_for("auth.login", next=request.path))

    @app.teardown_appcontext
    def remove_session(exception=None):  # noqa: ANN001
        SessionLocal.remove()

    return app
