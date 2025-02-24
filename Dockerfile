FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create templates directory if it doesn't exist
RUN mkdir -p templates

# Create environment for config
ENV PORT=5000 \
    ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=password \
    STREAM_URL=""

# Expose port
EXPOSE ${PORT}

# Run the application
CMD ["python", "app.py"]
