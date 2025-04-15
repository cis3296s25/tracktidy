"""
Spotify API integration for TrackTidy
"""
import os
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from rich.console import Console
from rich.prompt import Prompt

console = Console()

# Path to store credentials
def get_creds_file_path():
    """Get the path to the Spotify credentials file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(base_dir, '.spotify_creds.json')

def validate_spotify_credentials(client_id, client_secret):
    """Test if the provided Spotify credentials are valid"""
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
    creds_file = get_creds_file_path()
    
    # Try to read from credentials file first
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as f:
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
        console.print("[#f38ba8]Enter -1 to return to the main menu[/#f38ba8]")
        client_id = Prompt.ask("[#cba6f7]Enter your Spotify Client ID[/#cba6f7]").strip()
        
        # Check if user wants to return to main menu
        if client_id == "-1":
            return "-1", "-1"  # Special return value to indicate return to main menu
            
        client_secret = Prompt.ask("[#cba6f7]Enter your Spotify Client Secret[/#cba6f7]").strip()
        
        # Also check after second prompt
        if client_secret == "-1":
            return "-1", "-1"  # Special return value to indicate return to main menu
        
        console.print("[#89dceb]Validating credentials...[/#89dceb]")
        
        # Validate the credentials
        if validate_spotify_credentials(client_id, client_secret):
            console.print("[bold #a6e3a1]✅ Credentials validated successfully![/bold #a6e3a1]")
            
            # Save for future use if both are provided and valid
            try:
                with open(creds_file, 'w') as f:
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

def initialize_spotify_client(client_id, client_secret):
    """Initialize or reinitialize the Spotify client"""
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

def search_track(spotify_client, song_name, artist_name):
    """Search for a track on Spotify and return its cover art URL"""
    try:
        query = f"track:{song_name} artist:{artist_name}"
        results = spotify_client.search(q=query, type="track", limit=1)

        if not results['tracks']['items']:
            return None, None, None, None
            
        track = results['tracks']['items'][0]
        cover_url = track['album']['images'][0]['url']
        track_name = track['name']
        track_artist = track['artists'][0]['name']
        album_name = track['album']['name']
        
        return cover_url, track_name, track_artist, album_name
    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error searching for track:[/bold #f38ba8] {e}")
        return None, None, None, None

def download_cover_art(cover_url):
    """Download cover art from the given URL"""
    try:
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        console.print(f"[bold #f38ba8]❌ Failed to download cover art:[/bold #f38ba8] {e}")
        return None

def reset_spotify_credentials():
    """Delete or reset the Spotify credentials file"""
    creds_file = get_creds_file_path()
    
    if os.path.exists(creds_file):
        try:
            # Option 1: Delete the file
            os.remove(creds_file)
            console.print("[bold #a6e3a1]✅ Spotify credentials have been reset![/bold #a6e3a1]")
            return True
        except Exception as e:
            console.print(f"[bold #f38ba8]❌ Failed to reset Spotify credentials:[/bold #f38ba8] {e}")
            return False
    else:
        console.print("[#89dceb]No stored Spotify credentials found.[/#89dceb]")
        return True  # Return True since there's nothing to reset
