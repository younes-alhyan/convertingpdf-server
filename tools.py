# tools.py
import os
import uuid
import shutil
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter

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

def merge_pdfs(paths):
    merger = PdfMerger()
    for pdf in paths:
        merger.append(pdf)
    output_path = os.path.join(UPLOAD_FOLDER, f"merged_{uuid.uuid4()}.pdf")
    merger.write(output_path)
    merger.close()
    return output_path

def split_pdf(path):
    reader = PdfReader(path)
    output_dir = os.path.join(UPLOAD_FOLDER, f"split_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        part_path = os.path.join(output_dir, f"page_{i+1}.pdf")
        with open(part_path, "wb") as f:
            writer.write(f)
    zip_path = shutil.make_archive(output_dir, "zip", output_dir)
    return zip_path

def compress_pdf(path):
    doc = fitz.open(path)
    output_path = os.path.join(UPLOAD_FOLDER, f"compressed_{uuid.uuid4()}.pdf")
    doc.save(output_path, deflate=True)
    doc.close()
    return output_path

def pdf_to_word(path):
    output_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.docx")
    cv = Converter(path)
    cv.convert(output_path)
    cv.close()
    return output_path

def pdf_to_jpg(path):
    pdf = fitz.open(path)
    output_dir = os.path.join(UPLOAD_FOLDER, f"jpg_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)
    for i, page in enumerate(pdf):
        pix = page.get_pixmap()
        img_path = os.path.join(output_dir, f"page_{i+1}.jpg")
        pix.save(img_path)
    pdf.close()
    zip_path = shutil.make_archive(output_dir, "zip", output_dir)
    return zip_path
