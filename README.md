# 📄 ConvertingPDF Server

This is the **backend server** for the [ConvertingPDF web app](https://quick-doc-tool.onrender.com) — a tool that lets you merge, split, compress, edit, and convert PDF files to other formats.

The server is built with **Flask**, provides a REST API for PDF processing, and handles **user authentication**, **email verification**, and **conversion history tracking**.

## 🤝 Contributions

I contributed mainly to linking the **backend server** with the web app, handling authentication, and integrating PDF tools.

Frontend handled by my teammate: [Quick-Doc-Tool repo](https://github.com/itachi-555/quick-doc-tool).

## 📑 Table of Contents

- [⚙️ Features](#⚙️-features)
- [🛠️ Tech Stack](#🛠️-tech-stack)
- [📦 Setup](#📦-setup)
- [🔑 Authentication](#🔑-authentication)
- [📡 API Endpoints](#📡-api-endpoints)
  - [Merge PDFs](#1-merge-pdfs)
  - [Split PDF](#2-split-pdf)
  - [Compress PDF](#3-compress-pdf)
  - [PDF → Word](#4-pdf-→-word)
  - [PDF → JPG](#5-pdf-→-jpg)
  - [Edit PDF](#6-edit-pdf)
  - [List Conversions](#7-list-conversions)
  [📂 Project Structure](#📂-project-structure)

## ⚙️ Features

- 🔐 User authentication with JWT
- 📧 Email verification with expiration handling
- 🗂 Track user conversions in the database
- 📑 PDF operations:

  - Merge PDFs
  - Split PDFs
  - Compress PDFs
  - Convert PDF → Word (`.docx`)
  - Convert PDF → JPG (zipped images)
  - Edit PDFs (add text or images)

- ⏱ Rate limiting for security (`10 requests/minute`)

## 🛠️ Tech Stack

- **Backend Framework:** [![Flask](https://img.shields.io/badge/Flask-Backend-blue?logo=flask)](https://flask.palletsprojects.com/)
- **Database:** [![Supabase](https://img.shields.io/badge/Supabase-DB-blue?logo=supabase)](https://app.supabase.com/)
- **Auth:** JWT + bcrypt
- **Email:** Flask-Mail (SMTP)
- **File Handling:** PyPDF2 / pdf2docx / Pillow

## 📦 Setup

### Option 1: Run Locally with Python

1. **Clone the repo**

```bash
git clone https://github.com/itachi-555/convertingpdf-server.git
cd convertingpdf-server
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.yourmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_password
```

4. **Run the server**

```bash
python app.py
```

The server will start at:
`http://localhost:10000`

### Option 2: Run with Docker

1. **Build the Docker image**

```bash
docker build -t convertingpdf-server .
```

2. **Run the container**

```bash
docker run -d -p 10000:10000 --env-file .env convertingpdf-server
```

3. The server will be accessible at:
   `http://localhost:10000`

## 🔑 Authentication

Most routes require a **JWT Bearer Token**.

1. **Signup:** `POST /signup` → creates account & sends verification email
2. **Verify Email:** `GET /verify-email/<token>`
3. **Login:** `POST /login` → returns JWT token
4. **Delete Account:** `DELETE /delete`

Send the token in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

Also include `X-User-ID` in headers for PDF routes:

```
X-User-ID: <user_id>
```

## 📡 API Endpoints

### 1. Merge PDFs

```bash
curl -X POST http://localhost:10000/merge-pdf \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>" \
-F "files=@file1.pdf" \
-F "files=@file2.pdf"
```

**Response:**

```json
{
  "conversion_id": "uuid",
  "converted_filename": "file1.pdf_merged.pdf",
  "converted_file_size": 12345,
  "downloadUrl": "/downloads/file1.pdf_merged.pdf",
  "status": "completed",
  "message": "Conversion completed successfully"
}
```

### 2. Split PDF

```bash
curl -X POST http://localhost:10000/split-pdf \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>" \
-F "file=@document.pdf" \
-F "splitType=pages" \
-F "splitValue=2"
```

**Notes:**

- `splitType` accepted values:

  - `"pages"` → split the PDF every N pages
  - `"ranges"` → split the PDF using specific page ranges

- `splitValue` depends on `splitType`:
  - If `splitType="pages"`, provide a number of pages per split, e.g., `2`.
  - If `splitType="ranges"`, provide ranges as comma-separated `start-end` pairs, e.g., `"1-3,5-6"`.

**Response:**

```json
{
  "conversion_id": "uuid",
  "converted_filename": "document_split.zip",
  "converted_file_size": 54321,
  "downloadUrl": "/downloads/document_split.zip",
  "status": "completed",
  "message": "Conversion completed successfully"
}
```

### 3. Compress PDF

```bash
curl -X POST http://localhost:10000/compress-pdf \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>" \
-F "file=@document.pdf" \
-F "compressionLevel=high"
```

**Response:**

```json
{
  "conversion_id": "uuid",
  "converted_filename": "document_compressed.pdf",
  "converted_file_size": 12345,
  "downloadUrl": "/downloads/document_compressed.pdf",
  "status": "completed",
  "message": "Conversion completed successfully"
}
```

**Notes:**

- `compressionLevel` accepted values:
  - `"low"` → minimal compression, preserves quality
  - `"medium"` → balanced compression and file size
  - `"high"` → maximum compression, smaller file size but lower quality

### 4. PDF → Word

```bash
curl -X POST http://localhost:10000/pdf-to-word \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>" \
-F "file=@document.pdf"
```

**Response:**

```json
{
  "conversion_id": "uuid",
  "converted_filename": "document.docx",
  "converted_file_size": 23456,
  "downloadUrl": "/downloads/document.docx",
  "status": "completed",
  "message": "Conversion completed successfully"
}
```

### 5. PDF → JPG

```bash
curl -X POST http://localhost:10000/pdf-to-jpg \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>" \
-F "file=@document.pdf"
```

**Response:**

```json
{
  "conversion_id": "uuid",
  "converted_filename": "document_jpg.zip",
  "converted_file_size": 34567,
  "downloadUrl": "/downloads/document_jpg.zip",
  "status": "completed",
  "message": "Conversion completed successfully"
}
```

### 6. Edit PDF

```bash
curl -X POST http://localhost:10000/edit \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>" \
-F "file=@document.pdf" \
-F 'editData={"content":"Hello World","x":50,"y":100}' \
-F "editType=add-text"
```

**Notes:**

- `editType` accepted values:

  - `"add-text"` → add plain text to the PDF
  - `"add-signature"` → add a signature (image path or content)
  - `"add-annotation"` → add a text annotation
  - `"add-image"` → add an image (provide as file in `imageFile`)

- `editData` fields:
  - `content` → text content for `"add-text"`/`"add-signature"`/`"add-annotation"`; ignored for `"add-image"`
  - `x`, `y` → coordinates (in points) on the page for placement
  - `page_number` (optional) → 1-indexed page to edit (default: `1`)

**Response:**

```json
{
  "conversion_id": "uuid",
  "converted_filename": "document_edited.pdf",
  "converted_file_size": 23456,
  "downloadUrl": "/downloads/document_edited.pdf",
  "status": "completed",
  "message": "Conversion completed successfully"
}
```

### 7. List Conversions

```bash
curl -X GET http://localhost:10000/conversions \
-H "Authorization: Bearer <token>" \
-H "X-User-ID: <user_id>"
```

**Response:**

```json
{
  "data": [
    {
      "conversion_id": "uuid",
      "converted_filename": "document_edited.pdf",
      "conversion_type": "edit",
      "file_size": 23456,
      "downloadUrl": "/downloads/document_edited.pdf",
      "status": "completed"
    }
  ]
}
```

## 📂 Project Structure

```
convertingpdf/
├── app.py           # Main Flask server with endpoints
├── auth.py          # Email verification helpers
├── database.py      # Supabase integration
├── tools.py         # PDF processing functions (merge, split, compress, convert)
├── pages.py         # HTML templates & verification messages
├── Dockerfile       # Container deployment
├── requirements.txt # Python dependencies
└── README.md        # This file
```
