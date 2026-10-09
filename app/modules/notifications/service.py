from app.tasks.email_tasks import send_email_task


def send_notification(
    recipient_email: str, template_name: str, subject: str, context: dict
) -> None:
    send_email_task.delay(
        recipient_email=recipient_email,
        template_name=template_name,
        subject=subject,
        context=context,
    )
