"""
Music downloader UI for TrackTidy
"""
import asyncio
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from ..core.downloader import MusicDownloader

console = Console()


async def download_ui():
    """Interactive music downloader UI for TrackTidy"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Music Downloader 🎵[/bold #f5e0dc]\n")
    
    # Provider selection
    console.print("[#89b4fa]1.[/#89b4fa][bold] Spotify (YouTube Download)[/bold]")
    console.print("[#b4befe]2.[/#b4befe][bold] Tidal (Premium Required)[/bold] [#f38ba8](Coming Soon)[/#f38ba8]")
    console.print("[#f38ba8]3.[/#f38ba8][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask("\n[#cba6f7]Select a provider[/#cba6f7]", choices=["1", "2", "3"])
    
    if choice == "3":
        return
    
    if choice == "2":
        console.print("[bold #f38ba8]Tidal integration coming soon![/bold #f38ba8]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the provider selection...[/#89b4fa]")
        await download_ui()  # Return to provider selection
        return
    
    downloader = MusicDownloader()
    
    # Initialize SpotifyYouTube provider - without using console.status to avoid UI blocking
    console.print("[bold #89b4fa]Initializing Spotify...[/bold #89b4fa]")
    try:
        # Check if debug mode is needed for troubleshooting
        debug_mode = False
        if os.environ.get('TRACKTIDY_DEBUG') == '1':
            console.print("[#b4befe]Debug mode enabled - API responses will be shown in detail[/#b4befe]")
            debug_mode = True
            
        success = await downloader.initialize_provider("spotify-youtube", {'debug_mode': debug_mode})
        if not success:
            console.print("[bold #f38ba8]Failed to initialize Spotify provider. Check your credentials.[/bold #f38ba8]")
            Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
            return
    except Exception as e:
        console.print(f"[bold #f38ba8]Error: {str(e)}[/bold #f38ba8]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
        return
    
    # Show options for Spotify-YouTube provider
    while True:
        console.clear()
        console.print("\n[bold #f5e0dc]🎵 TrackTidy - Spotify Music Downloader 🎵[/bold #f5e0dc]\n")
        
        console.print("[#89b4fa]1.[/#89b4fa][bold] Download from URL (Track, Album, Playlist)[/bold]")
        console.print("[#b4befe]2.[/#b4befe][bold] Search and Download[/bold]")
        console.print("[#f38ba8]3.[/#f38ba8][bold] Return to Main Menu[/bold]")
        
        option = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2", "3"])
        
        if option == "3":
            return
        
        if option == "1":
            # Download from URL
            url = Prompt.ask("[#89dceb]Enter Spotify URL (track, album, or playlist)[/#89dceb]")
            
            if not ("spotify.com" in url or "open.spotify.com" in url):
                console.print("[bold #f38ba8]Invalid Spotify URL. Please enter a valid URL.[/bold #f38ba8]")
                Prompt.ask("\n[#89b4fa]Press Enter to continue...[/#89b4fa]")
                continue
            
            # Ask for output directory
            default_dir = os.path.join(os.path.expanduser("~"), "Music", "TrackTidy")
            output_dir = Prompt.ask(
                "[#89dceb]Enter output directory[/#89dceb]", 
                default=default_dir
            )
            
            # Create the directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Process download
            with console.status("[bold #f9e2af]Processing URL...[/bold #f9e2af]", spinner="dots"):
                try:
                    # Analyze URL first to provide better progress information
                    if "track" in url:
                        console.print("[#89dceb]Downloading a single track...[/#89dceb]")
                        content_type = "track"
                    elif "album" in url:
                        console.print("[#89dceb]Downloading an album...[/#89dceb]")
                        content_type = "album"
                    elif "playlist" in url:
                        console.print("[#89dceb]Downloading a playlist...[/#89dceb]")
                        content_type = "playlist"
                    else:
                        console.print("[#89dceb]Downloading from Spotify...[/#89dceb]")
                        content_type = "unknown"
                except Exception:
                    content_type = "unknown"
            
            console.print("\n[bold #a6e3a1]Starting download...[/bold #a6e3a1]")
            try:
                quality = 2  # Highest quality
                
                with Progress(
                    "[progress.description]{task.description}",
                    BarColumn(bar_width=None, complete_style="#cba6f7", finished_style="#cba6f7", pulse_style="#cba6f7"),
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
                if files:
                    console.print(f"\n[bold #a6e3a1]✅ Successfully downloaded {len(files)} files![/bold #a6e3a1]")
                    console.print(f"[#94e2d5]Files saved to: {output_dir}[/#94e2d5]")
                else:
                    console.print("[bold #f38ba8]❌ No files were downloaded.[/bold #f38ba8]")
            except Exception as e:
                console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {str(e)}")
            
            Prompt.ask("\n[#89b4fa]Press Enter to continue...[/#89b4fa]")
            
        elif option == "2":
            # Search and download
            console.print("\n[#cba6f7]Select content type to search:[/#cba6f7]")
            console.print("[#89b4fa]1.[/#89b4fa][bold] Track[/bold]")
            console.print("[#b4befe]2.[/#b4befe][bold] Album[/bold]")
            console.print("[#f5c2e7]3.[/#f5c2e7][bold] Playlist[/bold]")
            
            type_choice = Prompt.ask("\n[#cba6f7]Content type[/#cba6f7]", choices=["1", "2", "3"], default="1")
            media_type = "track" if type_choice == "1" else "album" if type_choice == "2" else "playlist"
            
            query = Prompt.ask(f"[#89dceb]Enter search query for {media_type}[/#89dceb]")
            
            # Process download
            with console.status("[bold #f9e2af]Searching...[/bold #f9e2af]", spinner="dots"):
                try:
                    results = await downloader.search_music(query, media_type, limit=10)
                    if not results:
                        console.print(f"[bold #f38ba8]No {media_type}s found matching '{query}'[/bold #f38ba8]")
                        Prompt.ask("\n[#89b4fa]Press Enter to continue...[/#89b4fa]")
                        continue
                except Exception as e:
                    console.print(f"[bold #f38ba8]Error searching: {str(e)}[/bold #f38ba8]")
                    Prompt.ask("\n[#89b4fa]Press Enter to continue...[/#89b4fa]")
                    continue
            
            # Display search results
            console.print(f"\n[bold #a6e3a1]Found {len(results)} {media_type}s:[/bold #a6e3a1]")
            
            for i, item in enumerate(results):
                if media_type == "track":
                    console.print(f"[#89b4fa]{i+1}.[/#89b4fa] {item['name']} by {item['artist']} ({item['album']})")
                elif media_type == "album":
                    console.print(f"[#89b4fa]{i+1}.[/#89b4fa] {item['name']} by {item['artist']}")
                elif media_type == "playlist":
                    console.print(f"[#89b4fa]{i+1}.[/#89b4fa] {item['name']} by {item['owner']} ({item['tracks_count']} tracks)")
            
            # Select an item to download
            choice_num = Prompt.ask(
                "\n[#cba6f7]Enter number to download (0 to cancel)[/#cba6f7]",
                choices=[str(i) for i in range(len(results) + 1)],
                default="1"
            )
            
            if choice_num == "0":
                console.print("[bold #f38ba8]Download canceled.[/bold #f38ba8]")
                # Pause briefly so user can see the message
                await asyncio.sleep(1)
                continue
                
            selected_item = results[int(choice_num) - 1]
            
            # Ask for output directory
            default_dir = os.path.join(os.path.expanduser("~"), "Music", "TrackTidy")
            output_dir = Prompt.ask(
                "[#89dceb]Enter output directory[/#89dceb]", 
                default=default_dir
            )
            
            # Create the directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Download the selected item
            console.print(f"\n[bold #a6e3a1]Downloading {selected_item['name']}...[/bold #a6e3a1]")
            
            try:
                # Always use highest quality
                quality = 2  # Highest quality
                
                with Progress(
                    "[progress.description]{task.description}",
                    BarColumn(bar_width=None, complete_style="#cba6f7", finished_style="#cba6f7", pulse_style="#cba6f7"),
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
                
                if files and any(files):
                    console.print(f"\n[bold #a6e3a1]✅ Successfully downloaded {len([f for f in files if f])} files![/bold #a6e3a1]")
                    console.print(f"[#94e2d5]Files saved to: {output_dir}[/#94e2d5]")
                else:
                    console.print("[bold #f38ba8]❌ No files were downloaded.[/bold #f38ba8]")
            except Exception as e:
                console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {str(e)}")
            
            Prompt.ask("\n[#89b4fa]Press Enter to continue...[/#89b4fa]")
            
    # Pause before returning to the menu
    Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
