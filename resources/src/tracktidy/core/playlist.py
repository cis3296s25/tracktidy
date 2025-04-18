"""
Playlist generation module for TrackTidy
Supports .m3u and .pls playlist formats
"""
import os
import datetime
from typing import List, Dict, Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

def create_m3u_playlist(tracks: List[str], output_path: str, playlist_name: Optional[str] = None) -> str:
    """
    Create an M3U playlist file from a list of track paths
    
    Args:
        tracks: List of file paths to audio tracks
        output_path: Directory where the playlist will be saved
        playlist_name: Optional name for the playlist (default: auto-generated)
        
    Returns:
        Path to the created playlist file
    """
    if not playlist_name:
        # Generate a default playlist name if none provided
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        playlist_name = f"tracktidy_playlist_{timestamp}"
    
    # Ensure the playlist name has the correct extension
    if not playlist_name.lower().endswith('.m3u'):
        playlist_name += '.m3u'
    
    playlist_path = os.path.join(output_path, playlist_name)
    
    with open(playlist_path, 'w', encoding='utf-8') as f:
        # Write M3U header
        f.write("#EXTM3U\n")
        
        # Write each track
        for track_path in tracks:
            if os.path.isfile(track_path):
                # Get the filename for display
                track_name = os.path.basename(track_path)
                
                # Write extended info (optional but useful)
                f.write(f"#EXTINF:-1,{track_name}\n")
                
                # Write the file path - use relative path if in same directory
                if os.path.dirname(track_path) == output_path:
                    f.write(f"{os.path.basename(track_path)}\n")
                else:
                    f.write(f"{track_path}\n")
    
    return playlist_path

def create_pls_playlist(tracks: List[str], output_path: str, playlist_name: Optional[str] = None) -> str:
    """
    Create a PLS playlist file from a list of track paths
    
    Args:
        tracks: List of file paths to audio tracks
        output_path: Directory where the playlist will be saved
        playlist_name: Optional name for the playlist (default: auto-generated)
        
    Returns:
        Path to the created playlist file
    """
    if not playlist_name:
        # Generate a default playlist name if none provided
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        playlist_name = f"tracktidy_playlist_{timestamp}"
    
    # Ensure the playlist name has the correct extension
    if not playlist_name.lower().endswith('.pls'):
        playlist_name += '.pls'
    
    playlist_path = os.path.join(output_path, playlist_name)
    
    with open(playlist_path, 'w', encoding='utf-8') as f:
        # Write PLS header
        f.write("[playlist]\n")
        
        # Write number of entries
        f.write(f"NumberOfEntries={len(tracks)}\n")
        
        # Write each track
        for i, track_path in enumerate(tracks, 1):
            if os.path.isfile(track_path):
                # Get the filename for display
                track_name = os.path.basename(track_path)
                
                # Write file path, title, and length (-1 for unknown)
                f.write(f"File{i}={track_path}\n")
                f.write(f"Title{i}={track_name}\n")
                f.write(f"Length{i}=-1\n")
        
        # Write version
        f.write("Version=2\n")
    
    return playlist_path

def select_tracks_from_directory(directory: str) -> List[str]:
    """
    Allow user to select multiple tracks from a directory
    
    Args:
        directory: Directory to scan for audio files
        
    Returns:
        List of selected track paths
    """
    # List of common audio file extensions
    audio_extensions = ['.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg']
    
    # Scan directory for audio files
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        console.print(f"[bold red]No audio files found in {directory}[/bold red]")
        return []
    
    # Sort files alphabetically
    audio_files.sort()
    
    # Display files with numbers for selection
    console.print(f"[bold cyan]Found {len(audio_files)} audio files:[/bold cyan]")
    for i, file in enumerate(audio_files, 1):
        console.print(f"[cyan]{i}.[/cyan] {os.path.basename(file)}")
    
    # Allow user to select multiple files
    console.print("\n[bold yellow]Enter file numbers to include (comma-separated, e.g. '1,3,5-7')[/bold yellow]")
    console.print("[bold yellow]Enter 'all' to select all files[/bold yellow]")
    
    selection = Prompt.ask("[bold green]Selection[/bold green]")
    
    selected_tracks = []
    
    if selection.lower() == 'all':
        selected_tracks = audio_files
    else:
        # Parse the selection string (e.g., "1,3,5-7")
        parts = selection.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Handle ranges (e.g., "5-7")
                try:
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        if 1 <= i <= len(audio_files):
                            selected_tracks.append(audio_files[i - 1])
                except ValueError:
                    console.print(f"[bold red]Invalid range: {part}[/bold red]")
            else:
                # Handle single numbers
                try:
                    i = int(part)
                    if 1 <= i <= len(audio_files):
                        selected_tracks.append(audio_files[i - 1])
                    else:
                        console.print(f"[bold red]Number out of range: {i}[/bold red]")
                except ValueError:
                    console.print(f"[bold red]Invalid number: {part}[/bold red]")
    
    return selected_tracks

async def generate_playlist(tracks: List[str], output_dir: str, format_type: str, playlist_name: Optional[str] = None) -> str:
    """
    Generate a playlist file in the specified format
    
    Args:
        tracks: List of track paths to include in the playlist
        output_dir: Directory where the playlist will be saved
        format_type: Playlist format ('m3u' or 'pls')
        playlist_name: Optional name for the playlist
        
    Returns:
        Path to the created playlist file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create progress bar
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold green]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("Creating playlist...", total=len(tracks))
        
        # Generate the playlist based on the selected format
        if format_type.lower() == 'm3u':
            playlist_path = create_m3u_playlist(tracks, output_dir, playlist_name)
        elif format_type.lower() == 'pls':
            playlist_path = create_pls_playlist(tracks, output_dir, playlist_name)
        else:
            raise ValueError(f"Unsupported playlist format: {format_type}")
        
        # Update progress
        progress.update(task, completed=len(tracks))
    
    return playlist_path