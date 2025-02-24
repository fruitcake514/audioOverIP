import subprocess
import socket
import threading

# Set up RTSP stream URL
RTSP_URL = "rtsp://your-rtsp-stream-url"

# Audio streaming parameters
HOST = '0.0.0.0'
PORT = 12345

def stream_audio_from_rtsp():
    # Set up the FFmpeg command to capture audio from the RTSP stream
    command = [
        "ffmpeg",
        "-i", RTSP_URL,        # Input RTSP stream
        "-f", "wav",           # Output format
        "-acodec", "pcm_s16le", # Audio codec for raw PCM audio
        "-ar", "44100",        # Set audio sample rate
        "-ac", "1",            # Mono channel
        "pipe:1"               # Output to stdout
    ]
    
    # Start the FFmpeg process to capture the RTSP stream
    ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Create socket for streaming
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))

    print("Streaming RTSP audio...")

    while True:
        data = ffmpeg_process.stdout.read(1024)  # Read data from FFmpeg output
        if data:
            s.sendto(data, (HOST, PORT))  # Send data to the receiver

# Run the streaming in a separate thread
stream_thread = threading.Thread(target=stream_audio_from_rtsp)
stream_thread.start()
