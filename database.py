# database.py
import os
import jwt
import datetime
from supabase import create_client
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv
import bcrypt
import threading

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


def schedule_unverified_deletion(email, delay_seconds=3600):
    """Delete user if not verified after delay_seconds (default 1 hour)"""

    def delete_if_unverified():
        user = get_user_by_email(email)
        if user and not user.get("is_verified", False):
            print(f"[INFO] Deleting unverified user: {email}")
            delete_user(email)

    timer = threading.Timer(delay_seconds, delete_if_unverified)
    timer.start()


def add_conversion(user_id, original_filename, converted_filename, conversion_type, file_path, status="completed"):
    try:
        print("[INFO] Starting add_conversion...")
        folder_path = f"{user_id}/"
        storage_path = folder_path + converted_filename
        print(f"[INFO] Storage path: {storage_path}")

        # 1️⃣ Upload file
        try:
            print("[INFO] Uploading file to Supabase Storage...")
            with open(file_path, "rb") as f:
                supabase.storage.from_("converted_files").upload(storage_path, f, {"upsert": True})
            print("[INFO] File uploaded successfully.")
        except Exception as e:
            print(f"[ERROR] Storage upload failed: {e}")
            return None

        # 2️⃣ Generate signed URL
        try:
            print("[INFO] Generating download URL...")
            download_url = supabase.storage.from_("converted_files").create_signed_url(storage_path, 3600)["signedURL"]
            print(f"[INFO] Download URL: {download_url}")
        except Exception as e:
            print(f"[ERROR] Generating signed URL failed: {e}")
            return None

        # 3️⃣ Get file size and timestamp
        try:
            file_size = os.path.getsize(file_path)
            created_at = datetime.datetime.utcnow()
            print(f"[INFO] File size: {file_size}, created_at: {created_at}")
        except Exception as e:
            print(f"[ERROR] Getting file metadata failed: {e}")
            return None

        # 4️⃣ Insert into files table
        try:
            print("[INFO] Inserting record into files table...")
            response = supabase.table("files").insert({
                "original_filename": original_filename,
                "converted_filename": converted_filename,
                "conversion_type": conversion_type,
                "status": status,
                "created_at": created_at,
                "completed_at": created_at if status == "completed" else None,
                "file_size": file_size,
                "download_url": download_url,
                "user_id": user_id,
            }).execute()

            if response.error:
                print(f"[ERROR] Insert failed: {response.error}")
                return None

            print("[INFO] Insert successful!")
            return response.data[0]

        except Exception as e:
            print(f"[ERROR] Insert exception: {e}")
            return None

    except Exception as e:
        print(f"[DB ERROR] Unexpected error in add_conversion: {e}")
        return None
