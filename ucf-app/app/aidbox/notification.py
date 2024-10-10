import logging

from aidbox_python_sdk.aidboxpy import AsyncAidboxClient
from app.config import emr as emr_config

async def send_email(
    client: AsyncAidboxClient, to, template_id, payload, attachments=None, *, save=True
):
    notification = client.resource(
        "Notification",
        provider=emr_config.EMAIL_PROVIDER,
        providerData={
            "fromApp": True,
            "type": "email",
            "to": to,
            "payload": payload,
            "template": {"resourceType": "NotificationTemplate", "id": template_id},
            "attachments": attachments or [],
        },
    )
    if save:
        await notification.save()
        await notification.execute("$send")
    return notification
