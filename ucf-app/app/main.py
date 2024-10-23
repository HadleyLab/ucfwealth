from aidbox_python_sdk.main import create_app
from aiohttp import web
import app.aidbox
import app.auth

from app.aidbox.sdk import sdk

import logging




logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def application() -> web.Application:
    app = create_app(sdk)
    return app