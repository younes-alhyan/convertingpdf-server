# database.py
import os
import jwt
import datetime
from supabase import create_client
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv
import bcrypt

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------- Auth helpers ----------------
def get_user_by_email(email):
    """Check if a user exists in DB by email"""
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] get_user_by_email: {e}")
        return None


def add_user(full_name, email, password):
    """Insert a new user into DB with hashed password"""
    try:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        response = (
            supabase.table("users")
            .insert(
                {
                    "fullname": full_name,
                    "email": email,
                    "password": hashed_password,
                    "is_verified": False,
                }
            )
            .execute()
        )
        print("Supabase response:", response)
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] add_user: {e}")
        raise


def mark_verified(email):
    """Set user.is_verified=True"""
    try:
        supabase.table("users").update({"is_verified": True}).eq(
            "email", email
        ).execute()
        return True
    except Exception as e:
        print(f"[DB ERROR] mark_verified: {e}")
        return False


def delete_user(email):
    """Delete a user from DB"""
    try:
        response = supabase.table("users").delete().eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return {"success": True, "message": f"User {email} deleted"}
        else:
            return {
                "success": False,
                "message": f"User {email} not found or deletion blocked",
            }
    except Exception as e:
        print(f"[DB ERROR] delete_user: {e}")
        return {"success": False, "message": str(e)}


def generate_jwt(email):
    """Generate a JWT token for login sessions"""
    payload = {
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_jwt(token):
    """Decode JWT and return email if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["email"]
    except (ExpiredSignatureError, InvalidTokenError):
        return None
