import os
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from rich.console import Console
from rich.prompt import Prompt

console = Console()

# Path to store credentials
CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.spotify_creds.json')

def validate_spotify_credentials(client_id, client_secret):
    # Test if the provided Spotify credentials are valid
    if not client_id or not client_secret:
        return False
    
    try:
        # Initialize Spotify client attempt
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp_test = spotipy.Spotify(auth_manager=auth_manager)
        
        # Make API call to test the credentials
        _ = sp_test.search(q="test", limit=1)
        return True
    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Invalid credentials:[/bold #f38ba8] {str(e)}")
        return False

def get_spotify_credentials():
    """Get Spotify API credentials from file or user input with validation"""
    # Try to read from credentials file first
    if os.path.exists(CREDS_FILE):
        try:
            with open(CREDS_FILE, 'r') as f:
                creds = json.load(f)
                client_id = creds.get('client_id', '')
                client_secret = creds.get('client_secret', '')
                
                # Validate the stored credentials
                if validate_spotify_credentials(client_id, client_secret):
                    return client_id, client_secret
                else:
                    console.print("[#f38ba8]Stored Spotify credentials are invalid. Please enter new credentials.[/#f38ba8]")
        except Exception:
            console.print("[#f38ba8]Couldn't read stored credentials. You'll need to enter them again.[/#f38ba8]")
    
    # If credentials file doesn't exist or is invalid, prompt user
    console.print("\n[bold #f5e0dc]🎵 Spotify API Setup 🎵[/bold #f5e0dc]")
    console.print("[#89dceb]TrackTidy needs Spotify API credentials to fetch cover art.[/#89dceb]")
    console.print("[#89dceb]You can get these from https://developer.spotify.com/dashboard/[/#89dceb]")
    
    # Keep prompting until we get valid credentials or user gives up
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        client_id = Prompt.ask("[#cba6f7]Enter your Spotify Client ID[/#cba6f7]").strip()
        client_secret = Prompt.ask("[#cba6f7]Enter your Spotify Client Secret[/#cba6f7]").strip()
        
        console.print("[#89dceb]Validating credentials...[/#89dceb]")
        
        # Validate the credentials
        if validate_spotify_credentials(client_id, client_secret):
            console.print("[bold #a6e3a1]✅ Credentials validated successfully![/bold #a6e3a1]")
            
            # Save for future use if both are provided and valid
            try:
                with open(CREDS_FILE, 'w') as f:
                    json.dump({
                        'client_id': client_id,
                        'client_secret': client_secret
                    }, f)
                console.print("[bold #a6e3a1]✅ Credentials saved for future use![/bold #a6e3a1]")
            except Exception as e:
                console.print(f"[#f38ba8]Note: Couldn't save credentials ({e}). You'll need to enter them again next time.[/#f38ba8]")
            
            return client_id, client_secret
        
        attempts += 1
        if attempts < max_attempts:
            retry = Prompt.ask(
                f"[#cba6f7]Invalid credentials. Try again? ({max_attempts - attempts} attempts left)[/#cba6f7]",
                choices=["y", "n"], 
                default="y"
            )
            if retry.lower() != "y":
                break
        else:
            console.print("[bold #f38ba8]❌ Maximum attempts reached. Please check your credentials.[/bold #f38ba8]")
    
    return "", ""  # Return empty strings if validation fails

# Get the Spotify credentials when module is imported
SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET = get_spotify_credentials()

# Initialize Spotify API client (might be None if credentials are invalid)
sp = None
if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET
        ))
    except Exception:
        sp = None

# Initialize or reinitialize the Spotify client
def initialize_spotify_client(client_id, client_secret):
    if not client_id or not client_secret:
        return None
    
    try:
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))
    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Failed to initialize Spotify client: {e}[/bold #f38ba8]")
        return None

async def fetch_cover_art():
    global sp  # Declare global here before any use
    
    console.print("\n[bold #f5e0dc]🎵 TrackTidy Cover Art Fetcher 🎵[/bold #f5e0dc]\n")
    
    # Check if Spotify API client is initialized
    if sp is None:
        console.print("[bold #f38ba8]❌ Error: Spotify API connection failed![/bold #f38ba8]")
        console.print("[#89dceb]This could be due to invalid credentials or network issues.[/#89dceb]")
        
        # Reset credentials?
        reset = Prompt.ask("[#cba6f7]Would you like to reset your Spotify credentials?[/#cba6f7]", 
                           choices=["y", "n"], default="n")
        
        if reset.lower() == "y":
            # Remove credentials file if it exists
            if os.path.exists(CREDS_FILE):
                try:
                    os.remove(CREDS_FILE)
                    console.print("[#a6e3a1]Credentials reset.[/#a6e3a1]")
                    # Re-prompt for credentials immediately
                    new_id, new_secret = get_spotify_credentials()
                    if new_id and new_secret:
                        # Reinitialize Spotify client with new credentials
                        sp = initialize_spotify_client(new_id, new_secret)
                        if sp is not None:
                            console.print("[bold #a6e3a1]✅ Spotify API reconnected successfully![/bold #a6e3a1]")
                        else:
                            Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                            return
                    else:
                        console.print("[#f38ba8]No valid credentials provided.[/#f38ba8]")
                        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                        return
                except Exception as e:
                    console.print(f"[#f38ba8]Failed to reset credentials file: {e}[/#f38ba8]")
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
    try:
        query = f"track:{song_name} artist:{artist_name}"
        results = sp.search(q=query, type="track", limit=1)

        if not results['tracks']['items']:
            console.print("[bold #f38ba8]❌ No cover art found for this track.[/bold #f38ba8]")
            Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
            return

        track = results['tracks']['items'][0]
        cover_url = track['album']['images'][0]['url']

        console.print(f"[#94e2d5]🎨 Cover Art Found:[/#94e2d5] {cover_url}")
        
        # Show track name and artist for confirmation
        track_name = track['name']
        track_artist = track['artists'][0]['name']
        console.print(f"[#94e2d5]Track:[/#94e2d5] {track_name} by {track_artist}")
        
    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error searching for track:[/bold #f38ba8] {e}")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return

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
    try:
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()
        image_data = response.content
    except requests.RequestException as e:
        console.print(f"[bold #f38ba8]❌ Failed to download cover art:[/bold #f38ba8] {e}")
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