import os
import platform
import sys
import shutil
import subprocess
import requests
import zipfile
import io
import tempfile
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def get_app_directory():
    """Get the application directory path
    
    Returns:
        str: Path to the application directory
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        return os.path.dirname(sys.executable)
    else:
        # Running in development mode
        return os.path.dirname(os.path.abspath(__file__))

def find_executable(name):
    """Find the path to a specified executable (ffmpeg or ffprobe)
    
    Args:
        name (str): Either 'ffmpeg' or 'ffprobe'
        
    Returns:
        str or None: Path to the executable, or None if not found
    """
    if name not in ['ffmpeg', 'ffprobe']:
        raise ValueError("Name must be either 'ffmpeg' or 'ffprobe'")
        
    # Get executable extension for current platform
    exe_ext = ".exe" if platform.system() == "Windows" else ""
    exe_name = f"{name}{exe_ext}"
    
    # Check in application's bin directory first (for downloaded FFmpeg)
    app_dir = get_app_directory()
    
    # Bin directory path
    app_bin_path = os.path.join(app_dir, "bin", exe_name)
    if os.path.exists(app_bin_path):
        return app_bin_path
    
    # Check current directory
    current_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name)
    if os.path.exists(current_dir_path):
        return current_dir_path
    
    # Check in PATH
    in_path = shutil.which(name)
    if in_path:
        return in_path
    
    # On Windows, check common installation locations
    if platform.system() == "Windows":
        common_locations = [
            os.path.join(r"C:\Program Files\ffmpeg\bin", exe_name),
            os.path.join(r"C:\ffmpeg\bin", exe_name),
            os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", exe_name)
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                return location
    
    # On macOS, check Homebrew locations
    if platform.system() == "Darwin":
        brew_locations = [
            f"/usr/local/bin/{name}",
            f"/opt/homebrew/bin/{name}"
        ]
        for location in brew_locations:
            if os.path.exists(location):
                return location
    
    return None

def find_ffmpeg_executable():
    """Find the FFmpeg executable path"""
    return find_executable('ffmpeg')

def find_ffprobe_executable():
    """Find the FFprobe executable path"""
    return find_executable('ffprobe')

def check_ffmpeg_installed():
    """Check if FFmpeg is installed and available
    
    Returns:
        tuple: (bool, str) - Success status and message
    """
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

def download_with_retry(url, max_retries=3):
    """Download a file with retry capability
    
    Args:
        url (str): URL to download
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        requests.Response: Response object from the download
        
    Raises:
        Exception: If download fails after all retries
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, IOError) as e:
            if attempt < max_retries - 1:
                console.print(f"Download failed, retrying ({attempt+1}/{max_retries})...")
                time.sleep(2)  # Wait before retry
            else:
                raise e
                
def verify_binary_executable(path):
    """Verify that a binary is executable
    
    Args:
        path (str): Path to the binary file
        
    Returns:
        bool: True if executable, False otherwise
    """
    if not os.path.exists(path):
        return False
        
    if platform.system() in ["Linux", "Darwin"]:
        # Check if the file has execute permission
        return os.access(path, os.X_OK)
    else:
        # On Windows, just check if the file exists
        return True
                
