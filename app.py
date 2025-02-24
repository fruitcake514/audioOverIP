from flask import Flask, Response
import pyaudio
import socket
import subprocess

app = Flask(__name__)

HOST = '0.0.0.0'
PORT = 12345

# RTSP stream URL (optional)
RTSP_URL = "rtsp://your-rtsp-stream-url"

# Audio streaming function to capture and stream audio
def generate_audio_stream():
    command = [
        "ffmpeg",
        "-i", RTSP_URL,  # Input RTSP stream (optional)
        "-f", "wav",     # Output format
        "-acodec", "pcm_s16le",  # Audio codec for raw PCM audio
        "-ar", "44100",  # Set audio sample rate
        "-ac", "1",      # Mono channel
        "pipe:1"         # Output to stdout (used for streaming)
    ]

    ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        data = ffmpeg_process.stdout.read(1024)  # Read from FFmpeg
        if data:
            yield data  # Stream data to client (HTTP)

# Route for serving the audio stream
@app.route('/audio')
def audio_stream():
    return Response(generate_audio_stream(), content_type='audio/wav')

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
