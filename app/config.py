"""Runtime configuration, read from environment (with safe local defaults).

Everything here can be overridden via a `.env` file (see .env.example). The app
runs fine with no .env at all — defaults put it in local test mode.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root, regardless of the current working directory,
# so it behaves the same locally and on a host.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Public URL where this app is reachable by recipients' email clients. Real-world
# open/click tracking only works when this is publicly reachable (localhost is
# fine for local tests).
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5050").rstrip("/")

# Sender identity shown on outgoing email.
FROM_NAME = os.environ.get("FROM_NAME", "Lagniappe Foods")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "hello@lagniappefoods.com")

# CAN-SPAM: a real physical mailing address is required in every email footer.
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Lagniappe Foods")
COMPANY_ADDRESS = os.environ.get("COMPANY_ADDRESS", "546 Mitchell St, Orange, NJ 07050")

# Email provider. Blank => test mode (records sends without delivering them).
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# Web app session secret + shared team password.
# Login is enforced ONLY when APP_PASSWORD is set, so local dev needs no login.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