def download_ffmpeg_to_app_dir():
    """Download FFmpeg binaries to the application directory
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Get the application directory
    app_dir = get_app_directory()
    
    bin_dir = os.path.join(app_dir, "bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    
    system = platform.system()
    
    # Only support Windows for now
    if system != "Windows":
        console.print("[bold #f38ba8]❌ Currently only Windows is supported for automatic FFmpeg installation.[/bold #f38ba8]")
        console.print("[#89dceb]Please install FFmpeg manually:[/#89dceb]")
        console.print("- macOS: Run 'brew install ffmpeg'")
        console.print("- Linux: Run 'sudo apt install ffmpeg' or use your package manager")
        return False
    
    arch = platform.machine().lower()
    console.print(f"[bold #89b4fa]Downloading FFmpeg for Windows ({arch})[/bold #89b4fa]")
    console.print(f"[#89dceb]Target directory: {bin_dir}[/#89dceb]\n")
    
    # Check if we already have working binaries installed
    ffmpeg_installed, _ = check_ffmpeg_installed()
    if ffmpeg_installed:
        console.print("[bold #a6e3a1]✅ FFmpeg is already installed and working.[/bold #a6e3a1]")
        return True
    
    try:
        # For Windows - smaller essential build
        url = "https://github.com/GyanD/codexffmpeg/releases/download/2025-03-31-git-35c091f4b7/ffmpeg-2025-03-31-git-35c091f4b7-essentials_build.zip"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Download with retry
            task = progress.add_task("[#89b4fa]Downloading FFmpeg...[/#89b4fa]", total=None)
            try:
                response = download_with_retry(url)
            except Exception as e:
                progress.update(task, description=f"[#f38ba8]Download failed: {e}[/#f38ba8]")
                raise
            
            progress.update(task, description="[#89b4fa]Extracting files...[/#89b4fa]")
            # Create proper temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        # Extract only the executables we need
                        for file in z.namelist():
                            filename = os.path.basename(file)
                            if filename in ["ffmpeg.exe", "ffprobe.exe"]:
                                # Extract to temporary directory
                                z.extract(file, temp_dir)
                                # Get the extracted file path
                                source = os.path.join(temp_dir, file)
                                target = os.path.join(bin_dir, filename)
                                # Move to target directory
                                if os.path.exists(source):
                                    shutil.move(source, target)
                                    progress.update(task, description=f"[#94e2d5]Installed {filename}[/#94e2d5]")
                                    
                                    # Verify the binary is executable
                                    if not verify_binary_executable(target):
                                        progress.update(task, description=f"[#f38ba8]Warning: {filename} may not be executable[/#f38ba8]")
                except (zipfile.BadZipFile, IOError) as e:
                    progress.update(task, description=f"[#f38ba8]Extraction failed: {e}[/#f38ba8]")
                    raise
        
        console.print("\n[bold #a6e3a1]✅ FFmpeg has been installed successfully![/bold #a6e3a1]")
        console.print("[#89dceb]You can now use all TrackTidy features that require FFmpeg.[/#89dceb]")
        return True
        
    except Exception as e:
        console.print(f"\n[bold #f38ba8]❌ Error downloading FFmpeg: {e}[/bold #f38ba8]")
        console.print("\n[#89dceb]Please install FFmpeg manually:[/#89dceb]")
        console.print("- Windows: Download from https://ffmpeg.org/download.html")
        console.print("- macOS: Run 'brew install ffmpeg'")
        console.print("- Linux: Run 'sudo apt install ffmpeg' or use your package manager")
        return False

def validate_installation():
    """Validate that FFmpeg installation was successful
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    ffmpeg_path = find_ffmpeg_executable()
    ffprobe_path = find_ffprobe_executable()
    
    if not ffmpeg_path or not ffprobe_path:
        return False
        
    # Verify executables work
    try:
        # Test FFmpeg
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            return False
            
        # Test FFprobe
        result = subprocess.run(
            [ffprobe_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            return False
            
        return True
    except (subprocess.SubprocessError, OSError, FileNotFoundError) as e:
        # SubprocessError: Base class for subprocess exceptions
        # OSError: Covers issues like permission errors
        # FileNotFoundError: In case the executable isn't found (though we checked earlier)
        console.print(f"[#f38ba8]Error validating FFmpeg: {e}[/#f38ba8]")
        return False

if __name__ == "__main__":
    # This allows running this file directly to install FFmpeg
    success = download_ffmpeg_to_app_dir()
    if success:
        # Validate installation
        if validate_installation():
            console.print("[bold #a6e3a1]✅ FFmpeg installation verified and working![/bold #a6e3a1]")
        else:
            console.print("[bold #f38ba8]⚠️ FFmpeg was installed but may not be working correctly.[/bold #f38ba8]")
