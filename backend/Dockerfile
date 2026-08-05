# Use official lightweight Python 3.12 slim image
FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable unbuffered logging stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV PORT=5000

# Set working directory
WORKDIR /app

# Install system dependencies required for FAISS, psycopg2, OpenBLAS, and PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libopenblas-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for layer caching
COPY requirements.txt .

# Install Python dependencies ensuring NumPy 1.26.4 compatibility
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create required persistent data and log directories
RUN mkdir -p data/raw data/extracted data/processed data/chunks data/embeddings data/faiss data/metadata data/evaluation logs

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Expose Render PORT
EXPOSE ${PORT}

# Set entrypoint to run migrations and launch Gunicorn
ENTRYPOINT ["./docker-entrypoint.sh"]
