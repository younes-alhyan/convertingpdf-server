# tools.py
import os
import uuid
import shutil
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from io import BytesIO

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


def split_pdf(path, split_type="pages", split_value=None):
    """
    Split a PDF into multiple files by pages or ranges and return a zip path.

    split_type: "pages" or "ranges"
    split_value:
        - "pages": string with number of pages per split, e.g., "3"
        - "ranges": string with comma-separated ranges, e.g., "1-2,4-7"
    """
    reader = PdfReader(path)
    num_pages = len(reader.pages)
    output_dir = os.path.join(UPLOAD_FOLDER, f"split_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)

    files_created = []

    if split_type == "pages":
        if not split_value:
            raise ValueError("split_value required for 'pages'")
        pages_per_file = int(split_value)
        for start in range(0, num_pages, pages_per_file):
            writer = PdfWriter()
            end = min(start + pages_per_file, num_pages)
            for i in range(start, end):
                writer.add_page(reader.pages[i])
            part_path = os.path.join(output_dir, f"pages_{start+1}_to_{end}.pdf")
            with open(part_path, "wb") as f:
                writer.write(f)
            files_created.append(part_path)

    elif split_type == "ranges":
        if not split_value:
            raise ValueError("split_value required for 'ranges'")
        ranges = split_value.split(",")
        for r in ranges:
            start_str, end_str = r.split("-")
            start, end = int(start_str) - 1, int(end_str)  # zero-indexed
            writer = PdfWriter()
            for i in range(start, end):
                if 0 <= i < num_pages:
                    writer.add_page(reader.pages[i])
            part_path = os.path.join(output_dir, f"pages_{start+1}_to_{end}.pdf")
            with open(part_path, "wb") as f:
                writer.write(f)
            files_created.append(part_path)

    else:
        raise ValueError("Invalid split_type, must be 'pages' or 'ranges'")

    zip_path = shutil.make_archive(output_dir, "zip", output_dir)
    return zip_path


def compress_pdf(path, level="medium"):
    """
    Compress a PDF according to the specified level.
    level: 'low', 'medium', 'high'
    """
    doc = fitz.open(path)
    output_path = os.path.join(UPLOAD_FOLDER, f"compressed_{uuid.uuid4()}.pdf")

    # Set scale factor for resolution reduction
    if level == "low":
        scale = 1.0  # no change
        deflate = False
    elif level == "medium":
        scale = 0.8
        deflate = True
    else:  # high
        scale = 0.5
        deflate = True

    # Create a new PDF with scaled pages
    new_doc = fitz.open()
    for page in doc:
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        new_page = new_doc.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(new_page.rect, pixmap=pix)

    new_doc.save(output_path, deflate=deflate)
    doc.close()
    new_doc.close()
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


def clear_uploads_folder(folder_path="uploads"):
    """
    Delete all files in the specified folder.
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            # Optional: delete subfolders as well
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

def edit_pdf(path, edit_type, content, x, y, page_number=1):
    """
    Edit a PDF by adding text, signature, or annotation.

    path: str - input PDF path
    edit_type: "add-text", "add-signature", "add-annotation"
    content: str - text or image path for signature
    x, y: int - coordinates for the edit
    page_number: int - 1-indexed page to edit (default: 1)
    """
    doc = fitz.open(path)
    output_path = os.path.join(UPLOAD_FOLDER, f"edited_{uuid.uuid4()}.pdf")
    
    # Ensure page_number is valid
    page_index = max(0, min(page_number - 1, len(doc) - 1))
    page = doc[page_index]

    if edit_type == "add-text":
        page.insert_text((x, y), content, fontsize=12)
    elif edit_type == "add-signature":
        # content should be path to signature image
        page.insert_text((x, y), content, fontsize=12, fontname="helv")
    elif edit_type == "add-annotation":
        page.add_text_annot((x, y), content)
    elif edit_type == "add-image":
        img_bytes = BytesIO(content.read())
        rect = fitz.Rect(x, y, x + 200, y + 200)
        page.insert_image(rect, stream=img_bytes)
    else:
        doc.close()
        raise ValueError("Invalid edit_type, must be 'add-text', 'add-signature', or 'add-annotation'")

    doc.save(output_path)
    doc.close()
    return output_path