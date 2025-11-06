# app.py
import os
import logging
from flask_cors import CORS
from flask import Flask, request, jsonify, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import tools

# ---------------- App setup ----------------
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# ---------------- PDF routes ----------------


@app.route("/merge-pdf", methods=["POST"])
def merge_pdf_route():
    try:
        pdf_files = request.files.getlist("files")
        if not pdf_files:
            return jsonify({"error": "No files uploaded"}), 400

        paths = tools.save_uploaded_files(pdf_files)
        output_path = tools.merge_pdfs(paths)
        filename = pdf_files[0].filename
        converted_filename = f"{filename}_merged.pdf"

        tools.clear_uploads_folder()

        return send_file(
            output_path,
            as_attachment=True,
            download_name=converted_filename,
            mimetype="application/pdf",
        )

    except Exception as e:
        logging.error(f"[ERROR] merge_pdf_route: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/split-pdf", methods=["POST"])
def split_pdf_route():
    try:
        pdf_file = request.files.get("file")
        split_type = request.form.get("splitType")
        split_value = request.form.get("splitValue")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400

        path = tools.save_uploaded_files([pdf_file])[0]
        zip_path = tools.split_pdf(path, split_type, split_value)
        converted_filename = pdf_file.filename.replace(".pdf", "_split.zip")

        tools.clear_uploads_folder()

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=converted_filename,
            mimetype="application/zip",
        )

    except Exception as e:
        logging.error(f"[ERROR] split_pdf_route: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/compress-pdf", methods=["POST"])
def compress_pdf_route():
    try:
        pdf_file = request.files.get("file")
        compression_level = request.form.get("compressionLevel", "medium")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400

        path = tools.save_uploaded_files([pdf_file])[0]
        output_path = tools.compress_pdf(path, level=compression_level)
        converted_filename = pdf_file.filename.replace(".pdf", "_compressed.pdf")

        tools.clear_uploads_folder()

        return send_file(
            output_path,
            as_attachment=True,
            download_name=converted_filename,
            mimetype="application/pdf",
        )

    except Exception as e:
        logging.error(f"[ERROR] compress_pdf_route: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word_route():
    try:
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400

        path = tools.save_uploaded_files([pdf_file])[0]
        output_path = tools.pdf_to_word(path)
        converted_filename = pdf_file.filename.replace(".pdf", ".docx")

        tools.clear_uploads_folder()

        return send_file(
            output_path,
            as_attachment=True,
            download_name=converted_filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as e:
        logging.error(f"[ERROR] pdf_to_word_route: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/pdf-to-jpg", methods=["POST"])
def pdf_to_jpg_route():
    try:
        pdf_file = request.files.get("file")
        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400

        path = tools.save_uploaded_files([pdf_file])[0]
        zip_path = tools.pdf_to_jpg(path)
        converted_filename = pdf_file.filename.replace(".pdf", "_jpg.zip")

        tools.clear_uploads_folder()

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=converted_filename,
            mimetype="application/zip",
        )

    except Exception as e:
        logging.error(f"[ERROR] pdf_to_jpg_route: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/edit", methods=["POST"])
def edit_route():
    try:
        pdf_file = request.files.get("file")
        edit_type = request.form.get("editType")
        edit_data = request.form.get("editData")

        if not pdf_file:
            return jsonify({"error": "No file uploaded"}), 400

        path = tools.save_uploaded_files([pdf_file])[0]

        edit_data = json.loads(edit_data)
        # Destructure
        if edit_type == "add-image":
            image_file = request.files.get("imageFile")
            if not image_file:
                return jsonify({"error": "No image uploaded"}), 400
            content = image_file  # pass the file object
        else:
            content = edit_data.get("content")
            if not content:
                return jsonify({"error": "No text content provided"}), 400

        x = edit_data.get("x")
        y = edit_data.get("y")

        output_path = tools.edit_pdf(path, edit_type, content, x, y)
        converted_filename = pdf_file.filename.replace(".pdf", "_edited.pdf")

        tools.clear_uploads_folder()

        return send_file(
            output_path,
            as_attachment=True,
            download_name=converted_filename,
            mimetype="application/pdf",
        )

    except Exception as e:
        logging.error(f"[ERROR] edit_pdf_route: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ---------------- Run server ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
