# app.py
import os
import uuid
from functools import wraps
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import bcrypt

import database
import auth
import pages
import tools

# ---------------- App setup ----------------
load_dotenv()
app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# Mail config
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)
SECRET_KEY = os.getenv("SECRET_KEY")


# ---------------- JWT-protected decorator ----------------
def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or " " not in auth_header:
            return jsonify({"error": "Missing token"}), 401
        token = auth_header.split(" ")[1]
        email = database.verify_jwt(token)
        if not email:
            return jsonify({"error": "Invalid or expired token"}), 403
        return func(*args, **kwargs)

    return wrapper


# ---------------- PDF routes (updated) ----------------
from flask import request, jsonify, send_file
import uuid
import os
import database
import tools


def get_user_id():
    """Helper to extract user_id from headers"""
    user_id = request.headers.get("X-User-ID")  # Or use request.json.get("user_id")
    if not user_id:
        raise ValueError("User ID required")
    return user_id


def build_response(conversion):
    """Standardized JSON response"""
    return {
        "conversion_id": str(conversion["id"]),
        "converted_filename": conversion["converted_filename"],
        "downloadUrl": conversion["download_url"],
        "file_size": conversion["file_size"],
        "status": conversion["status"],
        "message": "Conversion completed successfully",
    }


@app.route("/merge-pdf", methods=["POST"])
@require_auth
def merge_pdf_route():
    try:
        user_id = get_user_id()
        pdf_files = request.files.getlist("files")
        if not pdf_files:
            return jsonify({"error": "No files uploaded"}), 400
        paths = tools.save_uploaded_files(pdf_files)
        output_path = tools.merge_pdfs(paths)
        converted_filename = "merged.pdf"

        conversion = database.add_conversion(
            user_id=user_id,
            original_filename=";".join(f.filename for f in pdf_files),
            converted_filename=converted_filename,
            conversion_type="merge",
            file_path=output_path,
        )
        return jsonify(build_response(conversion))

    except Exception as e:
        print(f"[ERROR] merge_pdf_route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/split-pdf", methods=["POST"])
@require_auth
def split_pdf_route():
    try:
        user_id = get_user_id()
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        zip_path = tools.split_pdf(path)
        converted_filename = pdf_file.filename.replace(".pdf", "_split.zip")

        conversion = database.add_conversion(
            user_id=user_id,
            original_filename=pdf_file.filename,
            converted_filename=converted_filename,
            conversion_type="split",
            file_path=zip_path,
        )
        return jsonify(build_response(conversion))

    except Exception as e:
        print(f"[ERROR] split_pdf_route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/compress-pdf", methods=["POST"])
@require_auth
def compress_pdf_route():
    try:
        user_id = get_user_id()
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        output_path = tools.compress_pdf(path)
        converted_filename = pdf_file.filename.replace(".pdf", "_compressed.pdf")

        conversion = database.add_conversion(
            user_id=user_id,
            original_filename=pdf_file.filename,
            converted_filename=converted_filename,
            conversion_type="compress",
            file_path=output_path,
        )
        return jsonify(build_response(conversion))

    except Exception as e:
        print(f"[ERROR] compress_pdf_route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/pdf-to-word", methods=["POST"])
@require_auth
def pdf_to_word_route():
    try:
        user_id = get_user_id()
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        output_path = tools.pdf_to_word(path)
        converted_filename = pdf_file.filename.replace(".pdf", ".docx")

        conversion = database.add_conversion(
            user_id=user_id,
            original_filename=pdf_file.filename,
            converted_filename=converted_filename,
            conversion_type="pdf_to_word",
            file_path=output_path,
        )
        return jsonify(build_response(conversion))

    except Exception as e:
        print(f"[ERROR] pdf_to_word_route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/pdf-to-jpg", methods=["POST"])
@require_auth
def pdf_to_jpg_route():
    try:
        user_id = get_user_id()
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        zip_path = tools.pdf_to_jpg(path)
        converted_filename = pdf_file.filename.replace(".pdf", "_jpg.zip")

        conversion = database.add_conversion(
            user_id=user_id,
            original_filename=pdf_file.filename,
            converted_filename=converted_filename,
            conversion_type="pdf_to_jpg",
            file_path=zip_path,
        )
        return jsonify(build_response(conversion))

    except Exception as e:
        print(f"[ERROR] pdf_to_jpg_route: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------- Auth routes ----------------
@app.route("/signup", methods=["POST"])
def sign_up():
    try:
        data = request.json
        full_name = data.get("fullName")
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        if database.get_user_by_email(email):
            return jsonify({"error": "User already exists"}), 400
        user = database.add_user(full_name, email, password)
        if not user:
            return jsonify({"error": "Failed to create user"}), 500
        auth.send_verification_email(email, mail, SECRET_KEY)
        database.schedule_unverified_deletion(email, 3600)
        return jsonify({"message": f"Verification email sent to {email}"}), 200
    except Exception as e:
        print(f"[ERROR] sign_up: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/verify-email/<token>")
def verify_email(token):
    from jwt import ExpiredSignatureError, InvalidTokenError

    try:
        payload = database.jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]
        if database.mark_verified(email):
            return render_template_string(pages.verification_html(0)), 200
        else:
            return render_template_string(pages.verification_html(3)), 500
    except ExpiredSignatureError:
        return render_template_string(pages.verification_html(1)), 400
    except InvalidTokenError:
        return render_template_string(pages.verification_html(2)), 400
    except Exception as e:
        print(f"[ERROR] verify_email: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        user = database.get_user_by_email(email)
        if not user:
            return jsonify({"error": "User does not exist"}), 404
        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"error": "Incorrect password"}), 401
        if not user["is_verified"]:
            return jsonify({"error": "Email not verified"}), 403
        token = database.generate_jwt(email)
        return (
            jsonify(
                {
                    "id": user["id"],
                    "email": user["email"],
                    "fullName": user["fullname"],
                    "token": token,
                }
            ),
            200,
        )
    except Exception as e:
        print(f"[ERROR] login: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/delete", methods=["DELETE"])
@require_auth
def delete_account():
    try:
        data = request.json
        email = data.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400
        result = database.delete_user(email)
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["message"]}), 400
    except Exception as e:
        print(f"[ERROR] delete_account: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ---------------- Run server ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
