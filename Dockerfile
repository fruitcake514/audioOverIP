FROM python:3.9-slim

# Install system dependencies (including FFmpeg, ALSA, and PortAudio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    libsndfile1 \
    libavcodec-extra \
    alsa-utils \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application files
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

# Run the Flask app using Gunicorn (better than flask run)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
