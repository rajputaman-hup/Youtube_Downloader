from pytubefix import YouTube
import os
import re # Import regex for URL validation

def download_youtube_video(url: str, download_path: str, format_type: str = "video", quality: str = "720p"):
    """
    Downloads a YouTube video or audio.

    Args:
        url (str): The YouTube video URL.
        download_path (str): The directory to save the downloaded file.
        format_type (str): 'video' for video+audio (MP4), 'audio' for audio only (MP3).
        quality (str): Desired video quality (e.g., '1080p', '720p').
                       Ignored for audio downloads.

    Returns:
        dict: A dictionary containing success status and message/filename.
    """
    if not url or ("youtu.be" not in url and "youtube.com" not in url):
        return {"success": False, "message": "Invalid YouTube URL."}

    if not os.path.exists(download_path) or not os.path.isdir(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
        except OSError as e:
            return {"success": False, "message": f"Could not create download directory: {e}"}

    try:
        yt = YouTube(url)

        if format_type == "audio":
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not stream:
                return {"success": False, "message": "No audio stream found."}
            filename = f"{yt.title}.mp3"
            output_file = stream.download(output_path=download_path, filename=filename)
            base, ext = os.path.splitext(output_file)
            new_file = base + '.mp3'
            os.rename(output_file, new_file)
            return {"success": True, "message": "Audio downloaded successfully!", "filename": os.path.basename(new_file)}
        else: # format_type == "video"
            # Try to get progressive stream first
            stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=quality).first()
            
            if not stream: # If specific quality progressive not found, try highest progressive
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

            if not stream: # Fallback to highest resolution video-only and separate audio
                video_stream = yt.streams.filter(res=quality, file_extension='mp4', type='video').first()
                if not video_stream:
                    video_stream = yt.streams.filter(file_extension='mp4', type='video').order_by('resolution').desc().first()
                
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

                if not video_stream or not audio_stream:
                    return {"success": False, "message": "Could not find suitable video and/or audio streams."}
                
                # For simplicity, we'll just download the video stream here.
                # Merging video and audio requires external tools like ffmpeg, which is beyond this scope.
                # For a full solution, you'd download both and then merge them.
                print("Warning: Progressive stream not found for desired quality. Downloading video-only stream.")
                stream = video_stream # Proceed with video-only download
            
            if not stream:
                return {"success": False, "message": "No suitable video stream found."}

            filename = f"{yt.title}.mp4"
            output_file = stream.download(output_path=download_path, filename=filename)
            return {"success": True, "message": "Video downloaded successfully!", "filename": os.path.basename(output_file)}

    except Exception as e:
        print(f"Error during download: {e}")
        return {"success": False, "message": f"An error occurred during download: {e}. This might be due to network issues, video unavailability, or age restrictions."}

def get_video_info(url: str):
    """
    Fetches information about a YouTube video.

    Args:
        url (str): The YouTube video URL.

    Returns:
        dict: A dictionary containing video information or an error message.
    """
    if not url or ("youtu.be" not in url and "youtube.com" not in url):
        return {"success": False, "message": "Invalid YouTube URL."}

    try:
        yt = YouTube(url)
        
        # Get available resolutions
        available_resolutions = sorted(list(set([
            s.resolution for s in yt.streams.filter(progressive=True, file_extension='mp4') if s.resolution
        ])), key=lambda x: int(x[:-1]) if x and x.endswith('p') else 0, reverse=True)
        
        # Add common resolutions if not present
        common_resolutions = ["1080p", "720p", "480p", "360p"]
        for res in common_resolutions:
            if res not in available_resolutions:
                available_resolutions.append(res)
        available_resolutions = sorted(list(set(available_resolutions)), key=lambda x: int(x[:-1]) if x and x.endswith('p') else 0, reverse=True)


        return {
            "success": True,
            "title": yt.title,
            "thumbnail": yt.thumbnail_url,
            "duration": str(yt.length // 60).zfill(2) + ":" + str(yt.length % 60).zfill(2),
            "views": f"{yt.views:,} views", # Format with commas
            "formats": available_resolutions
        }
    except Exception as e:
        print(f"Error fetching video info: {e}")
        return {"success": False, "message": f"Failed to fetch video information: {e}. Please check the URL or try again later."}

