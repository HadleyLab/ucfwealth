import uuid

from app.aidbox.sdk import sdk
from app.config.emr import FRONTEND_URL
from app.aidbox.notification import notification_sub

@sdk.subscription("User")
async def user_created(event, request):
    aidbox = request.app["client"]
    if event["action"] == "create":
        user = aidbox.resource("User", **event["resource"])
        if user["data"].get("resetPassword", False):
            reset_token = uuid.uuid4()
            user["data"]["reset_token"] = str(reset_token)
            await user.save()
            notification = aidbox.resource(
                "Notification",
                **{
                    "provider": "smtp-provider",
                    "providerData": {
                        "to": user["email"],
                        "subject": "Password reset",
                        "template": {
                            "id": "reset-user-password",
                            "resourceType": "NotificationTemplate",
                        },
                        "payload": {
                            "user": user.serialize(),
                            "confirm-href": f"{FRONTEND_URL}/reset-password/{reset_token}",
                        },
                    },
                },
            )
            await notification.save()


@sdk.subscription("Notification")
async def notification_handler(event, request):
    aidbox = request.app["client"]
    notification = aidbox.resource("Notification", **event["resource"])

    await notification_sub(request.app, event["action"], notification, None)