from datetime import timedelta

from aiohttp import web
from fhirpy.base.exceptions import OperationOutcome

from app.auth.utils import (
    is_set_password_token_valid,
    remove_user_sessions,
    send_set_password_link_emails,
)
from app.fhirdate import format_fhir_date_time, get_now
from app.aidbox.sdk import sdk

@sdk.operation(
    ["POST"],
    ["fhir", "User", "$auth", "$send-setup-password-link"],
    public=True,
    request_schema={
        "required": ["resource"],
        "properties": {
            "resource": {
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            }
        },
    },
)
@sdk.operation(
    ["POST"],
    ["User", "$auth", "$send-setup-password-link"],
    public=True,
    request_schema={
        "required": ["resource"],
        "properties": {
            "resource": {
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            }
        },
    },
)
async def auth_send_setup_password_link_op(_operation, request):
    client = request["app"]["client"]
    days_for_expiration = 1
    email = request["resource"]["email"]

    user = await client.resources("User").search(email=email).first()
    if not user:
        raise OperationOutcome(reason=f"User with mail {email} does not exist")

    prev_set_password_token = await client.resources("SetPasswordToken").search(user=user).first()
    if prev_set_password_token:
        await prev_set_password_token.patch(**{"status": "expired"})

    set_password_token = client.resource(
        "SetPasswordToken",
        **{
            "user": user.to_reference(),
            "status": "active",
            "dateTimeExpired": format_fhir_date_time(
                get_now() + timedelta(seconds=days_for_expiration * 60 * 60 * 24)
            ),
        },
    )
    await set_password_token.save()

    await send_set_password_link_emails(client, user, set_password_token.id)

    return web.json_response({"message": "Email sent successfully"})


@sdk.operation(
    ["POST"],
    ["fhir", "User", "$auth", "$set-password"],
    request_schema={
        "required": ["resource"],
        "properties": {
            "resource": {
                "properties": {
                    "password": {"type": "string"},
                    "setPasswordTokenId": {"type": "string"},
                },
                "required": ["password", "setPasswordTokenId"],
            }
        },
    },
    public=True,
)
@sdk.operation(
    ["POST"],
    ["User", "$auth", "$set-password"],
    request_schema={
        "required": ["resource"],
        "properties": {
            "resource": {
                "properties": {
                    "password": {"type": "string"},
                    "setPasswordTokenId": {"type": "string"},
                },
                "required": ["password", "setPasswordTokenId"],
            }
        },
    },
    public=True,
)
async def set_password_op(operation, request):
    db = request["app"]["db"]
    client = request["app"]["client"]
    password = request["resource"]["password"]
    set_password_token_id = request["resource"]["setPasswordTokenId"]
    set_password_token = (
        await client.resources("SetPasswordToken").search(_id=set_password_token_id).first()
    )
    if not is_set_password_token_valid(set_password_token):
        raise OperationOutcome(reason="Invalid request")
    user = await set_password_token["user"].to_resource()

    await user.patch(**{"password": password})
    await set_password_token.patch(**{"status": "used"})
    await remove_user_sessions(db, user.id)

    return web.json_response({"message": "The password was successfully changed"})