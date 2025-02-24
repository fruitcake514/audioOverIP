# Build Stage
FROM python:3.9-slim AS builder

# Install dependencies required for building
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file and install dependencies in the builder stage
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime Stage
FROM python:3.9-slim

# Install dependencies required at runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /app /app

# Copy the application files
COPY . .

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000 \
    ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=password \
    STREAM_URL=""

# Install flask in runtime image (to be absolutely sure it's installed)
RUN pip install --no-cache-dir Flask

# Expose the necessary port
EXPOSE 5000

# Start Flask application using the flask command
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
