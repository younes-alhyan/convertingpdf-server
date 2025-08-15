verification_responses = [
    {
        "title": "✅ Email Verified",
        "message": "Your email has been successfully verified! You can now log in.",
    },
    {
        "title": "⏰ Token Expired",
        "message": "The verification link has expired. Please sign up again to receive a new link.",
    },
    {
        "title": "❌ Invalid Token",
        "message": "The verification link is invalid or malformed. Please check your email or request a new link.",
    },
    {
        "title": "⚠️ Verification Failed",
        "message": "An unexpected error occurred while verifying your email. Please try again later.",
    },
]


def verification_html(code):
    try:
        resp = verification_responses[code]
    except IndexError:
        resp = verification_responses[3]  # default fail message

    return f"""
    <html>
        <head><title>Email Verification</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
            <h1>{resp['title']}</h1>
            <p>{resp['message']}</p>
        </body>
    </html>
    """

