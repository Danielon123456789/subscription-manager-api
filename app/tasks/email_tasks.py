from jinja2 import Environment, FileSystemLoader
from app.tasks.celery_app import celery_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

env = Environment(
    loader=FileSystemLoader("app/modules/notifications/templates"),
    autoescape=True,
)

sg = SendGridAPIClient(api_key=os.getenv("SMTP_API_KEY"))


@celery_app.task
def send_email_task(
    recipient_email: str, template_name: str, subject: str, context: dict
) -> None:
    template = env.get_template(template_name)
    html_content = template.render(**context)

    message = Mail(
        from_email=os.getenv("SENDER_EMAIL"),
        to_emails=recipient_email,
        subject=subject,
        html_content=html_content,
    )

    sg.send(message)
