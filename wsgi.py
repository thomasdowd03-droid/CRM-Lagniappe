"""WSGI entrypoint for production hosts (PythonAnywhere, gunicorn, etc.).

PythonAnywhere's web-app config imports `application` from this module.
"""
from app import create_app

application = create_app()
