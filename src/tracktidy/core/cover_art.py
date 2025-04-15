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
    download_cover_art,
    reset_spotify_credentials
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
    
    # Check if user wants to return to main menu
    if SPOTIPY_CLIENT_ID == "-1" and SPOTIPY_CLIENT_SECRET == "-1":
        return "return_to_menu"
    
    # Initialize Spotify API client
    if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
        sp = initialize_spotify_client(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
        return sp is not None
    return False

async def fetch_cover_art():
    """Interactive cover art fetching UI"""
    global sp, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET
    
    console.print("\n[bold #f5e0dc]🎵 TrackTidy Cover Art Fetcher  🎵[/bold #f5e0dc]\n")
    
    # Initialize Spotify client if not already initialized
    if sp is None:
        setup_result = setup_spotify()
        
        # Check if user wants to return to main menu
        if setup_result == "return_to_menu":
            return
            
        if not setup_result:
            console.print("[bold #f38ba8]❌ Error: Spotify API connection failed![/bold #f38ba8]")
            console.print("[#89dceb]This could be due to invalid credentials or network issues.[/#89dceb]")
            
            # Reset credentials?
            reset = Prompt.ask("[#cba6f7]Would you like to reset your Spotify credentials?[/#cba6f7]", 
                            choices=["y", "n"], default="n")
            
            if reset.lower() == "y":
                # Force credential reset by calling setup_spotify again
                setup_result = setup_spotify()
                
                # Check again if user wants to return to main menu
                if setup_result == "return_to_menu":
                    return
                    
                if not setup_result:
                    console.print("[#f38ba8]Failed to set up Spotify connection.[/#f38ba8]")
                    Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                    return
            else:
                Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                return

    # Get song name and artist from user
    console.print("\n[#89b4fa]1.[/#89b4fa][bold] Enter Song Details[/bold]")
    console.print("[#b4befe]2.[/#b4befe][bold] Reset Spotify API Credentials[/bold]")
    console.print("[#f38ba8]3.[/#f38ba8][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2", "3"])
    
    if choice == "3":
        return
    
    # Main menu loop - allows returning to menu after credential reset
    while True:
        if choice == "2":
            # Reset Spotify credentials
            console.print("[#89dceb]Resetting Spotify API credentials...[/#89dceb]")
            
            # Delete the credentials file
            reset_result = reset_spotify_credentials()
            
            # Clear existing credentials in memory
            sp = None
            SPOTIPY_CLIENT_ID = ""
            SPOTIPY_CLIENT_SECRET = ""
            
            # Force credential reset
            setup_result = setup_spotify()
            
            # Check if user wants to return to main menu
            if setup_result == "return_to_menu":
                return
                
            if not setup_result:
                console.print("[#f38ba8]Failed to set up Spotify connection.[/#f38ba8]")
                Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                return
                
            console.print("[bold #a6e3a1]✅ Spotify credentials reset successfully![/bold #a6e3a1]")
            
            # Return to menu instead of recursive call
            console.print("\n[#89b4fa]1.[/#89b4fa][bold] Enter Song Details[/bold]")
            console.print("[#b4befe]2.[/#b4befe][bold] Reset Spotify API Credentials[/bold]")
            console.print("[#f38ba8]3.[/#f38ba8][bold] Return to Main Menu[/bold]")
            
            choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2", "3"])
            
            if choice == "3":
                return
                
            # Continue the loop if they choose option 2 again
            if choice == "2":
                continue
                
        # Break out of the loop if they choose option 1
        break
    
    # Get song name
    while True:
        song_name = Prompt.ask("[#89dceb]Enter the song name[/#89dceb]").strip()
        if not song_name:
            console.print("[bold #f38ba8]❌ Error: Song name cannot be empty![/bold #f38ba8]")
            continue
        break

    # Get artist name
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
    
    # Ask if user wants to continue or return to main menu
    console.print("\n[#89b4fa]1.[/#89b4fa][bold] Continue and Add Cover Art to MP3[/bold]")
    console.print("[#f38ba8]2.[/#f38ba8][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2"])
    
    if choice == "2":
        return
    
    def scan_directory_for_mp3(directory_path):
        """Scan a directory for MP3 files"""
        mp3_files = []
        
        try:
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path) and file_path.lower().endswith('.mp3'):
                    mp3_files.append(file_path)
        except Exception as e:
            console.print(f"[bold #f38ba8]❌ Error scanning directory:[/bold #f38ba8] {e}")
        
        return mp3_files
    
    # Get the MP3 file path from the user
    while True:
        console.print("[#94e2d5]You can enter a file path or a folder path containing MP3 files[/#94e2d5]")
        file_path = Prompt.ask("[#cba6f7]Enter the path to the MP3 file or folder[/#cba6f7]").strip()
        
        # Handle paths with quotes (often added when dragging files with spaces)
        if (file_path.startswith('"') and file_path.endswith('"')) or \
           (file_path.startswith("'") and file_path.endswith("'")):
            file_path = file_path[1:-1]
        
        # Normalize and expand the path
        file_path = os.path.normpath(os.path.expanduser(file_path))
        
        # Check if path is a directory
        if os.path.isdir(file_path):
            # Scan directory for MP3 files
            mp3_files = scan_directory_for_mp3(file_path)
            
            if not mp3_files:
                console.print("[bold #f38ba8]❌ No MP3 files found in the directory![/bold #f38ba8]")
                continue
                
            # Display list of found MP3 files
            console.print("\n[#f9e2af]Found the following MP3 files:[/#f9e2af]")
            for i, mp3_path in enumerate(mp3_files):
                console.print(f"[#89b4fa]{i+1}.[/#89b4fa] {os.path.basename(mp3_path)}")
                
            # Let user select a file
            file_choice = Prompt.ask(
                "\n[#cba6f7]Select a file by number[/#cba6f7]",
                choices=[str(i+1) for i in range(len(mp3_files))]
            )
                
            file_path = mp3_files[int(file_choice) - 1]
            console.print(f"[#94e2d5]Selected:[/#94e2d5] {file_path}")
            break
        elif os.path.isfile(file_path):
            if not file_path.lower().endswith('.mp3'):
                console.print("[bold #f38ba8]❌ Error: File must be an MP3 file![/bold #f38ba8]")
                continue
            break
        else:
            console.print("[bold #f38ba8]❌ Error: File not found! Please enter a valid file path.[/bold #f38ba8]")
            console.print(f"[#89dceb]Attempted to find: {file_path}[/#89dceb]")
            console.print("[#89dceb]Tip: For files with spaces in the name, you can drag and drop the file here.[/#89dceb]")
            continue
    
    # Display the selected file with its full path for clarity
    console.print(f"[bold #b4befe]Selected file:[/bold #b4befe] [#cba6f7]{os.path.abspath(file_path)}[/#cba6f7]")

    # Download the cover image
    image_data = download_cover_art(cover_url)
    if not image_data:
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return

    # Embed cover art into the MP3 file
    try:
        # First clear existing ID3 tags if they exist
        try:
            id3 = ID3(file_path)
            # Only remove the APIC frames (cover art)
            for key in list(id3.keys()):
                if key.startswith('APIC'):
                    del id3[key]
            id3.save(file_path)
        except:
            pass  # No existing tags
            
        # Add the new cover art
        audio = MP3(file_path, ID3=ID3)
        
        # Ensure ID3v2 tags exist
        if audio.tags is None:
            audio.add_tags()
            
        # Add cover art with appropriate MIME type
        # Try to determine MIME type from the first bytes
        mime_type = "image/jpeg"  # Default
        if image_data[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
            
        audio.tags.add(
            APIC(
                encoding=3,         # UTF-8
                mime=mime_type,     # Image MIME type based on content
                type=3,             # Front cover image
                desc="Cover",
                data=image_data
            )
        )
        audio.save(v2_version=3)  # Explicitly use ID3v2.3
        
        console.print(f"[bold #a6e3a1]✅ Cover art added successfully![/bold #a6e3a1]")
        console.print("[#89dceb]Note: It may take a moment for Windows Explorer to show the thumbnail.[/#89dceb]")
        console.print("[#89dceb]If it doesn't appear, try right-clicking and selecting 'Properties' to refresh.[/#89dceb]")

        # Pause before returning to the menu
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error embedding cover art:[/bold #f38ba8] {e}")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
