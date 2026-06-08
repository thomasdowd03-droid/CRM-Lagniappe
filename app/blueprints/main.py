"""Dashboard."""
from flask import Blueprint, render_template
from sqlalchemy import func

from ..database import SessionLocal
from ..models import Company, Contact

bp = Blueprint("main", __name__)


@bp.route("/")
def dashboard():
    db = SessionLocal()
    company_count = db.query(Company).count()
    contact_count = db.query(Contact).count()
    by_category = (
        db.query(Company.category, func.count(Company.id))
        .group_by(Company.category)
        .order_by(func.count(Company.id).desc())
        .all()
    )
    recent = db.query(Company).order_by(Company.created_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        company_count=company_count,
        contact_count=contact_count,
        by_category=by_category,
        recent=recent,
    )
