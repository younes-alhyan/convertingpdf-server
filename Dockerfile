# Use official Python slim image
FROM python:3.11-slim

# Install system dependencies (poppler for pdf->jpg, pillow dependencies, zip)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render uses $PORT)
ENV PORT=10000
EXPOSE $PORT

# Run the Flask app
CMD ["python", "app.py"]
