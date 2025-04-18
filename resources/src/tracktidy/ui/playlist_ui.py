"""
Playlist generation UI for TrackTidy
"""
import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from src.tracktidy.core.playlist import select_tracks_from_directory, generate_playlist

console = Console()

async def playlist_ui():
    """
    User interface for generating playlists
    """
    console.clear()
    
    # Display header
    header = Text("🎵 Playlist Generator 🎵", style="bold #f5c2e7")
    console.print(Panel(header, style="bold #cba6f7"))
    
    console.print("\n[bold #89b4fa]This tool helps you create playlist files from your music collection.[/bold #89b4fa]")
    console.print("[#89dceb]You can create .m3u or .pls playlist files from selected tracks.[/#89dceb]\n")
    
    # Get directory containing audio files
    default_dir = os.path.expanduser("~/Music")
    if not os.path.exists(default_dir):
        default_dir = os.getcwd()
    
    directory = Prompt.ask(
        "[bold #a6e3a1]Enter the directory containing your audio files[/bold #a6e3a1]",
        default=default_dir
    )
    
    # Validate directory
    if not os.path.isdir(directory):
        console.print(f"[bold #f38ba8]Error: {directory} is not a valid directory[/bold #f38ba8]")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Select tracks
    console.print(f"\n[bold #89b4fa]Scanning {directory} for audio files...[/bold #89b4fa]")
    selected_tracks = select_tracks_from_directory(directory)
    
    if not selected_tracks:
        console.print("[bold #f38ba8]No tracks selected. Returning to main menu.[/bold #f38ba8]")
        input("\nPress Enter to continue...")
        return
    
    console.print(f"\n[bold #a6e3a1]Selected {len(selected_tracks)} tracks.[/bold #a6e3a1]")
    
    # Choose playlist format
    format_type = Prompt.ask(
        "[bold #f5c2e7]Select playlist format[/bold #f5c2e7]",
        choices=["m3u", "pls"],
        default="m3u"
    )
    
    # Get playlist name (optional)
    playlist_name = Prompt.ask(
        "[bold #fab387]Enter playlist name (optional)[/bold #fab387]",
        default=""
    )
    
    # Get output directory
    output_dir = Prompt.ask(
        "[bold #b4befe]Enter output directory for the playlist[/bold #b4befe]",
        default=directory
    )
    
    # Validate output directory
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            console.print(f"[bold #a6e3a1]Created output directory: {output_dir}[/bold #a6e3a1]")
        except Exception as e:
            console.print(f"[bold #f38ba8]Error creating output directory: {e}[/bold #f38ba8]")
            input("\nPress Enter to return to the main menu...")
            return
    
    # Generate the playlist
    try:
        console.print("\n[bold #89b4fa]Generating playlist...[/bold #89b4fa]")
        playlist_path = await generate_playlist(
            selected_tracks,
            output_dir,
            format_type,
            playlist_name
        )
        
        console.print(f"\n[bold #a6e3a1]✅ Playlist successfully created:[/bold #a6e3a1]")
        console.print(f"[#89dceb]{playlist_path}[/#89dceb]")
        
    except Exception as e:
        console.print(f"[bold #f38ba8]Error generating playlist: {e}[/bold #f38ba8]")
    
    input("\nPress Enter to return to the main menu...")