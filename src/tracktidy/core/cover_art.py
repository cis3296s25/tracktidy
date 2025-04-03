"""
Cover art functionality for TrackTidy
"""
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from rich.console import Console
from rich.prompt import Prompt

from tracktidy.services.spotify import (
    get_spotify_credentials, 
    initialize_spotify_client,
    search_track,
    download_cover_art
)

console = Console()

# Initialize with empty globals initially
sp = None
SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET = "", ""

def setup_spotify():
    """Set up the Spotify client"""
    global sp, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET
    
    # Get Spotify credentials
    SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET = get_spotify_credentials()
    
    # Initialize Spotify API client
    if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
        sp = initialize_spotify_client(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
        return sp is not None
    return False

async def fetch_cover_art():
    """Interactive cover art fetching UI"""
    global sp
    
    console.print("\n[bold #f5e0dc]🎵 TrackTidy Cover Art Fetcher 🎵[/bold #f5e0dc]\n")
    
    # Initialize Spotify client if not already initialized
    if sp is None:
        if not setup_spotify():
            console.print("[bold #f38ba8]❌ Error: Spotify API connection failed![/bold #f38ba8]")
            console.print("[#89dceb]This could be due to invalid credentials or network issues.[/#89dceb]")
            
            # Reset credentials?
            reset = Prompt.ask("[#cba6f7]Would you like to reset your Spotify credentials?[/#cba6f7]", 
                            choices=["y", "n"], default="n")
            
            if reset.lower() == "y":
                # Force credential reset by calling setup_spotify again
                if not setup_spotify():
                    console.print("[#f38ba8]Failed to set up Spotify connection.[/#f38ba8]")
                    Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                    return
            else:
                Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                return

    # Get song name and artist from user
    while True:
        song_name = Prompt.ask("[#89dceb]Enter the song name[/#89dceb]").strip()
        if not song_name:
            console.print("[bold #f38ba8]❌ Error: Song name cannot be empty![/bold #f38ba8]")
            continue
        break

    while True:
        artist_name = Prompt.ask("[#89dceb]Enter the artist name[/#89dceb]").strip()
        if not artist_name:
            console.print("[bold #f38ba8]❌ Error: Artist name cannot be empty![/bold #f38ba8]")
            continue
        break

    # Search for the track on Spotify
    cover_url, track_name, track_artist, album_name = search_track(sp, song_name, artist_name)
    
    if not cover_url:
        console.print("[bold #f38ba8]❌ No cover art found for this track.[/bold #f38ba8]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return

    console.print(f"[#94e2d5]🎨 Cover Art Found:[/#94e2d5] {cover_url}")
    
    # Show track name and artist for confirmation
    console.print(f"[#94e2d5]Track:[/#94e2d5] {track_name} by {track_artist}")
    console.print(f"[#94e2d5]Album:[/#94e2d5] {album_name}")
    
    # Get the MP3 file path from the user
    while True:
        file_path = Prompt.ask("[#cba6f7]Enter the path to the MP3 file[/#cba6f7]").strip()
        if not os.path.isfile(file_path):
            console.print("[bold #f38ba8]❌ Error: File not found! Please enter a valid file path.[/bold #f38ba8]")
            continue
        
        if not file_path.lower().endswith('.mp3'):
            console.print("[bold #f38ba8]❌ Error: File must be an MP3 file![/bold #f38ba8]")
            continue
        break

    # Download the cover image
    image_data = download_cover_art(cover_url)
    if not image_data:
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return

    # Embed cover art into the MP3 file
    try:
        audio = MP3(file_path, ID3=ID3)
        audio.tags.add(
            APIC(
                encoding=3,         # UTF-8
                mime="image/jpeg",  # Image MIME type
                type=3,             # Front cover image
                desc="Cover",
                data=image_data
            )
        )
        audio.save()
        console.print(f"[bold #a6e3a1]✅ Cover art added successfully![/bold #a6e3a1]")

        # Pause before returning to the menu
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error embedding cover art:[/bold #f38ba8] {e}")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
