# 📄 Convertingpdf — PDF Processing API

**Convertingpdf** is a Python Flask server providing ⚡ fast PDF operations—including merge, split, compress, convert (PDF→Word, PDF→JPG)—for the frontend at [Convertingpdf Web App](https://preview--quick-doc-tool.lovable.app/).
It handles file uploads, processes them, and returns results—all while enforcing rate limits ⏱️ and clean packaging 🗂️.
It also includes **email verification**, **JWT authentication**, and account management features.


## 🗂️ Table of Contents

* [✨ Overview](#-overview)
* [🚀 Features](#-features)
* [🛠️ Setup & Hosting](#️-setup--hosting)
* [💻 Using the API](#-using-the-api)
* [💡 Example cURL Requests](#-example-curl-requests)
* [📁 Project Structure](#-project-structure)


## ✨ Overview

This server powers the backend of **Convertingpdf**—a web app offering PDF utilities like merging, splitting, OCR-free conversions, and compression.
Built with Flask and libraries like **PyPDF2**, **pdf2docx**, and **PyMuPDF**, it supports:

* Upload handling
* JWT authentication & email verification
* Rate limiting
* ZIP packaging for multi-file outputs


## 🚀 Features

* **Endpoints**:

| Endpoint                | Method | Auth | Description                                    |
|-- | |- |- |
| `/merge-pdf`            | POST   | ✅    | Merge multiple PDFs into one 📎                |
| `/split-pdf`            | POST   | ✅    | Split PDF into pages; returns ZIP 🗜️          |
| `/compress-pdf`         | POST   | ✅    | Compress PDF file 🗜️                          |
| `/pdf-to-word`          | POST   | ✅    | Convert PDF to Word `.docx` 📝                 |
| `/pdf-to-jpg`           | POST   | ✅    | Convert PDF pages to JPG in ZIP 🖼️            |
| `/signup`               | POST   | ❌    | Register new user & send verification email ✉️ |
| `/verify-email/<token>` | GET    | ❌    | Verify user email via token 🔑                 |
| `/login`                | POST   | ❌    | User login & receive JWT 🔐                    |
| `/delete`               | DELETE | ✅    | Delete user account 🗑️                        |

* **Rate Limit**: Each endpoint limited to **10 requests/minute per IP** ⏱️
* **Zipped Downloads** for multi-file responses (split / JPG conversions) 📦
* **JWT Auth** required for all PDF endpoints
* **Email Verification** required before login


## 🛠️ Setup & Hosting

### 1️⃣ Clone & install dependencies

```bash
git clone <repo-url>
cd convertingpdf
pip install -r requirements.txt
```

### 2️⃣ Install system dependencies (PDF→JPG conversion)

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils libgl1 libglib2.0-0 zip
```

### 3️⃣ Run locally

```bash
python app.py
```

Flask will start on `http://127.0.0.1:5000` 🚀

### 4️⃣ Using Docker

```bash
docker build -t convertingpdf .
docker run -p 5000:10000 convertingpdf
```

> Flask listens on `0.0.0.0:$PORT` (default `10000`) for cloud deployment.


## 💻 Using the API

All endpoints expect **HTTP POST** with multipart form data (except `/verify-email`). Responses are downloadable files or JSON.

### PDF Endpoints

1️⃣ **Merge PDFs**

* **URL**: `POST /merge-pdf`
* **Auth**: JWT required
* **Form Param**: `files` — multiple PDFs
* **Response**: Merged PDF 📎

2️⃣ **Split PDF**

* **URL**: `POST /split-pdf`
* **Auth**: JWT required
* **Param**: `file` — PDF
* **Response**: ZIP of split pages 📦

3️⃣ **Compress PDF**

* **URL**: `POST /compress-pdf`
* **Auth**: JWT required
* **Param**: `file` — PDF
* **Response**: Compressed PDF 🗜️

4️⃣ **PDF → Word**

* **URL**: `POST /pdf-to-word`
* **Auth**: JWT required
* **Param**: `file` — PDF
* **Response**: Word `.docx` 📝

5️⃣ **PDF → JPG**

* **URL**: `POST /pdf-to-jpg`
* **Auth**: JWT required
* **Param**: `file` — PDF
* **Response**: ZIP of JPG images 🖼️

### Auth Endpoints

* **Sign Up**: `POST /signup` → JSON `{ "email": "...", "password": "..." }`
* **Verify Email**: `GET /verify-email/<token>` → shows HTML verification page
* **Login**: `POST /login` → JSON `{ "email": "...", "password": "..." }` → returns JWT
* **Delete Account**: `DELETE /delete` → JWT required, JSON `{ "email": "..." }`

> ⚠️ All JWT-protected endpoints require `Authorization` header:

```http
Authorization: <jwt-token>
```


## 💡 Example cURL Requests

```bash
# Merge PDFs
curl -F "files=@a.pdf" -F "files=@b.pdf" http://localhost:5000/merge-pdf \
  -H "Authorization: <jwt>" --output merged.pdf

# Split PDF
curl -F "file=@input.pdf" http://localhost:5000/split-pdf \
  -H "Authorization: <jwt>" --output split_pages.zip

# Compress PDF
curl -F "file=@input.pdf" http://localhost:5000/compress-pdf \
  -H "Authorization: <jwt>" --output compressed.pdf

# PDF to Word
curl -F "file=@input.pdf" http://localhost:5000/pdf-to-word \
  -H "Authorization: <jwt>" --output output.docx

# PDF to JPG
curl -F "file=@input.pdf" http://localhost:5000/pdf-to-jpg \
  -H "Authorization: <jwt>" --output pages.zip

# Sign Up
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'
```


## 📁 Project Structure

```
convertingpdf/
├── app.py           # Main Flask server with endpoints
├── auth.py          # Email verification helpers
├── database.py      # Supabase integration & JWT helpers
├── tools.py         # PDF processing functions (merge, split, compress, convert)
├── pages.py         # HTML templates & verification messages
├── Dockerfile       # Container deployment
├── requirements.txt # Python dependencies
└── README.md        # This file
```

