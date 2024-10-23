import uuid

from app.aidbox.sdk import sdk
from app.config.emr import FRONTEND_URL, EMAIL_PROVIDER

from datetime import timedelta

from app.fhirdate import format_fhir_date_time, get_now


@sdk.subscription("User")
async def user_created(event, request):
    client = request.app["client"]
    if event["action"] == "create":
        user = client.resource("User", **event["resource"])
        if user["data"].get("resetPassword", False):
            days_for_expiration = 1
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
            notification = client.resource(
                "Notification",
                **{
                    "provider": EMAIL_PROVIDER,
                    "providerData": {
                        "to": user["email"],
                        "subject": "Welcome to UCF Mammogram Research Study!",
                        "template": {
                            "id": "new-user",
                            "resourceType": "NotificationTemplate",
                        },
                        "payload": {
                            "user": user.serialize(),
                            # TODO: sanitize user
                            "confirm-href": f"{FRONTEND_URL}/reset-password/{set_password_token.id}",
                        },
                    },
                },
            )
            await notification.save()
            await notification.execute("$send")
