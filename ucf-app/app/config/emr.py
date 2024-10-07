from os import environ

FRONTEND_URL = environ.get("FRONTEND_URL", "http://localhost:3000")
EMAIL_PROVIDER = "console"