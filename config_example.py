from pathlib import Path

TMS_URL = 'https://your-tms-url/framework/Frame.jsp'

# .env keys for TMS credentials
TMS_USER_ENV = 'TMSUser'
TMS_PASS_ENV = 'TMSPW'

ENV_PATH = Path(r'\\your-server\path\to\.env')

DESKTOP_PATH = Path.home() / 'Desktop'
DOWNLOAD_BASE = DESKTOP_PATH / 'YourFolder' / 'Data'
MAX_DATA_FOLDERS = 5

SMTP_SERVER = 'your.smtp.server'
SMTP_PORT = 25

# .env keys for SMTP credentials
SMTP_USER_ENV = 'SMTPUser'
SMTP_PASS_ENV = 'SMTPPW'

EMAIL_FROM    = 'sender@example.com'
EMAIL_TO      = ['recipient@example.com']
EMAIL_CC      = ['cc@example.com']
EMAIL_SUBJECT = 'Tender Status Report {}'  # .format(date)
