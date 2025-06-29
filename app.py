from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time # For simulating progress
import threading # For handling downloads in a non-blocking way
import uuid # For unique download IDs

# Import your download logic
from youtube_downloader import download_youtube_video, get_video_info

app = Flask(__name__, static_folder='static')
CORS(app) # Enable CORS for all routes

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Dictionary to store download progress and status
# {download_id: {'status': 'pending'/'downloading'/'completed'/'failed', 'progress': 0-100, 'filename': None, 'error': None}}
download_statuses = {}

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/fetch_info', methods=['POST'])
def fetch_info():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"success": False, "message": "URL is required."}), 400

    info = get_video_info(video_url)
    return jsonify(info)

def run_download_in_thread(download_id, video_url, format_type, quality):
    """Helper function to run download in a separate thread."""
    download_statuses[download_id] = {'status': 'downloading', 'progress': 0, 'filename': None, 'error': None}
    
    # Simulate progress updates (replace with actual progress from pytubefix if available)
    # pytubefix has on_progress_callback, which would be ideal here.
    # For now, we'll just simulate.
    for i in range(1, 101):
        if download_statuses[download_id]['status'] == 'failed': # Allow early exit if cancelled/failed
            break
        download_statuses[download_id]['progress'] = i
        time.sleep(0.1) # Simulate work

    result = download_youtube_video(video_url, DOWNLOAD_FOLDER, format_type, quality)
    
    if result['success']:
        download_statuses[download_id]['status'] = 'completed'
        download_statuses[download_id]['filename'] = result['filename']
        download_statuses[download_id]['progress'] = 100
    else:
        download_statuses[download_id]['status'] = 'failed'
        download_statuses[download_id]['error'] = result['message']
        download_statuses[download_id]['progress'] = 0 # Reset progress on failure

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')
    format_type = data.get('format', 'video')
    quality = data.get('quality', '720p')

    if not video_url:
        return jsonify({"success": False, "message": "URL is required."}), 400

    download_id = str(uuid.uuid4())
    
    # Start the download in a new thread to avoid blocking the main Flask thread
    thread = threading.Thread(target=run_download_in_thread, args=(download_id, video_url, format_type, quality))
    thread.start()

    return jsonify({"success": True, "message": "Download started.", "download_id": download_id})

@app.route('/download_status/<download_id>', methods=['GET'])
def get_download_status(download_id):
    status = download_statuses.get(download_id, {'status': 'not_found', 'progress': 0, 'filename': None, 'error': None})
    return jsonify(status)

@app.route('/downloads/<filename>')
def serve_downloaded_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

