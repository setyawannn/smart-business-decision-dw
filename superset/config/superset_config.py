import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

WTF_CSRF_ENABLED = True

SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

TALISMAN_ENABLED = False