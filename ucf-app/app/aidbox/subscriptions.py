import uuid

from app.aidbox.sdk import sdk
from app.config.emr import FRONTEND_URL, EMAIL_PROVIDER

from datetime import timedelta

from app.fhirdate import format_fhir_date_time, get_now
from fhirpathpy import evaluate
import logging


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
                        "subject": "Welcome to UCF MammoChat Research Study!",
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


study_coordinator_email = 'Amoy.Fraser@ucf.edu'

@sdk.subscription("QuestionnaireResponse")
async def send_qr_notification(event, request):
    qr = event["resource"]
    aidbox = request.app["client"]
    if event["action"] == "create" and qr["status"] == "completed":
        logging.debug("QR created %s", qr["id"])
        if qr["questionnaire"] in ["patient-informed-consent", "authorization-for-release-of-medical-images"]:
            logging.debug("Processing %s", qr["id"])
            patient_id = qr["subject"]["id"]
            qr_id = qr["id"]
            patient = await aidbox.reference("Patient", patient_id).to_resource()
            questionnaire = await aidbox.reference("Questionnaire", qr["questionnaire"]).to_resource()
            emails = evaluate(patient, "Patient.telecom.where(system='email').value")
            if len(emails) == 1:
                patient_email = emails[0]
                notification = aidbox.resource(
                    "Notification",
                    **{
                        "provider": EMAIL_PROVIDER,
                        "providerData": {
                            "to": patient_email,
                            "subject": f"Copy of your {questionnaire['title']}",
                            "template": {
                                "id": "questionnaire-pdf",
                                "resourceType": "NotificationTemplate",
                            },
                            "payload": {
                                "print-href": f"{FRONTEND_URL}/print-patient-document/{patient_id}/{qr_id}",
                            },
                        },
                    },
                )
                await notification.save()
                logging.debug("Notifing patient %s", notification['id'])
                await notification.execute("$send")

            patient_name = evaluate(patient, "Patient.name.given + ' ' + Patient.name.family")[0]
            notification = aidbox.resource(
                "Notification",
                **{
                    "provider": EMAIL_PROVIDER,
                    "providerData": {
                        "to": study_coordinator_email,
                        "subject": f"Copy of {patient_name} {questionnaire['title']}",
                        "template": {
                            "id": "questionnaire-pdf",
                            "resourceType": "NotificationTemplate",
                        },
                        "payload": {
                            "print-href": f"{FRONTEND_URL}/print-patient-document/{patient_id}/{qr_id}",
                        },
                    },
                },
            )
            await notification.save()
            logging.debug("Notifing study coordinator %s", notification['id'])
            await notification.execute("$send")
