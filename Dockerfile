# Build Stage
FROM python:3.9-slim AS builder

RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime Stage
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app /app
COPY . .

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000 \
    ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=password \
    STREAM_URL=""

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
