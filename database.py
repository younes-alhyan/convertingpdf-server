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
import uuid
import httpx

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
    Add a converted file to Supabase Storage and record it in the 'files' table.
    File is stored by its conversion UUID and deleted after 1 hour.
    """
    try:
        logging.info("[START] add_conversion called")

        # 1️⃣ Insert DB record first to get UUID
        created_at = datetime.datetime.utcnow().isoformat()
        file_size = os.path.getsize(file_path)

        insert_resp = (
            supabase.table("files")
            .insert(
                {
                    "user_id": user_id,
                    "original_filename": original_filename,
                    "converted_filename": converted_filename,
                    "conversion_type": conversion_type,
                    "status": status,
                    "created_at": created_at,
                    "completed_at": created_at if status == "completed" else None,
                    "file_size": file_size,
                    "download_url": None,  # placeholder until upload
                }
            )
            .execute()
        )

        if not insert_resp.data:
            logging.error("[DB ERROR] Could not insert file record")
            return None

        file_record = insert_resp.data[0]
        file_id = file_record["id"]  # UUID from Supabase

        # 2️⃣ Decide file extension based on conversion type
        if conversion_type in ["split", "pdf_to_jpg"]:
            file_ext = ".zip"
            content_type = "application/zip"
        elif conversion_type == "pdf_to_word":
            file_ext = ".docx"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
        else:
            file_ext = ".pdf"
            content_type = "application/pdf"

        # 3️⃣ Upload file using UUID as storage path
        storage_path = f"{user_id}/{file_id}{file_ext}"
        storage = supabase.storage.from_("converted_files")

        with open(file_path, "rb") as f:
            storage.upload(storage_path, f, {"content-type": content_type})

        # 4️⃣ Create signed URL (1 hour)
        download_url = storage.create_signed_url(storage_path, 60 * 60)["signedURL"]

        # 5️⃣ Update DB record with the signed URL
        supabase.table("files").update({"download_url": download_url}).eq(
            "id", file_id
        ).execute()

        logging.info(f"[UPLOAD] File stored as {storage_path}, URL: {download_url}")

        # 6️⃣ Schedule deletion after 1 hour
        def delete_after_delay():
            try:
                storage.remove([storage_path])
                logging.info(f"[CLEANUP] Deleted {storage_path} from storage")
                supabase.table("files").delete().eq("id", file_id).execute()
                logging.info(f"[CLEANUP] Deleted DB record for {file_id}")
            except Exception as e:
                logging.error(f"[CLEANUP ERROR] {e}", exc_info=True)

        threading.Timer(3600, delete_after_delay).start()

        return {**file_record, "download_url": download_url}
    except httpx.ReadTimeout:
        logging.error("[TIMEOUT] Upload took too long")
        return {"error": "upload_timeout"}

    except Exception as e:
        logging.error(f"[DB ERROR] add_conversion: {e}", exc_info=True)
        return None


def get_conversions(user_id):
    """
    Fetch all conversions for a specific user.
    Returns a list of conversion records (dicts).
    """
    try:
        resp = (
            supabase.table("files")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)  # newest first
            .execute()
        )
        logging.error(resp)
        # Check if there was an error
        if getattr(resp, "error", None):
            print(f"[ERROR] Supabase returned an error: {resp.error}")
            return None  # Indicates request failed

        # If no error, return data (could be empty list)
        return resp.data or []  # empty list if no records

    except Exception as e:
        print(f"[ERROR] get_conversions failed: {e}")
        return []
