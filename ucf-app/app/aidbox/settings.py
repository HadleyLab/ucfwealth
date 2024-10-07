from aidbox_python_sdk.settings import Required
from aidbox_python_sdk.settings import Settings as AidboxSettings

from app.config import aidbox, emr


class Settings(AidboxSettings):
    APP_ID = Required(v_type=str)
    FRONTEND_URL = Required(v_type=str)
    APP_INIT_URL = Required(v_type=str)


settings = Settings(
    APP_ID=aidbox.APP_ID,
    FRONTEND_URL=emr.FRONTEND_URL,
    APP_INIT_URL=aidbox.APP_INIT_URL,
)