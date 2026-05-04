import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate
from email import encoders
from pathlib import Path
from typing import List, Optional

import config

logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def send(
        self,
        subject: str,
        body: str,
        to: List[str],
        cc: List[str] = None,
        sender: str = None,
        attachment_path: Optional[Path] = None,
    ) -> bool:
        cc = cc or []
        sender = sender or config.EMAIL_FROM

        msgRoot = MIMEMultipart('related')
        msgRoot['From'] = sender
        msgRoot['To'] = ','.join(to)
        msgRoot['Cc'] = ','.join(cc)
        msgRoot['Date'] = formatdate(localtime=True)
        msgRoot['Subject'] = subject

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        msgAlternative.attach(MIMEText(body, 'html', 'utf-8'))

        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=Path(attachment_path).name)
            msgRoot.attach(part)

        try:
            with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
                smtp.login(self.username, self.password)
                smtp.sendmail(sender, to + cc, msgRoot.as_string())
            logger.info(f"Mail sent to {to + cc}")
            return True
        except Exception as e:
            logger.error(f"Failed to send mail: {e}", exc_info=True)
            return False
