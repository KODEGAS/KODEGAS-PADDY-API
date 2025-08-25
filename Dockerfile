# Use official lightweight Python image
FROM python:3.11.4-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system dependencies needed for TensorFlow, Pillow, and OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpng-dev \
    libjpeg-dev \
    zlib1g-dev \
    gcc \
    libgl1-mesa-glx \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Create non-root user for security first
RUN useradd --create-home --shell /bin/bash app

# Copy requirements and install as non-root user
COPY --chown=app:app requirements.txt .
USER app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application code as non-root user
COPY --chown=app:app . .

# Add the user's local bin to the PATH
ENV PATH="/home/app/.local/bin:${PATH}"

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application with Gunicorn using the external config
CMD ["gunicorn", "-c", "gunicorn_conf.py", "main:app"]
