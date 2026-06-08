# Lagniappe CRM

A lightweight CRM for **Lagniappe Foods** (Orange, NJ) — a value-added seafood brand.
It manages contacts and companies, runs tracked email blasts, and helps find new
prospects (distributors, retailers, and private-label / co-packing clients).

## Stack

- **Python + Flask** — a server-rendered web app that runs locally with no Node/build step.
- **SQLAlchemy + SQLite** for data (swappable to Postgres when we host it).
- **Tailwind (CDN)** for styling.
- External services sit behind clean, swappable seams (the hybrid approach): an email
  provider for blasts + open/click tracking, and a B2B data source for prospecting.

## Roadmap

1. Companies & contacts (the CRM core) ← in progress
2. Prospect import from the B2B data tool
3. Email blasts + open/click tracking (with unsubscribe & compliance)
4. Pipeline, notes & activity history
5. Login + hosting

## Setup

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

_(Run instructions are finalized once the app entrypoint lands.)_
