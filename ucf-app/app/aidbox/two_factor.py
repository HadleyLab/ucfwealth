import logging

from aiohttp import web

from app.aidbox.notification import send_email
from app.aidbox.sdk import sdk

from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest
from aidbox_python_sdk import app_keys as ak
from aidbox_python_sdk.aidboxpy import AsyncAidboxClient, AsyncAidboxResource

@sdk.operation(["POST"], ["webhook", "two-factor-confirmation"])
async def auth_webhook_two_factor_confirmation_op(_operation: SDKOperation, request: SDKOperationRequest):
    client = request["app"][ak.client]
    user = client.resource("User", **request["resource"]["user"])
    token = request["resource"]["token"]
    await send_confirmation_token(client, user, token)
    return web.json_response({})


async def send_confirmation_token(client: AsyncAidboxClient, user: AsyncAidboxResource, token: str):
    logging.info(
        "OTP for user {email}: {token}".format(email=user["email"], token=token)
    )

    await send_email(
        client, user["email"],
        "verify-two-factor",
        "UCF MammoChat Two-Factor Authentication",
        {
            "token": token,
            "user": user.serialize()
        })
