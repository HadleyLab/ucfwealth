from aidbox_python_sdk.sdk import SDK
from app.aidbox.migrations import load_sql_migrations

from .settings import settings

sdk = SDK(settings, migrations=load_sql_migrations())
