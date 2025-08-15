import os
import auth
import pages
import tools
import database
from flask import Flask, request, send_file, jsonify
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from dotenv import load_dotenv
from flask import render_template_string

# ---------------- App setup ----------------
app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

load_dotenv()  # Load .env variables

SECRET_KEY = os.getenv("SECRET_KEY")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT"))

# Flask-Mail config
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD

mail = Mail(app)


# ---------------- JWT-protected decorator ----------------
def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Missing token"}), 401
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
        return send_file(output_path, as_attachment=True)
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
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        if database.get_user_by_email(email):
            return jsonify({"error": "User already exists"}), 400

        user = database.add_user(email, password)
        if not user:
            return jsonify({"error": "Failed to create user"}), 500

        auth.send_verification_email(email, mail, SECRET_KEY)
        return jsonify({"message": f"Verification email sent to {email}"}), 200
    except Exception as e:
        print(f"[ERROR] sign_up: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/verify-email/<token>")
def verify_email(token):
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
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
        if user["password"] != password:
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
