FROM python:3.9-slim

# Install system dependencies (including portaudio, ffmpeg, and others)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt to container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files into container
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000 \
    ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=password \
    STREAM_URL=""

# Expose port for the application
EXPOSE 5000

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
