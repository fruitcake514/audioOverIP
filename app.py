from flask import Flask, Response
import pyaudio
import subprocess
import os  # For environment variable handling

app = Flask(__name__)

HOST = '0.0.0.0'

# Get the port from the environment variable (default to 5000 if not set)
PORT = int(os.environ.get('PORT', 5000))

# Get RTSP stream URL from the environment (default to None if not set)
RTSP_URL = os.environ.get('RTSP_URL', None)  # None if RTSP URL is not set

# Audio parameters for microphone capture
CHUNK_SIZE = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
CHANNELS = 1  # Mono audio
RATE = 44100  # Sample rate (44.1 kHz)

# Initialize PyAudio for microphone input
p = pyaudio.PyAudio()
microphone_stream = p.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK_SIZE)

# Audio streaming function to capture and stream audio
def generate_audio_stream():
    if RTSP_URL:
        # If RTSP stream URL is provided, use ffmpeg to capture the RTSP stream
        command = [
            "ffmpeg",
            "-i", RTSP_URL,  # Input RTSP stream
            "-vn",  # Disable video (we want only audio)
            "-f", "wav",     # Output format (WAV)
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

    else:
        # If RTSP stream is not provided, capture from the microphone
        while True:
            data = microphone_stream.read(CHUNK_SIZE)  # Read from microphone input stream
            if data:
                yield data  # Stream data to client (HTTP)

# Route for serving the audio stream
@app.route('/audio')
def audio_stream():
    return Response(generate_audio_stream(), content_type='audio/wav')

# Route for serving the index.html file
@app.route('/')
def home():
    return app.send_static_file('index.html')  # Flask will look in /static/ directory for this file

if __name__ == '__main__':
    # Use dynamic port from environment
    app.run(debug=True, host=HOST, port=PORT)
