"""Shared-password login.

Enforced only when APP_PASSWORD is set (see create_app's before_request guard),
so local development needs no login while a deployed instance does.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .. import config

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if config.APP_PASSWORD and request.form.get("password", "") == config.APP_PASSWORD:
            session["authed"] = True
            nxt = request.args.get("next", "")
            if not nxt.startswith("/"):  # only allow internal redirects
                nxt = url_for("main.dashboard")
            return redirect(nxt)
        flash("Incorrect password.", "error")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
