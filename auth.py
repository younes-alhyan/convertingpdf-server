# auth.py
import jwt
import datetime
from flask_mail import Message
from flask import url_for
import os

def generate_verification_token(email, secret_key):
    payload = {
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def send_verification_email(email, mail, secret_key):
    """
    Sends a verification email via Flask-Mail.
    """
    token = generate_verification_token(email, secret_key)
    verify_url = url_for("verify_email", token=token, _external=True)

    msg = Message(
        subject="Verify your email",
        sender=os.getenv("MAIL_USERNAME"),
        recipients=[email],
        body=f"""
Hello!

Please click the link to verify your email:

{verify_url}

This link will expire in 24 hours.

If you did not sign up, ignore this email.
"""
    )
    mail.send(msg)
