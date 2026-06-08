"""Company list, detail, manual entry, editing, and deletion."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..database import SessionLocal
from ..models import Company

bp = Blueprint("companies", __name__, url_prefix="/companies")


@bp.route("/")
def list_companies():
    db = SessionLocal()
    companies = db.query(Company).order_by(Company.name).all()
    return render_template("companies/list.html", companies=companies)


@bp.route("/new", methods=["GET", "POST"])
def new_company():
    db = SessionLocal()
    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()
        if not name:
            flash("Company name is required.", "error")
            return render_template("companies/new.html", form=form)
        website = form.get("website", "").strip() or None
        company = Company(
            name=name,
            website=website,
            domain=website,
            category=form.get("category", "").strip() or None,
            city=form.get("city", "").strip() or None,
            region=form.get("region", "").strip() or None,
            country=form.get("country", "").strip() or None,
            status=form.get("status", "").strip() or "lead",
            description=form.get("description", "").strip() or None,
            source="manual",
        )
        db.add(company)
        db.commit()
        flash(f"Added {company.name}.", "success")
        return redirect(url_for("companies.company_detail", company_id=company.id))
    return render_template("companies/new.html", form={})


@bp.route("/<int:company_id>")
def company_detail(company_id: int):
    db = SessionLocal()
    company = db.get(Company, company_id)
    if company is None:
        abort(404)
    return render_template("companies/detail.html", company=company)


@bp.route("/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id: int):
    db = SessionLocal()
    company = db.get(Company, company_id)
    if company is None:
        abort(404)
    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()
        if not name:
            flash("Company name is required.", "error")
            return render_template("companies/edit.html", company=company)
        website = form.get("website", "").strip() or None
        company.name = name
        company.website = website
        company.domain = website
        company.category = form.get("category", "").strip() or None
        company.city = form.get("city", "").strip() or None
        company.region = form.get("region", "").strip() or None
        company.status = form.get("status", "").strip() or "lead"
        company.description = form.get("description", "").strip() or None
        db.commit()
        flash(f"Updated {company.name}.", "success")
        return redirect(url_for("companies.company_detail", company_id=company.id))
    return render_template("companies/edit.html", company=company)


@bp.route("/<int:company_id>/delete", methods=["POST"])
def delete_company(company_id: int):
    db = SessionLocal()
    company = db.get(Company, company_id)
    if company is None:
        abort(404)
    name = company.name
    db.delete(company)  # cascade also removes its contacts
    db.commit()
    flash(f"Deleted {name} and its contacts.", "success")
    return redirect(url_for("companies.list_companies"))
