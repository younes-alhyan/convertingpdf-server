# supabase.py
from supabase import create_client
import os
from dotenv import load_dotenv
import jwt
import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------- Auth helpers ----------------

def get_user_by_email(email):
    """Check if a user exists in DB by email"""
    response = supabase.table("users").select("*").eq("email", email).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None

def add_user(email, password):
    """Add new user to DB with is_verified=False"""
    user = supabase.table("users").insert({
        "email": email,
        "password": password,  # Ideally hash this before storing
        "is_verified": False
    }).execute()
    return user

def mark_verified(email):
    """Set user.is_verified=True"""
    supabase.table("users").update({"is_verified": True}).eq("email", email).execute()

def generate_jwt(email):
    """Generate a JWT token for login sessions"""
    payload = {
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt(token):
    """Decode JWT and return email if valid"""
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["email"]
    except (ExpiredSignatureError, InvalidTokenError):
        return None
