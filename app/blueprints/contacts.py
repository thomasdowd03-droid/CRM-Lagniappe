"""Contact list, manual entry, editing, deletion, and CSV import."""
import csv
import io

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..database import SessionLocal
from ..models import Company, Contact

bp = Blueprint("contacts", __name__, url_prefix="/contacts")

# Map our fields to the header names a spreadsheet might use (case-insensitive).
HEADER_ALIASES = {
    "email": {"email", "e-mail", "email address", "emailaddress", "work email"},
    "first_name": {"first name", "first", "firstname", "given name"},
    "last_name": {"last name", "last", "lastname", "surname", "family name"},
    "full_name": {"name", "full name", "contact name", "contact", "customer name", "customer"},
    "company": {"company", "company name", "business", "account", "organization", "org"},
    "title": {"title", "job title", "position", "role"},
    "phone": {"phone", "telephone", "phone number", "mobile", "work phone", "phone 1", "main phone"},
}


def _norm(value):
    return (value or "").strip().lower()


def _build_header_map(fieldnames):
    mapping = {}
    for column in fieldnames or []:
        key = _norm(column)
        for target, aliases in HEADER_ALIASES.items():
            if key in aliases and target not in mapping:
                mapping[target] = column
    return mapping


@bp.route("/")
def list_contacts():
    db = SessionLocal()
    contacts = db.query(Contact).order_by(Contact.last_name).all()
    return render_template("contacts/list.html", contacts=contacts)


@bp.route("/new", methods=["GET", "POST"])
def new_contact():
    db = SessionLocal()
    companies = db.query(Company).order_by(Company.name).all()
    if request.method == "POST":
        form = request.form
        first = form.get("first_name", "").strip()
        last = form.get("last_name", "").strip()
        email = form.get("email", "").strip().lower() or None
        if not (first or last or email):
            flash("Enter at least a name or an email.", "error")
            return render_template("contacts/new.html", companies=companies, form=form, preselect=None)
        company_id = form.get("company_id") or None
        contact = Contact(
            first_name=first or None,
            last_name=last or None,
            full_name=("%s %s" % (first, last)).strip() or None,
            title=form.get("title", "").strip() or None,
            email=email,
            phone=form.get("phone", "").strip() or None,
            linkedin=form.get("linkedin", "").strip() or None,
            status=form.get("status", "").strip() or "lead",
            company_id=int(company_id) if company_id else None,
            source="manual",
        )
        db.add(contact)
        db.commit()
        flash("Contact added.", "success")
        if contact.company_id:
            return redirect(url_for("companies.company_detail", company_id=contact.company_id))
        return redirect(url_for("contacts.list_contacts"))
    preselect = request.args.get("company_id", type=int)
    return render_template("contacts/new.html", companies=companies, form={}, preselect=preselect)


@bp.route("/import", methods=["GET", "POST"])
def import_contacts():
    db = SessionLocal()
    if request.method == "POST":
        upload = request.files.get("file")
        if not upload or not upload.filename:
            flash("Choose a CSV file to import.", "error")
            return render_template("contacts/import.html")

        raw = upload.stream.read()
        text = None
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            flash("Couldn't read that file — please upload a plain CSV.", "error")
            return render_template("contacts/import.html")

        reader = csv.DictReader(io.StringIO(text))
        header_map = _build_header_map(reader.fieldnames)
        if not header_map:
            flash("Couldn't recognize the columns. Include headers like Name (or First/Last), Company, and Email.", "error")
            return render_template("contacts/import.html")

        existing_emails = {
            row[0].lower() for row in db.query(Contact.email).filter(Contact.email.isnot(None)).all()
        }
        companies_by_name = {_norm(c.name): c for c in db.query(Company).all()}

        imported = skipped = 0
        for row in reader:
            def value(target):
                column = header_map.get(target)
                return (row.get(column, "") or "").strip() if column else ""

            email = value("email").lower() or None
            first = value("first_name")
            last = value("last_name")
            full = value("full_name")
            if not first and not last and full:
                parts = full.split()
                first = parts[0]
                last = " ".join(parts[1:])

            display = ("%s %s" % (first, last)).strip() or full or email
            if not display:
                continue  # skip blank rows
            if email and email in existing_emails:
                skipped += 1
                continue

            company_name = value("company")
            company = None
            if company_name:
                company = companies_by_name.get(_norm(company_name))
                if company is None:
                    company = Company(name=company_name, source="import", status="lead")
                    db.add(company)
                    db.flush()
                    companies_by_name[_norm(company_name)] = company

            db.add(Contact(
                first_name=first or None,
                last_name=last or None,
                full_name=("%s %s" % (first, last)).strip() or full or None,
                title=value("title") or None,
                email=email,
                phone=value("phone") or None,
                status="lead",
                source="import",
                company_id=(company.id if company else None),
            ))
            if email:
                existing_emails.add(email)
            imported += 1

        db.commit()
        msg = "Imported %d contact(s)" % imported
        if skipped:
            msg += ", skipped %d duplicate(s)" % skipped
        flash(msg + ".", "success")
        return redirect(url_for("contacts.list_contacts"))

    return render_template("contacts/import.html")


@bp.route("/<int:contact_id>/edit", methods=["GET", "POST"])
def edit_contact(contact_id: int):
    db = SessionLocal()
    contact = db.get(Contact, contact_id)
    if contact is None:
        abort(404)
    companies = db.query(Company).order_by(Company.name).all()
    if request.method == "POST":
        form = request.form
        first = form.get("first_name", "").strip()
        last = form.get("last_name", "").strip()
        email = form.get("email", "").strip().lower() or None
        if not (first or last or email):
            flash("Enter at least a name or an email.", "error")
            return render_template("contacts/edit.html", contact=contact, companies=companies)
        contact.first_name = first or None
        contact.last_name = last or None
        contact.full_name = ("%s %s" % (first, last)).strip() or None
        contact.title = form.get("title", "").strip() or None
        contact.email = email
        contact.phone = form.get("phone", "").strip() or None
        contact.linkedin = form.get("linkedin", "").strip() or None
        contact.status = form.get("status", "").strip() or "lead"
        company_id = form.get("company_id") or None
        contact.company_id = int(company_id) if company_id else None
        db.commit()
        flash("Contact updated.", "success")
        if contact.company_id:
            return redirect(url_for("companies.company_detail", company_id=contact.company_id))
        return redirect(url_for("contacts.list_contacts"))
    return render_template("contacts/edit.html", contact=contact, companies=companies)


@bp.route("/<int:contact_id>/delete", methods=["POST"])
def delete_contact(contact_id: int):
    db = SessionLocal()
    contact = db.get(Contact, contact_id)
    if contact is None:
        abort(404)
    name = contact.display_name
    db.delete(contact)
    db.commit()
    flash(f"Deleted {name}.", "success")
    return redirect(url_for("contacts.list_contacts"))
