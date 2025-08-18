# database.py
import os
import jwt
import datetime
from supabase import create_client
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv
import bcrypt
import threading
import logging

# Configure logging at the start of your app
logging.basicConfig(level=logging.INFO)

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
        logging.error(f"[DB ERROR] get_user_by_email: {e}", exc_info=True)
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
        logging.info(f"[DB] User added: {response}")
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"[DB ERROR] add_user: {e}", exc_info=True)
        raise


def mark_verified(email):
    """Set user.is_verified=True"""
    try:
        supabase.table("users").update({"is_verified": True}).eq(
            "email", email
        ).execute()
        logging.info(f"[DB] User verified: {email}")
        return True
    except Exception as e:
        logging.error(f"[DB ERROR] mark_verified: {e}", exc_info=True)
        return False


def delete_user(email):
    """Delete a user from DB"""
    try:
        response = supabase.table("users").delete().eq("email", email).execute()
        if response.data and len(response.data) > 0:
            logging.info(f"[DB] User deleted: {email}")
            return {"success": True, "message": f"User {email} deleted"}
        else:
            logging.warning(f"[DB] User not found or deletion blocked: {email}")
            return {
                "success": False,
                "message": f"User {email} not found or deletion blocked",
            }
    except Exception as e:
        logging.error(f"[DB ERROR] delete_user: {e}", exc_info=True)
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
        logging.warning("[AUTH] Invalid or expired JWT")
        return None


def schedule_unverified_deletion(email, delay_seconds=3600):
    """Delete user if not verified after delay_seconds (default 1 hour)"""

    def delete_if_unverified():
        user = get_user_by_email(email)
        if user and not user.get("is_verified", False):
            logging.info(f"[INFO] Deleting unverified user: {email}")
            delete_user(email)

    timer = threading.Timer(delay_seconds, delete_if_unverified)
    timer.start()


def add_conversion(
    user_id,
    original_filename,
    converted_filename,
    conversion_type,
    file_path,
    status="completed",
):
    """
    Add a converted file to Supabase Storage and record it in the 'files' table
    """
    try:
        logging.info("[START] add_conversion called")

        # 1️⃣ Upload file to Supabase Storage
        folder_path = f"{user_id}/"
        storage_path = folder_path + converted_filename
        logging.info(f"[UPLOAD] Uploading {file_path} → {storage_path}")

        storage = supabase.storage.from_("converted_files")

        # Check if file already exists
        existing_files = storage.list(user_id)  # list all files in the user's folder
        if converted_filename not in [f["name"] for f in existing_files]:
            with open(file_path, "rb") as f:
                storage.upload(storage_path, f)
        else:
            logging.info(
                f"[UPLOAD] File already exists: {storage_path}, skipping upload"
            )

        # 2️⃣ Get public download URL
        download_url = supabase.storage.from_("converted_files").create_signed_url(
            storage_path, 60 * 60 * 24  # expires in 24 hours
        )["signedURL"]
        logging.info(f"[URL] File uploaded. Public URL: {download_url}")

        # 3️⃣ File metadata
        file_size = os.path.getsize(file_path)
        created_at = datetime.datetime.utcnow().isoformat()
        logging.info(f"[META] Size: {file_size}, Created at: {created_at}")

        response = (
            supabase.table("files")
            .insert(
                {
                    "original_filename": original_filename,
                    "converted_filename": converted_filename,
                    "conversion_type": conversion_type,
                    "status": status,
                    "created_at": created_at,
                    "completed_at": created_at if status == "completed" else None,
                    "file_size": file_size,
                    "download_url": download_url,
                }
            )
            .execute()
        )

        logging.info(f"[DB] Insert response: {response}")
        return response.data[0] if response.data else None

    except Exception as e:
        logging.error(f"[DB ERROR] add_conversion: {e}", exc_info=True)
        return None
