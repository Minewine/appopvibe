FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create reports and feedback directories
RUN mkdir -p reports feedback flask_session && chmod -R 755 reports feedback flask_session

# Expose port
EXPOSE 5000

# Run gunicorn with 4 workers
CMD gunicorn --bind 0.0.0.0:$PORT --workers=4 --timeout=120 "app:app"
