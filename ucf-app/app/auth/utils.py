import sqlalchemy
from aidbox_python_sdk.aidboxpy import AsyncAidboxClient

from app.config.emr import FRONTEND_URL, EMAIL_PROVIDER
from app.fhirdate import get_now, parse_date_time


def is_set_password_token_valid(set_password_token):
    return (
        set_password_token
        and set_password_token["status"] == "active"
        and get_now() < parse_date_time(set_password_token["dateTimeExpired"])
    )


async def send_set_password_link_emails(client: AsyncAidboxClient, user, token_id):
    notification = client.resource(
        "Notification",
        **{
            "provider": EMAIL_PROVIDER,
            "providerData": {
                "to": user["email"],
                "subject": "Password reset",
                "template": {
                    "id": "reset-user-password",
                    "resourceType": "NotificationTemplate",
                },
                "payload": {
                    "user": user.serialize(),
                    # TODO: sanitize user
                    "confirm-href": f"{FRONTEND_URL}/reset-password/{token_id}",
                },
            },
        },
    )
    await notification.save()
    await notification.execute("$send")


async def remove_user_sessions(db, user_id):
    session_table = db.Session
    update_session = sqlalchemy.delete(session_table).where(
        session_table.c.resource["user"]["id"].astext.in_([user_id])
    )
    await db.alchemy(update_session)
