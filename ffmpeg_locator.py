import os
import platform
import shutil
import subprocess

def find_ffmpeg_executable():
    """Find the FFmpeg executable path"""
    # Check current directory first
    exe_ext = ".exe" if platform.system() == "Windows" else ""
    current_dir_ffmpeg = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"ffmpeg{exe_ext}")
    
    if os.path.exists(current_dir_ffmpeg):
        return current_dir_ffmpeg
    
    # Check in PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path
    
    # On Windows, check common installation locations
    if platform.system() == "Windows":
        common_locations = [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe")
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                return location
    
    # On macOS, check Homebrew location
    if platform.system() == "Darwin":
        brew_location = "/usr/local/bin/ffmpeg"
        if os.path.exists(brew_location):
            return brew_location
    
    return None

def find_ffprobe_executable():
    """Find the FFprobe executable path"""
    # Check current directory first
    exe_ext = ".exe" if platform.system() == "Windows" else ""
    current_dir_ffprobe = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"ffprobe{exe_ext}")
    
    if os.path.exists(current_dir_ffprobe):
        return current_dir_ffprobe
    
    # Check in PATH
    ffprobe_in_path = shutil.which("ffprobe")
    if ffprobe_in_path:
        return ffprobe_in_path
    
    # On Windows, check common installation locations
    if platform.system() == "Windows":
        common_locations = [
            r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
            r"C:\ffmpeg\bin\ffprobe.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffprobe.exe")
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                return location
    
    # On macOS, check Homebrew location
    if platform.system() == "Darwin":
        brew_location = "/usr/local/bin/ffprobe"
        if os.path.exists(brew_location):
            return brew_location
    
    return None

def check_ffmpeg_installed():
    """Check if FFmpeg is installed and available"""
    ffmpeg_path = find_ffmpeg_executable()
    ffprobe_path = find_ffprobe_executable()
    
    if ffmpeg_path and ffprobe_path:
        try:
            # Test FFmpeg
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                return False, "FFmpeg is installed but not working properly"
                
            # Test FFprobe
            result = subprocess.run(
                [ffprobe_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                return False, "FFprobe is installed but not working properly"
                
            return True, "FFmpeg and FFprobe are available"
        except Exception as e:
            return False, f"Error testing FFmpeg: {e}"
    else:
        missing = []
        if not ffmpeg_path:
            missing.append("FFmpeg")
        if not ffprobe_path:
            missing.append("FFprobe")
        return False, f"Missing: {', '.join(missing)}"
