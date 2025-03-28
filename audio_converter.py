import asyncio
import os
import re
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeRemainingColumn

console = Console(force_terminal=True, color_system="truecolor")

# Extract total duration (ffprobe)
def get_audio_duration(file_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path],
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

    file_path = os.path.abspath(file_path)

    # Get total duration
    total_duration = get_audio_duration(file_path)
    if total_duration is None:
        console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] Could not determine file duration! This might not be a valid audio file or ffprobe isn't installed.")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return

    # Detect input file format
    file_extension = os.path.splitext(file_path)[1].lower().strip(".")
    if not file_extension:
        console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] Could not determine file format!")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return
    console.print(
            f"[#94e2d5]📂 Detected file format:[/#94e2d5] [bold #89b4fa]{file_extension.upper()}[/bold #89b4fa]")

    # Ask for output format (limited options)
    valid_formats = ["mp3", "wav", "flac", "aac", "ogg"]
    while True:
        output_format = Prompt.ask("[#cba6f7]Enter the output format (mp3, wav, flac, aac, ogg)[/#cba6f7]").strip().lower()
        if output_format not in valid_formats:
            console.print("[bold #f38ba8]❌ Error:[/bold #f38ba8] Unsupported format!")
            continue
        break

    output_file = os.path.splitext(file_path)[0] + f".{output_format}"
    output_file = os.path.abspath(output_file)

    console.print(f"[#eba0ac]🔄 Converting {file_path} to {output_format}...[/#eba0ac]")

    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", file_path, output_file,
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
            task = progress.add_task(f"[#b4befe]{os.path.basename(file_path)}[/#b4befe]", total=total_duration)

            while True:
                line = await process.stderr.readline()
                line = line.decode("utf-8").strip() if isinstance(line, bytes) else line.strip()
                if not line:
                    break

                elapsed_time = extract_time_from_output(line)
                if elapsed_time is not None:
                    progress.update(task, completed=elapsed_time)

            await process.wait()

        if process.returncode == 0 and os.path.exists(output_file):
            console.print(
                f"[bold #a6e3a1]✅ Conversion successful![/bold #a6e3a1] [#f9e2af]Saved as:[/#f9e2af] {output_file}")
        else:
            console.print(f"[bold #f38ba8]❌ Error during conversion:[/bold #f38ba8] FFmpeg returned error code {process.returncode}.")
            console.print("[#89dceb]This could be due to incompatible formats or codec issues.[/#89dceb]")

        # Pause before returning to the menu
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")
        console.print("[#89dceb]This might be because FFmpeg is not installed or accessible from the command line.[/#89dceb]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

if __name__ == "__main__":
    asyncio.run(convert_audio())