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

# ---------------- PDF routes ----------------
@app.route("/merge-pdf", methods=["POST"])
@require_auth
def merge_pdf_route():
    try:
        pdf_files = request.files.getlist("files")
        if not pdf_files:
            return jsonify({"error": "No files uploaded"}), 400
        paths = tools.save_uploaded_files(pdf_files)
        output_path = tools.merge_pdfs(paths)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        print(f"[ERROR] merge_pdf_route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/split-pdf", methods=["POST"])
@require_auth
def split_pdf_route():
    try:
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        zip_path = tools.split_pdf(path)
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        print(f"[ERROR] split_pdf_route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/compress-pdf", methods=["POST"])
@require_auth
def compress_pdf_route():
    try:
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        output_path = tools.compress_pdf(path)
        converted_filename = pdf_file.filename.replace(".pdf", "_compressed.pdf")
        file_size = os.path.getsize(output_path)
        conversion_id = str(uuid.uuid4())
        download_url = "/downloads/" + converted_filename  # example
        return jsonify({
            "conversion_id": conversion_id,
            "converted_filename": converted_filename,
            "downloadUrl": download_url,
            "file_size": file_size,
            "status": "completed",
            "message": "PDF compressed successfully",
        })
    except Exception as e:
        print(f"[ERROR] compress_pdf_route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/pdf-to-word", methods=["POST"])
@require_auth
def pdf_to_word_route():
    try:
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        output_path = tools.pdf_to_word(path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        print(f"[ERROR] pdf_to_word_route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/pdf-to-jpg", methods=["POST"])
@require_auth
def pdf_to_jpg_route():
    try:
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400
        path = tools.save_uploaded_files([pdf_file])[0]
        zip_path = tools.pdf_to_jpg(path)
        return send_file(zip_path, as_attachment=True)
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
        return jsonify({"token": token}), 200
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
