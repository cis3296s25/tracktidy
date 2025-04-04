"""
Audio conversion functionality for TrackTidy
"""
import asyncio
import os
import re
import subprocess
import platform
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeRemainingColumn

# Import FFmpeg utilities
from tracktidy.services.ffmpeg import find_ffmpeg_executable, find_ffprobe_executable, check_ffmpeg_installed, get_app_directory

console = Console(force_terminal=True, color_system="truecolor")

# Get FFmpeg and FFprobe paths dynamically for each operation
def get_ffmpeg_paths():
    """Get current FFmpeg and FFprobe paths, or use installed binaries directly"""
    # First try the normal way
    ffmpeg = find_ffmpeg_executable()
    ffprobe = find_ffprobe_executable()
    
    # If not found, try direct paths to installed binaries
    if not ffmpeg or not ffprobe:
        app_dir = get_app_directory()
        bin_dir = os.path.join(app_dir, "bin")
        
        exe_ext = ".exe" if platform.system() == "Windows" else ""
        
        # Check direct paths to installed binaries
        ffmpeg_direct = os.path.join(bin_dir, f"ffmpeg{exe_ext}")
        ffprobe_direct = os.path.join(bin_dir, f"ffprobe{exe_ext}")
        
        if os.path.exists(ffmpeg_direct) and not ffmpeg:
            ffmpeg = ffmpeg_direct
        
        if os.path.exists(ffprobe_direct) and not ffprobe:
            ffprobe = ffprobe_direct
    
    return ffmpeg, ffprobe

# Extract total duration (ffprobe)
def get_audio_duration(file_path):
    try:
        # Get current path
        _, ffprobe_path = get_ffmpeg_paths()
        
        if not ffprobe_path:
            return None
            
        result = subprocess.run(
            [ffprobe_path, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        console.print(f"[bold #f38ba8]Error getting duration: {e}[/bold #f38ba8]")
        return None

# Extract elapsed time (FFmpeg)
def extract_time_from_output(log_line):
    match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", log_line)
    if match:
        h, m, s = map(float, match.group(1).split(":"))
        return (h * 3600) + (m * 60) + s  # Convert to seconds
    return None


async def convert_audio_file(input_file, output_file, silent=False):
    """Convert a single audio file with optional silent mode for batch processing"""
    try:
        # Check if files exist
        if not os.path.isfile(input_file):
            if not silent:
                console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] Input file not found!")
            return False
        
        input_file = os.path.abspath(input_file)
        output_file = os.path.abspath(output_file)
        
        # Get total duration
        total_duration = get_audio_duration(input_file)
        if total_duration is None:
            if not silent:
                console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] Could not determine file duration! This might not be a valid audio file or ffprobe isn't installed.")
            return False

        try:
            # Get current FFmpeg path
            ffmpeg_path, _ = get_ffmpeg_paths()
            
            if not ffmpeg_path:
                if not silent:
                    console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] FFmpeg not found or not properly installed.")
                    console.print("[#89dceb]Please install FFmpeg and make sure it's in your PATH.[/#89dceb]")
                return False
            
            if silent:
                # Use simple subprocess for silent mode
                process = subprocess.run(
                    [ffmpeg_path, "-y", "-i", input_file, output_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return process.returncode == 0
            else:
                # Use asyncio with progress bar for interactive mode
                process = await asyncio.create_subprocess_exec(
                    ffmpeg_path, "-y", "-i", input_file, output_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                with Progress(
                    "[bold #fab387]🔄 Converting:[/bold #fab387] {task.description}",
                    BarColumn(),
                    TimeRemainingColumn(),
                    console=console,
                    transient=True,  # Removes progress bar after completion
                ) as progress:
                    task = progress.add_task(f"[#b4befe]{os.path.basename(input_file)}[/#b4befe]", total=total_duration)

                    while True:
                        line = await process.stderr.readline()
                        line = line.decode("utf-8").strip() if isinstance(line, bytes) else line.strip()
                        if not line:
                            break

                        elapsed_time = extract_time_from_output(line)
                        if elapsed_time is not None:
                            progress.update(task, completed=elapsed_time)

                    await process.wait()

                return process.returncode == 0 and os.path.exists(output_file)
            
        except Exception as e:
            if not silent:
                console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")
                console.print("[#89dceb]This might be because FFmpeg is not installed or accessible from the command line.[/#89dceb]")
            return False
            
    except Exception as e:
        if not silent:
            console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")
        return False


async def convert_audio():
    """Interactive audio conversion UI"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy Audio Converter 🎵[/bold #f5e0dc]\n")

    # Get file path
    while True:
        file_path = Prompt.ask("[#89dceb]Enter the path of the audio file to convert[/#89dceb]").strip()
        if not file_path:
            console.print("[bold #f38ba8]❌ Error: Path cannot be empty! Try again.[/bold #f38ba8]")
            continue
        if not os.path.isfile(file_path):
            console.print("[bold #f38ba8]❌ Error: File not found! Try again.[/bold #f38ba8]")
            continue
        break

    # Choose the output format
    valid_formats = ["mp3", "wav", "flac", "aac", "ogg"]
    while True:
        output_format = Prompt.ask("[#cba6f7]Enter the output format (mp3, wav, flac, aac, ogg)[/#cba6f7]").strip().lower()
        if output_format not in valid_formats:
            console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] Unsupported format!")
            continue
        break

    output_file = os.path.splitext(file_path)[0] + f".{output_format}"
    
    console.print(f"[#eba0ac]🔄 Converting {file_path} to {output_format}...[/#eba0ac]")
    
    # Use the helper function for conversion
    if await convert_audio_file(file_path, output_file):
        console.print(f"[bold #a6e3a1]✅ Conversion successful![/bold #a6e3a1] [#f9e2af]Saved as:[/#f9e2af] {output_file}")
    else:
        console.print(f"[bold #f38ba8]❌ Error during conversion![/bold #f38ba8]")

    # Pause before returning to the menu
    Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
