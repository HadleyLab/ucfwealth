import logging

from aidbox_python_sdk.aidboxpy import AsyncAidboxClient
from jinja2 import Environment, Undefined
from jinja2.ext import Extension
from premailer import transform

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
    return notification


class SilentUndefined(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):  # type: ignore
        return None


class RenderBlocksExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.extend(render_blocks=[])

    def filter_stream(self, stream):
        block_level = 0
        skip_level = 0
        in_endblock = False

        for token in stream:
            if token.type == "block_begin":
                if stream.current.value == "block":
                    block_level += 1
                    if stream.look().value not in self.environment.render_blocks:  # type: ignore
                        skip_level = block_level

            if token.value == "endblock":
                in_endblock = True

            if skip_level == 0:
                yield token

            if token.type == "block_end":
                if in_endblock:
                    in_endblock = False
                    block_level -= 1

                    if skip_level == block_level + 1:
                        skip_level = 0


jinja_env = Environment(undefined=SilentUndefined)

jinja_subject_env = Environment(undefined=SilentUndefined, extensions=[RenderBlocksExtension])
jinja_subject_env.render_blocks = ["subject"]  # type: ignore

jinja_body_env = Environment(undefined=SilentUndefined, extensions=[RenderBlocksExtension])
jinja_body_env.render_blocks = ["body"]  # type: ignore


class SendNotificationExceptionError(Exception):
    pass


async def send_console(to, subject, body, attachments=None):
    logging.info(
        "New notification:\nTo: %s\nSubject: %s\n%s\nattachments: %s",
        to,
        subject,
        body,
        attachments or [],
    )


providers = {
    "console": send_console,
}


async def notification_sub(app, action, resource, _previous_resource):
    sdk_settings = app["settings"]
    client = app["client"]
    if action == "create":
        provider_data = resource["providerData"]

        # Skip processing for non-app notifications
        if not provider_data.get("fromApp"):
            return

        notification_type = provider_data.get("type")
        if notification_type == "email":
            payload = {
                **provider_data.get("payload", {}),
                "frontend_url": sdk_settings.FRONTEND_URL,
                # "backend_url": sdk_settings.backend_public_url,
                # "current_date": format_fhir_date(get_now()),
            }

            template = await provider_data["template"].to_resource()
            subject_template = jinja_subject_env.from_string(template["subject"])
            body_template = jinja_body_env.from_string(template["template"])
            subject = subject_template.render(payload)
            body = body_template.render(payload)
            layout = await client.resources("NotificationTemplate").get(id="email-layout")
            body = transform(
                jinja_env.from_string(layout["template"]).render({"body": body, **payload})
            )
            props = {
                "subject": subject.strip(),
                "body": body.strip(),
                "to": provider_data["to"],
            }
            if "attachments" in provider_data:
                props["attachments"] = provider_data["attachments"]
        elif notification_type == "sms":
            props = {
                "to": provider_data["to"],
                "body": provider_data["body"].strip(),
            }
        else:
            raise Exception("Notification type `%s` is not supported", notification_type)

        provider = resource["provider"]

        send_fn = providers.get(provider)
        if not send_fn:
            logging.warning("Unhandled notification for provider %s", provider)
            return

        try:
            await send_fn(**props)  # type: ignore

            resource["status"] = "delivered"
            await resource.save()
        except SendNotificationExceptionError as exc:
            logging.debug(exc)
            resource["status"] = "error"
            await resource.save()
        except Exception as exc:
            logging.exception(exc)
            resource["status"] = "failure"
            await resource.save()
            raise
