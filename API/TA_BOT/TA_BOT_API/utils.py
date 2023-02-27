import smtplib
import ssl
from email.message import EmailMessage

def send_email(email_host: str, host_port: int, sender_email: str, password: str, receiver_email: str, subject: str, message: str):
    # Set the subject and body of the email
    em = EmailMessage()
    em['From'] = sender_email
    em['To'] = receiver_email
    em['Subject'] = subject
    em.set_content(message)

    # Add SSL (layer of security)
    context = ssl.create_default_context()
    
    # Log in and send the email
    with smtplib.SMTP_SSL(email_host, host_port, context=context) as smtp:
        smtp.login(sender_email, password)
        smtp.sendmail(sender_email, receiver_email, em.as_string())