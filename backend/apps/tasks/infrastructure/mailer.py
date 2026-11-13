from django.core.mail import send_mail


class DjangoMailer:
    """Sends through the default mailer in MAILERS (SMTP to Mailpit in Docker)."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        # from_email=None means DEFAULT_FROM_EMAIL. Errors propagate so the job can retry.
        send_mail(subject, body, from_email=None, recipient_list=[to])
