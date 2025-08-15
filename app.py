from flask import Flask, request, send_file, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import fitz  # PyMuPDF
import zipfile
import shutil
import os
import uuid
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_uploaded_files(files):
    paths = []
    for file in files:
        filename = f"{uuid.uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        paths.append(path)
    return paths

@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    pdf_files = request.files.getlist("files")
    paths = save_uploaded_files(pdf_files)
    merger = PdfMerger()
    for pdf in paths:
        merger.append(pdf)
    output_path = os.path.join(UPLOAD_FOLDER, f"merged_{uuid.uuid4()}.pdf")
    merger.write(output_path)
    merger.close()
    return send_file(output_path, as_attachment=True)

@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    pdf_file = request.files["file"]
    path = save_uploaded_files([pdf_file])[0]
    reader = PdfReader(path)

    output_dir = os.path.join(UPLOAD_FOLDER, f"split_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        part_path = os.path.join(output_dir, f"page_{i+1}.pdf")
        with open(part_path, "wb") as f:
            writer.write(f)

    # TODO: Zip all the split files before returning
    zip_path = shutil.make_archive(output_dir, "zip", output_dir)
    return send_file(zip_path, as_attachment=True)

@app.route("/compress-pdf", methods=["POST"])
def compress_pdf():
    pdf_file = request.files["file"]
    path = save_uploaded_files([pdf_file])[0]
    doc = fitz.open(path)
    output_path = os.path.join(UPLOAD_FOLDER, f"compressed_{uuid.uuid4()}.pdf")
    doc.save(output_path, deflate=True)
    doc.close()
    return send_file(output_path, as_attachment=True)

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    pdf_file = request.files["file"]
    path = save_uploaded_files([pdf_file])[0]
    output_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.docx")
    cv = Converter(path)
    cv.convert(output_path)
    cv.close()
    return send_file(output_path, as_attachment=True)

@app.route("/pdf-to-jpg", methods=["POST"])
def pdf_to_jpg():
    pdf_file = request.files["file"]
    path = save_uploaded_files([pdf_file])[0]
    pdf = fitz.open(path)

    output_dir = os.path.join(UPLOAD_FOLDER, f"jpg_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(pdf):
        pix = page.get_pixmap()
        img_path = os.path.join(output_dir, f"page_{i+1}.jpg")
        pix.save(img_path)

    pdf.close()

    # TODO: Zip all the JPG files before returning
    zip_path = shutil.make_archive(output_dir, "zip", output_dir)
    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
