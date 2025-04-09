"""
Music downloader UI for TrackTidy
"""
import asyncio
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from ..core.downloader import MusicDownloader

# Define Catppuccin colors
COLORS = {
    'mauve': '#cba6f7',        # Progress bar color
    'blue': '#89b4fa',         # Info messages
    'sky': '#89dceb',          # Prompts
    'green': '#a6e3a1',        # Success messages
    'red': '#f38ba8',          # Error messages
    'peach': '#fab387',        # Warnings
    'yellow': '#f9e2af',       # Status messages
    'teal': '#94e2d5'          # File paths
}

console = Console()


async def download_ui():
    """Interactive music downloader UI for TrackTidy"""
    console.print(f"\n[bold {COLORS['mauve']}]🎵 TrackTidy - Music Downloader 🎵[/bold {COLORS['mauve']}]\n")
    
    # Provider selection
    console.print(f"[{COLORS['blue']}]1.[/{COLORS['blue']}][bold] Spotify (YouTube Download)[/bold]")
    console.print(f"[{COLORS['blue']}]2.[/{COLORS['blue']}][bold] Tidal (Premium Required)[/bold] [{COLORS['red']}](Coming Soon)[/{COLORS['red']}]")
    console.print(f"[{COLORS['red']}]3.[/{COLORS['red']}][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask(f"\n[{COLORS['mauve']}]Select a provider[/{COLORS['mauve']}]", choices=["1", "2", "3"])
    
    if choice == "3":
        return
    
    if choice == "2":
        console.print(f"[bold {COLORS['red']}]Tidal integration coming soon![/bold {COLORS['red']}]")
        Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to return to the provider selection...[/{COLORS['blue']}]")
        await download_ui()  # Return to provider selection
        return
    
    downloader = MusicDownloader()
    
    # Initialize SpotifyYouTube provider - without using console.status to avoid UI blocking
    console.print(f"[bold {COLORS['blue']}]Initializing Spotify...[/bold {COLORS['blue']}]")
    try:
        # Check if debug mode is needed for troubleshooting
        debug_mode = False
        if os.environ.get('TRACKTIDY_DEBUG') == '1':
            console.print(f"[{COLORS['blue']}]Debug mode enabled - API responses will be shown in detail[/{COLORS['blue']}]")
            debug_mode = True
            
        success = await downloader.initialize_provider("spotify-youtube", {'debug_mode': debug_mode})
        if not success:
            console.print(f"[bold {COLORS['red']}]Failed to initialize Spotify provider. Check your credentials.[/bold {COLORS['red']}]")
            Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to return to the main menu...[/{COLORS['blue']}]")
            return
    except Exception as e:
        console.print(f"[bold {COLORS['red']}]Error: {str(e)}[/bold {COLORS['red']}]")
        Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to return to the main menu...[/{COLORS['blue']}]")
        return
    
    # Show options for Spotify-YouTube provider
    while True:
        console.clear()
        console.print(f"\n[bold {COLORS['mauve']}]🎵 TrackTidy - Spotify Music Downloader 🎵[/bold {COLORS['mauve']}]\n")
        
        console.print(f"[{COLORS['blue']}]1.[/{COLORS['blue']}][bold] Download from URL (Track, Album, Playlist)[/bold]")
        console.print(f"[{COLORS['blue']}]2.[/{COLORS['blue']}][bold] Search and Download[/bold]")
        console.print(f"[{COLORS['red']}]3.[/{COLORS['red']}][bold] Return to Main Menu[/bold]")
        
        option = Prompt.ask(f"\n[{COLORS['mauve']}]Select an option[/{COLORS['mauve']}]", choices=["1", "2", "3"])
        
        if option == "3":
            return
        
        if option == "1":
            # Download from URL
            url = Prompt.ask(f"[{COLORS['sky']}]Enter Spotify URL (track, album, or playlist)[/{COLORS['sky']}]")
            
            if not ("spotify.com" in url or "open.spotify.com" in url):
                console.print(f"[bold {COLORS['red']}]Invalid Spotify URL. Please enter a valid URL.[/bold {COLORS['red']}]")
                Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to continue...[/{COLORS['blue']}]")
                continue
            
            # Ask for output directory
            default_dir = os.path.join(os.path.expanduser("~"), "Music", "TrackTidy")
            output_dir = Prompt.ask(
                f"[{COLORS['sky']}]Enter output directory[/{COLORS['sky']}]", 
                default=default_dir
            )
            
            # Create the directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Process download
            with console.status(f"[bold {COLORS['yellow']}]Processing URL...[/bold {COLORS['yellow']}]", spinner="dots"):
                try:
                    # Analyze URL first to provide better progress information
                    if "track" in url:
                        console.print(f"[{COLORS['sky']}]Downloading a single track...[/{COLORS['sky']}]")
                        content_type = "track"
                    elif "album" in url:
                        console.print(f"[{COLORS['sky']}]Downloading an album...[/{COLORS['sky']}]")
                        content_type = "album"
                    elif "playlist" in url:
                        console.print(f"[{COLORS['sky']}]Downloading a playlist...[/{COLORS['sky']}]")
                        content_type = "playlist"
                    else:
                        console.print(f"[{COLORS['sky']}]Downloading from Spotify...[/{COLORS['sky']}]")
                        content_type = "unknown"
                except Exception:
                    content_type = "unknown"
            
            console.print(f"\n[bold {COLORS['green']}]Starting download...[/bold {COLORS['green']}]")
            try:
                quality = 2  # Highest quality
                
                with Progress(
                    "[progress.description]{task.description}",
                    BarColumn(bar_width=None, complete_style=COLORS['mauve'], finished_style=COLORS['mauve'], pulse_style=COLORS['mauve']),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    refresh_per_second=15,  # Higher refresh rate for smoother animation
                ) as progress:
                    # Create a task that will be updated during download
                    task = progress.add_task("[cyan]Downloading...", total=100, start=False)
                    
                    # For URL downloads, we need to determine the type
                    files = []
                    
                    if "track" in url:
                        # For single tracks, display detailed progress
                        # Extract track ID
                        item_type, item_id = downloader.current_provider.extract_spotify_id(url)
                        
                        # Get track info
                        track = await downloader.current_provider.get_track(item_id)
                        track_name = track.title
                        progress.update(task, description=f"[cyan]Downloading: {track_name}")
                        
                        # Define a track progress handler
                        def track_progress_handler(stage, percent, status):
                            # Update the main progress bar
                            progress.update(task, completed=int(percent * 100))
                            # Also update the description to show status
                            progress.update(task, description=status)
                            
                        # Download the track
                        file_path = await downloader.current_provider.download_track(
                            track, 
                            output_dir, 
                            quality,
                            progress_callback=track_progress_handler
                        )
                        # Save the track
                        files = [file_path] if file_path else []
                        
                    elif "album" in url or "playlist" in url:
                        # Extract the ID and call the specific function for detailed progress tracking
                        item_type, item_id = downloader.current_provider.extract_spotify_id(url)
                        
                        # Define a progress callback that updates the single progress bar
                        def update_progress(current, total, song_name):
                            # Calculate percentage and update bar
                            percent = current/total if total else 0
                            progress.update(task, completed=int(percent * 100))
                            # Update description to show current track
                            progress.update(task, description=f"[cyan]Downloading {current}/{total}: {song_name}")
                            
                        if item_type == "album":
                            files = await downloader.download_album(item_id, output_dir, quality, update_progress)
                        elif item_type == "playlist":
                            files = await downloader.download_playlist(item_id, output_dir, quality, update_progress)
                    else:
                        # Generic fallback
                        progress.update(task, start=True)
                        files = await downloader.download_from_url(url, output_dir, quality)
                        progress.update(task, completed=100)
                # Similar improvements for URL-based downloads
                if files:
                    success_count = len([f for f in files if f])
                    console.print(f"\n[bold {COLORS['green']}]✅ Successfully downloaded {success_count} files![/bold {COLORS['green']}]")
                    console.print(f"[{COLORS['teal']}]Files saved to: {output_dir}[/{COLORS['teal']}]")
                else:
                    console.print(f"[bold {COLORS['red']}]❌ No files were downloaded.[/bold {COLORS['red']}]")
            except Exception as e:
                console.print(f"[bold {COLORS['red']}]❌ Error:[/bold {COLORS['red']}] {str(e)}")
            
            Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to continue...[/{COLORS['blue']}]")
            
        elif option == "2":
            # Search and download
            console.print(f"\n[{COLORS['mauve']}]Select content type to search:[/{COLORS['mauve']}]")
            console.print(f"[{COLORS['blue']}]1.[/{COLORS['blue']}][bold] Track[/bold]")
            console.print(f"[{COLORS['blue']}]2.[/{COLORS['blue']}][bold] Album[/bold]")
            console.print(f"[{COLORS['blue']}]3.[/{COLORS['blue']}][bold] Playlist[/bold]")
            
            type_choice = Prompt.ask(f"\n[{COLORS['mauve']}]Content type[/{COLORS['mauve']}]", choices=["1", "2", "3"], default="1")
            media_type = "track" if type_choice == "1" else "album" if type_choice == "2" else "playlist"
            
            # Get search query with validation
            query = ""
            while not query.strip():
                query = Prompt.ask(f"[{COLORS['sky']}]Enter search query for {media_type}[/{COLORS['sky']}]")
                if not query.strip():
                    console.print(f"[bold {COLORS['red']}]Search query cannot be empty. Please try again.[/bold {COLORS['red']}]")
            
            # Process download
            with console.status(f"[bold {COLORS['yellow']}]Searching...[/bold {COLORS['yellow']}]", spinner="dots"):
                try:
                    results = await downloader.search_music(query, media_type, limit=10)
                    if not results:
                        console.print(f"[bold {COLORS['red']}]No {media_type}s found matching '{query}'[/bold {COLORS['red']}]")
                        Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to continue...[/{COLORS['blue']}]")
                        continue
                except Exception as e:
                    console.print(f"[bold {COLORS['red']}]Error searching: {str(e)}[/bold {COLORS['red']}]")
                    Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to continue...[/{COLORS['blue']}]")
                    continue
            
            # Display search results
            console.print(f"\n[bold {COLORS['green']}]Found {len(results)} {media_type}s:[/bold {COLORS['green']}]")
            
            for i, item in enumerate(results):
                if media_type == "track":
                    console.print(f"[{COLORS['blue']}]{i+1}.[/{COLORS['blue']}] {item['name']} by {item['artist']} ({item['album']})")
                elif media_type == "album":
                    console.print(f"[{COLORS['blue']}]{i+1}.[/{COLORS['blue']}] {item['name']} by {item['artist']}")
                elif media_type == "playlist":
                    console.print(f"[{COLORS['blue']}]{i+1}.[/{COLORS['blue']}] {item['name']} by {item['owner']} ({item['tracks_count']} tracks)")
            
            # Select an item to download
            choice_num = Prompt.ask(
                f"\n[{COLORS['mauve']}]Enter number to download (0 to cancel)[/{COLORS['mauve']}]",
                choices=[str(i) for i in range(len(results) + 1)],
                default="1"
            )
            
            if choice_num == "0":
                console.print(f"[bold {COLORS['red']}]Download canceled.[/bold {COLORS['red']}]")
                # Pause briefly so user can see the message
                await asyncio.sleep(1)
                continue
                
            selected_item = results[int(choice_num) - 1]
            
            # Ask for output directory
            default_dir = os.path.join(os.path.expanduser("~"), "Music", "TrackTidy")
            output_dir = Prompt.ask(
                f"[{COLORS['sky']}]Enter output directory[/{COLORS['sky']}]", 
                default=default_dir
            )
            
            # Create the directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Download the selected item
            console.print(f"\n[bold {COLORS['green']}]Downloading {selected_item['name']}...[/bold {COLORS['green']}]")
            
            try:
                quality = 2  # Highest quality
                
                with Progress(
                    "[progress.description]{task.description}",
                    BarColumn(bar_width=None, complete_style=COLORS['mauve'], finished_style=COLORS['mauve'], pulse_style=COLORS['mauve']),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    refresh_per_second=15,  # Higher refresh rate for smoother animation
                ) as progress:
                    task = progress.add_task("[cyan]Preparing download...", total=100, start=True)
                    
                    # Define a progress handler for multiple tracks
                    def update_progress(current, total, song_name):
                        progress.update(task, completed=current*100//total if total else 0, 
                                       description=f"[cyan]Downloading {current}/{total}: {song_name}")
                    
                    if media_type == "track":
                        # Signal that we're downloading a track
                        progress.update(task, description=f"[cyan]Downloading: {selected_item['name']}")
                        
                        # Define a track progress handler that will update the progress bar
                        def track_progress_handler(stage, percent, status):
                            # Update the progress percentage
                            progress.update(task, completed=int(percent * 100))
                            # Update the description to show the current status
                            progress.update(task, description=status)
                            
                        # Download a single track
                        file_path = await downloader.download_track(
                            selected_item['id'], 
                            output_dir, 
                            quality,
                            progress_callback=track_progress_handler
                        )
                        
                        files = [file_path] if file_path else []
                    elif media_type == "album":
                        files = await downloader.download_album(selected_item['id'], output_dir, quality, update_progress)
                    elif media_type == "playlist":
                        files = await downloader.download_playlist(selected_item['id'], output_dir, quality, update_progress)
                
                # If we downloaded files, show a link to the folder
                if files and any(files):
                    success_count = len([f for f in files if f])
                    console.print(f"\n[bold {COLORS['green']}]✅ Successfully downloaded {success_count} files![/bold {COLORS['green']}]")
                    console.print(f"[{COLORS['teal']}]Files saved to: {output_dir}[/{COLORS['teal']}]")
                else:
                    console.print(f"[bold {COLORS['red']}]❌ No files were downloaded.[/bold {COLORS['red']}]")
            except Exception as e:
                console.print(f"[bold {COLORS['red']}]❌ Error:[/bold {COLORS['red']}] {str(e)}")
            
            Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to continue...[/{COLORS['blue']}]")
            
    # Pause before returning to the menu
    Prompt.ask(f"\n[{COLORS['blue']}]Press Enter to return to the main menu...[/{COLORS['blue']}]")
