import os
import shutil
import subprocess
import platform
import sys

def main():
    """Build the TrackTidy executable using PyInstaller"""
    print("Building TrackTidy executable...")
    
    # Determine the system
    system = platform.system()
    
    # Clean up previous builds
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Run PyInstaller
    subprocess.run(["pyinstaller", "tracktidy.spec"], check=True)
    
    # Create additional files for the distribution
    create_readme()
    
    print("\nNOTE: FFmpeg must be installed for audio conversion features to work.")
    print("Recommend users to run 'TrackTidy --download-ffmpeg' after installation.")
    
    print("\nBuild complete! You can find the executable in the 'dist/TrackTidy' folder.")
    
def create_readme():
    """Create a shorter README for the distribution"""
    readme_path = os.path.join("dist", "TrackTidy", "README.txt")
    os.makedirs(os.path.dirname(readme_path), exist_ok=True)
    
    with open(readme_path, "w") as f:
        f.write("""TrackTidy - Music Manager for DJs and Music Enthusiasts
==================================================

This program allows you to:
- Edit audio file metadata (title, artist, album, genre)
- Convert audio between different formats
- Fetch and embed album artwork from Spotify
- Process multiple files in batches

IMPORTANT REQUIREMENTS:
- FFmpeg must be installed for audio conversion features
  Easy install: Run 'TrackTidy --download-ffmpeg'
  OR install manually from: https://ffmpeg.org/download.html

For Spotify artwork features:
- You'll need to get your own Spotify API credentials from https://developer.spotify.com/dashboard
- The app will prompt you to enter these the first time you use the cover art feature

For more information and updates, visit: https://github.com/yourusername/tracktidy
""")

if __name__ == "__main__":
    main()