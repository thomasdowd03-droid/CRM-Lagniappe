"""Seed a fresh database with the current CRM contents.

Reads the snapshot in seed_data.py and inserts it once, on an empty database
(e.g. the first time the app boots against a new Postgres instance).
"""
from .models import Company, Contact
from .seed_data import COMPANIES, CONTACTS


def seed_demo(db) -> None:
    if db.query(Company).count() > 0:
        return

    by_key = {}
    for data in COMPANIES:
        company = Company(**data)
        db.add(company)
        by_key[data.get("external_id") or ("name:" + data["name"])] = company
    db.flush()

    for data in CONTACTS:
        fields = {k: v for k, v in data.items() if k != "company_key"}
        company = by_key.get(data.get("company_key"))
        db.add(Contact(company_id=(company.id if company else None), **fields))
    db.commit()
