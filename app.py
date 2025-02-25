from flask import Flask, Response, render_template, request, redirect, url_for, session, flash
import pyaudio
import subprocess
import os
import json
from functools import wraps
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# Get secret key from environment or use a default (but prefer environment)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configuration - load from config file or use defaults from environment variables
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file exists but has issues, use environment variables
            pass
    
    # Default configuration from environment variables
    return {
        'host': os.environ.get('HOST', '0.0.0.0'),
        'port': int(os.environ.get('PORT', 5000)),
        'audio_source': os.environ.get('AUDIO_SOURCE', 'microphone'),  # 'microphone' or 'url'
        'stream_url': os.environ.get('STREAM_URL', ''),
        'admin_username': os.environ.get('ADMIN_USERNAME', 'admin'),
        'admin_password': os.environ.get('ADMIN_PASSWORD', 'password'),
        'chunk_size': int(os.environ.get('CHUNK_SIZE', 1024)),
        'channels': int(os.environ.get('CHANNELS', 1)),
        'rate': int(os.environ.get('SAMPLE_RATE', 44100)),
        'format': pyaudio.paInt16,
        'debug': os.environ.get('DEBUG', 'false').lower() == 'true'
    }

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            # Filter out non-serializable items like format
            serializable_config = {k: v for k, v in config.items() if k != 'format'}
            json.dump(serializable_config, f, indent=2)
        return True
    except IOError:
        return False

# Initialize config
config = load_config()

# Audio setup
p = None
microphone_stream = None
ffmpeg_process = None

def init_audio():
    global p, microphone_stream, ffmpeg_process
    
    # Close existing resources if any
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
    
    if microphone_stream:
        microphone_stream.stop_stream()
        microphone_stream.close()
        microphone_stream = None
    
    if p:
        p.terminate()
    
    # Initialize new audio resources based on current config
    if config['audio_source'] == 'microphone':
        p = pyaudio.PyAudio()
        microphone_stream = p.open(
            format=config['format'],
            channels=config['channels'],
            rate=config['rate'],
            input=True,
            frames_per_buffer=config['chunk_size']
        )
    else:
        # URL-based streaming is initialized on-demand in generate_audio_stream
        pass

# Initialize audio on startup
init_audio()

# Admin authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_audio_stream():
    global ffmpeg_process

    if config['audio_source'] == 'url' and config['stream_url']:
        stream_url = config['stream_url']
        command = ["ffmpeg", "-i", stream_url, "-vn"]  # Disable video

        # Special handling for different streaming protocols
        if stream_url.startswith("rtsp"):
            command.insert(1, "-rtsp_transport")
            command.insert(2, "tcp")  # Ensure TCP mode for RTSP
        elif stream_url.startswith("rtmp"):
            command.insert(1, "-timeout")
            command.insert(2, "5000000")  # Set timeout for RTMP streams
        elif stream_url.endswith(".m3u8"):  # HLS stream
            command.insert(1, "-protocol_whitelist")
            command.insert(2, "file,http,https,tcp,tls")  # Ensure HLS works
        elif "webrtc" in stream_url:
            command.insert(1, "-protocol_whitelist")
            command.insert(2, "rtp,udp,ice,stun,tcp,tls")  # Ensure WebRTC support
        elif stream_url.startswith("http") and (".mp3" in stream_url or ".aac" in stream_url):
            command.insert(1, "-reconnect")
            command.insert(2, "1")  # Reconnect option for HTTP radio streams
        
        # Audio output settings
        command += [
            "-f", "wav",  # Output format (do NOT use "hls" or "flv" here)
            "-acodec", "pcm_s16le",
            "-ar", str(config['rate']),
            "-ac", str(config['channels']),
            "pipe:1"
        ]

        print(f"Running FFmpeg command: {' '.join(command)}")  # Debugging line

        ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            while True:
                data = ffmpeg_process.stdout.read(config['chunk_size'])
                if not data:
                    break
                yield data
        except Exception as e:
            print(f"FFmpeg Error: {str(e)}")
            if ffmpeg_process:
                ffmpeg_process.kill()
                ffmpeg_process = None

# Routes
@app.route('/audio')
def audio_stream():
    return Response(generate_audio_stream(), mimetype='audio/wav')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == config['admin_username'] and password == config['admin_password']:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials. Please try again.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        config['audio_source'] = request.form.get('audio_source')
        config['stream_url'] = request.form.get('stream_url').strip()  # Ensure no spaces
        config['port'] = int(request.form.get('port'))
        config['rate'] = int(request.form.get('rate'))
        config['channels'] = int(request.form.get('channels'))

        if save_config(config):
            flash('Configuration updated successfully!')
        else:
            flash('Failed to save configuration.')

        init_audio()

        return redirect(url_for('admin'))

    return render_template('admin.html', config=config)


@app.route('/check-stream')
@login_required
def check_stream():
    """Test if stream URL is valid and supports audio."""
    stream_url = config.get('stream_url', '')

    if not stream_url:
        return Response(json.dumps({"error": "No stream URL configured"}), mimetype='application/json')

    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a",  # Ensure we're checking the audio stream
            "-show_entries", "stream=codec_type",
            "-of", "json",
            stream_url
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        
        return Response(result.stdout, mimetype='application/json')

    except Exception as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json')


# Set up WebSocket for audio streaming
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('request_audio')
def stream_audio():
    """Handle WebSocket audio stream request"""
    for chunk in generate_audio_stream():
        socketio.emit('audio_data', chunk)

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Run the app with WebSocket support
    socketio.run(app, debug=config['debug'], host=config['host'], port=config['port'])
