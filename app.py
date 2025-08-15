import os
import auth
import tools  
import database
from flask import request
from functools import wraps
from flask_mail import Mail
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

load_dotenv()  # Load variables from .env

SECRET_KEY = os.getenv("SECRET_KEY")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT"))

# Flask-Mail configuration
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD

mail = Mail(app)

# ---------------- JWT-protected PDF decorator ----------------
def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Missing token"}), 401
        email = data_base.verify_jwt(token)
        if not email:
            return jsonify({"error": "Invalid or expired token"}), 403
        return func(*args, **kwargs)
    return wrapper

# ---------------- PDF routes ----------------
@app.route("/merge-pdf", methods=["POST"])
@require_auth
def merge_pdf_route():
    pdf_files = request.files.getlist("files")
    paths = tools.save_uploaded_files(pdf_files)
    output_path = tools.merge_pdfs(paths)
    return send_file(output_path, as_attachment=True)

@app.route("/split-pdf", methods=["POST"])
@require_auth
def split_pdf_route():
    pdf_file = request.files["file"]
    path = tools.save_uploaded_files([pdf_file])[0]
    zip_path = tools.split_pdf(path)
    return send_file(zip_path, as_attachment=True)

@app.route("/compress-pdf", methods=["POST"])
@require_auth
def compress_pdf_route():
    pdf_file = request.files["file"]
    path = tools.save_uploaded_files([pdf_file])[0]
    output_path = tools.compress_pdf(path)
    return send_file(output_path, as_attachment=True)

@app.route("/pdf-to-word", methods=["POST"])
@require_auth
def pdf_to_word_route():
    pdf_file = request.files["file"]
    path = tools.save_uploaded_files([pdf_file])[0]
    output_path = tools.pdf_to_word(path)
    return send_file(output_path, as_attachment=True)

@app.route("/pdf-to-jpg", methods=["POST"])
@require_auth
def pdf_to_jpg_route():
    pdf_file = request.files["file"]
    path = tools.save_uploaded_files([pdf_file])[0]
    zip_path = tools.pdf_to_jpg(path)
    return send_file(zip_path, as_attachment=True)

# ---------------- Authentication routes ----------------
@app.route("/signup", methods=["POST"])
def sign_up():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    if data_base.get_user_by_email(email):
        return jsonify({"error": "User already exists"}), 400
    
    # Add user to data_base DB
    data_base.add_user(email, password)
    
    # Send verification email
    auth.send_verification_email(email, mail, SECRET_KEY)
    
    return jsonify({"message": f"Verification email sent to {email}"}), 200

@app.route("/verify-email/<token>")
def verify_email(token):
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]
        data_base.mark_verified(email)
        return jsonify({"message": f"Email {email} verified successfully!"}), 200
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 400
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    user = data_base.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User does not exist"}), 404
    if user["password"] != password:
        return jsonify({"error": "Incorrect password"}), 401
    if not user["is_verified"]:
        return jsonify({"error": "Email not verified"}), 403
    
    token = data_base.generate_jwt(email)
    return jsonify({"token": token}), 200  

# ---------------- Run app ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
