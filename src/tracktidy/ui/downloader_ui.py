"""
Music downloader UI for TrackTidy
"""
from rich.console import Console
from rich.prompt import Prompt

from ..core.downloader import MusicDownloader

console = Console()


async def download_ui():
    """Interactive music downloader UI for TrackTidy"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Music Downloader 🎵[/bold #f5e0dc]\n")
    
    # Provider selection
    console.print("[#89b4fa]1.[/#89b4fa][bold] Spotify (YouTube Download)[/bold]")
    console.print("[#b4befe]2.[/#b4befe][bold] Tidal (Premium Required)[/bold]")
    console.print("[#f38ba8]3.[/#f38ba8][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask("\n[#cba6f7]Select a provider[/#cba6f7]", choices=["1", "2", "3"])
    
    if choice == "3":
        return
    
    downloader = MusicDownloader()
    
    if choice == "1":
        # UI for Spotify-YouTube provider
        # To be implemented
        pass
            
    elif choice == "2":
        # UI for Tidal provider
        # To be implemented
        pass
    
    # Pause before returning to the menu
    Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
