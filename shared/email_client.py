import smtplib
import boto3

from typing import List
from functools import wraps

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class EmailClient(metaclass=Singleton):
    """
    Email client using Office 365 SMTP server for sending notification for Snowflake admins and users.

    Attributes
    ----------
    recipients: str
        password for ServiceNow user
    sf_account: str
        Snowflake account name
    sf_username: str
        Snowflake user
    sf_password: str
        password for Snowflake user
    """

    def __init__(self, secrets_manager):
        self.secrets_manager = secrets_manager
        # MUST CHANGE TO EMAIL LIST WHERE NOTIFICATION SHOULD BE SENT
        self.recipients = ["default@email.ac.uk"]

        self.sender = secrets_manager.get_secret_value(
            SecretId="email_user"
        )['SecretString']

        self.password = secrets_manager.get_secret_value(
            SecretId="email_password"
        )['SecretString']

    def send_with_footnote(self, recipient: str, subject: str, body: str):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = recipient

        html = MIMEText(self.html_template.format(body), 'html')

        msg.attach(html)
        msg_str = msg.as_string()
        try:
            server = smtplib.SMTP("smtp.office365.com", 587)
            server.ehlo()
            server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, recipient, msg_str)
            server.close()
            print('Email sent!')
        except Exception as exception:
            print(f"Error: {exception}!\n\n")
            raise exception

    def send(self, recipients: List[str], subject: str, body: str):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = ", ".join(recipients)

        email_text = MIMEText(body, 'plain')

        msg.attach(email_text)
        msg_str = msg.as_string()
        try:
            server = smtplib.SMTP("smtp.office365.com", 587)
            server.ehlo()
            server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, recipients, msg_str)
            server.close()
            print('Email sent!')
        except Exception as exception:
            print(f"Error: {exception}!\n\n")
            raise exception

    def start(self, function_name):
        subject = "{} started".format(function_name)
        body = "Process to {} started.".format(function_name)
        self.send(self.recipients, subject, body)

    def error(self, function_name, error_message):
        subject = f"{function_name} failed"
        body = f"Process to {function_name} failed:\n{error_message}"
        self.send(self.recipients, subject, body)

    def success(self, function_name):
        subject = f"{function_name} succeeded"
        body = f"Process to {function_name} successfully finished."
        self.send(self.recipients, subject, body)

    html_template = """
<html>
  <head></head>
  <body>
    <p>{}</p>
    <p><span style="font-size: 13px;"><br></span></p>
      <ul type="disc">
        <li style="font-size: 13px;">Do not copy or download data, code or other material from the Trusted Research Environment Platform (TREP) without permission from data owner. &nbsp;</li>
        <li style="font-size: 13px;">Only access and use the TREP for the purpose of participating in the Consortium named.</li>
        <li style="font-size: 13px;">Security of the TREP is a shared security model. You are responsible for managing and protecting your usage of the TREP, your Participant Data and the Consortium Data, including user information, roles, password strength and encryption keys:</li>
        <li style="font-size: 13px;">Specifically, as a collaboration participant, usage and processing of your own Participant Data and the Consortium Data must comply with applicable laws and regulations. &nbsp;Only make available (share) data that you have the right to share. You must maintain all necessary consents and approvals for upload and making available such data.
            <ul style="font-size: initial;" type="circle">
                <li style="font-size: 13px;">Work with your institution Data Privacy Officer (or equivalent responsible person) to check for data restrictions, regulations and other relevant rules (including&nbsp;privacy legislation, data localisation, data sovereignty, data residency rules) and do not upload and share data if it would breach such restrictions.&nbsp;If the applicable rules mean certain legal standards need to be implemented prior to use or sharing of the Data, you must inform the TRE administration department so that together with your DPO we can look for suitable solutions. Note that the SCCs and UK IDTA are integrated in the TREP T&amp;Cs. The legal standards also need to be covered in the separate agreement between the consortium institutions governing the research project.</li>
                <li style="font-size: 13px;">DO NOT upload HIPAA data (patient, medical or other protected health information regulated by HIPAA or any similar U.S. federal or state laws, rules or regulations) to the TREP without administration department prior approval. You must request approval before the administration department provides you with Designated Accounts in order for the Designated Accounts to be configured to hold HIPAA Data.</li>
                <li style="font-size: 13px;">You are responsible for anonymisation and/or data transformation of data you upload and share.</li>
            </ul>
        </li>
      </ul>
  </body>
</html>
"""


def notification(secrets_manager, function_name):
    """
    Decorator that sends email notification when the function starts,
    sends success notification when function finishes without error,
    and sends error notification when the functions raises an exception.

    Every lambda function in this repository should be decorated with this function.

    Args:
        secrets_manager: Client for AWS secrets manager, where email credentials are stored.
        function_name: Readable name of the function that is decorated, e.g. `create user`.
    """
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if environ['env'] == "dev":
                try:
                    func(*args, **kwargs)
                    return {'status': 'success'}
                except Exception as e:
                    return {'status': 'error', 'message': str(e)}

            email_client = EmailClient(secrets_manager)
            email_client.start(function_name)
            try:
                func(*args, **kwargs)
                email_client.success(function_name)
                return {'status': 'success'}
            except Exception as e:
                print(e)
                email_client.error(function_name, str(e))
                return {'status': 'error', 'message': str(e)}

        return wrapper
    return inner
