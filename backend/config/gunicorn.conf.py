import os
from dotenv import load_dotenv

# Determine the path to the .env file relative to this config file.
# backend/config/gunicorn.conf.py -> backend/.env
# This assumes your .env file is in the 'backend' directory.
# If your .env file is in the root directory, adjust the path:
# dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Number of worker processes
# Use WEB_CONCURRENCY from Render, or a default (e.g., 1) if not set.
workers = int(os.environ.get('WEB_CONCURRENCY', 1))

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Setting reload to True if FLASK_ENV is development for easier local dev
# In production (e.g., on Render), FLASK_ENV should be 'production'.
reload = os.environ.get('FLASK_ENV', 'production') == 'development'
