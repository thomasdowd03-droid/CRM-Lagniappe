"""Vercel serverless entrypoint.

Exposes the Flask application as a WSGI callable named `app`, which the
@vercel/python runtime serves. All routes are sent here via vercel.json.
"""
import os
import sys

# Make the project root importable so `import app` resolves from inside /api.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()
