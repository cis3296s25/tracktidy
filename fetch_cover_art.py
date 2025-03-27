import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from rich.console import Console
from rich.prompt import Prompt

console = Console()

# ✅ Replace with your own Spotify API credentials
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                           client_secret=SPOTIPY_CLIENT_SECRET))

async def fetch_cover_art():
    console.print("\n[bold #f5e0dc]🎵 TrackTidy Cover Art Fetcher 🎵[/bold #f5e0dc]\n")

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
    query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=query, type="track", limit=1)

    if not results['tracks']['items']:
        console.print("[bold #f38ba8]❌ No cover art found for this track.[/bold #f38ba8]")
        return

    track = results['tracks']['items'][0]
    cover_url = track['album']['images'][0]['url']

    console.print(f"[#94e2d5]🎨 Cover Art Found:[/#94e2d5] {cover_url}")

    # Get the MP3 file path from the user
    file_path = Prompt.ask("[#cba6f7]Enter the path to the MP3 file[/#cba6f7]").strip()

    # Download the cover image
    try:
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()
        image_data = response.content
    except requests.RequestException as e:
        console.print(f"[bold #f38ba8]❌ Failed to download cover art:[/bold #f38ba8] {e}")
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