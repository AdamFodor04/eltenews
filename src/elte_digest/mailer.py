from email.message import EmailMessage
import smtplib
from datetime import date

from .config import Settings
from .models import Summary


def send_digest(items: list[Summary], settings: Settings) -> None:
    if not items:
        return
    message = EmailMessage()
    message["Subject"] = f"ELTE napi TL;DR – {date.today().isoformat()} ({len(items)} új)"
    message["From"] = settings.mail_from
    message["To"] = settings.mail_to
    body = ["Az elmúlt futás óta felfedezett ELTE-anyagok rövid összefoglalói:\n"]
    for item in items:
        body.extend([f"{item.article.title}", item.text, item.article.url, ""])
    message.set_content("\n".join(body))
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
