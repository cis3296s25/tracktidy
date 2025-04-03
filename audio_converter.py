import asyncio
import os
import re
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeRemainingColumn

# Import FFmpeg locator
from ffmpeg_utils import find_ffmpeg_executable, find_ffprobe_executable, check_ffmpeg_installed

console = Console(force_terminal=True, color_system="truecolor")

# Get FFmpeg and FFprobe paths
FFMPEG_PATH = find_ffmpeg_executable()
FFPROBE_PATH = find_ffprobe_executable()

# Extract total duration (ffprobe)
def get_audio_duration(file_path):
    try:
        if not FFPROBE_PATH:
            return None
            
        result = subprocess.run(
            [FFPROBE_PATH, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
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
            if silent:
                # Use simple subprocess for silent mode
                if not FFMPEG_PATH:
                    if not silent:
                        console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] FFmpeg not found or not properly installed.")
                    return False
                    
                process = subprocess.run(
                    [FFMPEG_PATH, "-y", "-i", input_file, output_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return process.returncode == 0
            else:
                # Use asyncio with progress bar for interactive mode
                if not FFMPEG_PATH:
                    console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] FFmpeg not found or not properly installed.")
                    console.print("[#89dceb]Please install FFmpeg and make sure it's in your PATH.[/#89dceb]")
                    return False
                    
                process = await asyncio.create_subprocess_exec(
                    FFMPEG_PATH, "-y", "-i", input_file, output_file,
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

if __name__ == "__main__":
    asyncio.run(convert_audio())