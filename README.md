# 📄 Convertingpdf — PDF Processing API

**Convertingpdf** is a Python-based Flask server providing ⚡ fast PDF operations—including merge, split, compress, convert (PDF→Word, PDF→JPG)—for the frontend at [convertingpdf web app](https://preview--quick-doc-tool.lovable.app/).  
It handles file uploads, processes them, and returns results—all while enforcing rate limits ⏱️ and clean packaging 🗂️.


## 🗂️ Table of Contents
- [✨ Overview](#-overview)
- [🚀 Features](#-features)
- [⏱️ Rate Limiting](#️-rate-limiting)
- [🛠️ Setup & Hosting](#️-setup--hosting)
- [💻 Using the API (Client POV)](#-using-the-api-client-pov)
- [💡 Example cURL Requests](#-example-curl-requests)
- [📁 Project Structure](#-project-structure)

## ✨ Overview

This server powers the backend of **Convertingpdf**—a web app offering PDF utilities like merging, splitting, OCR-free conversions, and compression.  
Built with Flask and libraries like **PyPDF2**, **pdf2docx**, and **PyMuPDF**, it supports upload handling and rate limiting to ensure smooth operation.

## 🚀 Features

- **Endpoints**:
  - `POST /merge-pdf` → Merge multiple PDFs into one 📎
  - `POST /split-pdf` → Split PDFs into pages; returns zipped pages 🗜️
  - `POST /compress-pdf` → Reduce file size with optimization 🗜️
  - `POST /pdf-to-word` → Convert PDF to `.docx` 📝
  - `POST /pdf-to-jpg` → Export PDF pages as JPGs in a ZIP 🖼️

- **Rate Limit**: Each endpoint is limited to **10 requests/minute per client IP** ⏱️.

- **Zipped Downloads** for multi-file responses (split / JPG conversions) 📦.

## 🛠️ Setup & Hosting

1. **Clone & install dependencies**:
   ```bash
   git clone <repo-url>
   cd convertingpdf
   pip install -r requirements.txt
   ```

2. **Install system dependencies** (for PDF→JPG conversion):
   ```bash
   sudo apt-get update
   sudo apt-get install -y poppler-utils
   ```

3. **Run locally**:
   ```bash
   python app.py
   ```
   Flask will start on `http://127.0.0.1:5000` 🚀

## 💻 Using the API 

All endpoints expect **HTTP POST** with multipart form data. Responses are downloadable files.

### 1️⃣ Merge PDFs
- **URL**: `POST /merge-pdf`
- **Form Param**: `files` — multiple PDFs
- **Response**: single merged PDF (`application/pdf`) 📎

### 2️⃣ Split PDF
- **URL**: `POST /split-pdf`
- **Param**: `file` — PDF
- **Response**: ZIP with split pages 📦

### 3️⃣ Compress PDF
- **URL**: `POST /compress-pdf`
- **Param**: `file` — PDF
- **Response**: compressed PDF 🗜️

### 4️⃣ PDF → Word
- **URL**: `POST /pdf-to-word`
- **Param**: `file` — PDF
- **Response**: `.docx` Word file 📝

### 5️⃣ PDF → JPG
- **URL**: `POST /pdf-to-jpg`
- **Param**: `file` — PDF
- **Response**: ZIP of JPG images 🖼️

## 💡 Example cURL Requests

```bash
# Merge PDFs
curl -F "files=@a.pdf" -F "files=@b.pdf" http://localhost:5000/merge-pdf --output merged.pdf

# Split PDF
curl -F "file=@input.pdf" http://localhost:5000/split-pdf --output split_pages.zip

# Compress PDF
curl -F "file=@input.pdf" http://localhost:5000/compress-pdf --output compressed.pdf

# PDF to Word
curl -F "file=@input.pdf" http://localhost:5000/pdf-to-word --output output.docx

# PDF to JPG
curl -F "file=@input.pdf" http://localhost:5000/pdf-to-jpg --output pages.zip
```

## 📁 Project Structure

```
convertingpdf/
├── app.py                 # Flask server with endpoints
├── requirements.txt       # Python dependencies
└── README.md
```