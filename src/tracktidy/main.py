"""
Main entry point for TrackTidy application
"""
import asyncio
import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt

# Import services
from src.tracktidy.services.ffmpeg import download_ffmpeg_to_app_dir, prompt_and_install_ffmpeg

# Import core modules
from src.tracktidy.core.metadata import edit_metadata
from src.tracktidy.core.audio import convert_audio
from src.tracktidy.core.cover_art import fetch_cover_art
from src.tracktidy.batch.processor import batch_process

console = Console(force_terminal=True, color_system="truecolor")

LOGO = Text("""
████████╗██████╗  █████╗  ██████╗██╗  ██╗████████╗██╗██████╗ ██╗   ██╗
╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝╚══██╔══╝██║██╔══██╗╚██╗ ██╔╝
   ██║   ██████╔╝███████║██║     █████╔╝    ██║   ██║██║  ██║ ╚████╔╝ 
   ██║   ██╔══██╗██╔══██║██║     ██╔═██╗    ██║   ██║██║  ██║  ╚██╔╝  
   ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗   ██║   ██║██████╔╝   ██║   
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═════╝    ╚═╝   
""", style="bold gradient(#f5e0dc,#89b4fa)")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="TrackTidy - Music Manager for DJs and Music Enthusiasts")
    parser.add_argument("--download-ffmpeg", action="store_true", 
                      help="Download and install FFmpeg automatically (required for audio conversion)")
    return parser.parse_args()

async def main_menu():
    """Display and handle the main menu"""
    # Check if FFmpeg is installed and prompt to install if needed
    ffmpeg_available = prompt_and_install_ffmpeg()
    if not ffmpeg_available:
        console.print("\n[#89dceb]Audio conversion and some other features will be unavailable without FFmpeg.[/#89dceb]")
        console.print("[#89dceb]Press Enter to continue with limited functionality...[/#89dceb]")
        input()
        
    while True:
        # Print the ASCII Logo
        console.clear()
        console.print(Align.center(LOGO))

        title_panel = ("♫ TrackTidy - A DJ's Best Friend ♫"
                       "\n      ──────●───────────────"
                       "\n      ↻     ◁   ||   ▷     ↺")

        # Welcome panel and options
        console.print(Align.center(Panel(title_panel, style="bold #cba6f7", expand=False)))
        console.print("\n[#89b4fa]1.[/#89b4fa][bold]Edit Metadata[/bold]")
        console.print("[#b4befe]2.[/#b4befe][bold]Convert Audio File[/bold]")
        console.print("[#f5c2e7]3.[/#f5c2e7][bold]Fetch Cover Art[/bold]")
        console.print("[#fab387]4.[/#fab387][bold]Batch Processing[/bold]")
        console.print("[#94e2d5]5.[/#94e2d5][bold]Music Downloader[/bold]")
        console.print("[#f38ba8]6.[/#f38ba8][bold]Exit[/bold]")

        choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2", "3", "4", "5", "6"])

        if choice == "1":
            await edit_metadata()
        elif choice == "2":
            await convert_audio()
        elif choice == "3":
            await fetch_cover_art()
        elif choice == "4":
            await batch_process()
        elif choice == "5":
            # Music downloader option
            from src.tracktidy.ui.downloader_ui import download_ui
            await download_ui()
        elif choice == "6":
            console.print("[#a6e3a1]❌ Exiting TrackTidy. Goodbye![/#a6e3a1]")
            break

def main():
    """Main entry point for the application"""
    args = parse_args()
    
    if args.download_ffmpeg:
        # User requested to download FFmpeg
        console.print("[bold #89b4fa]Starting FFmpeg download and installation...[/bold #89b4fa]")
        success = download_ffmpeg_to_app_dir()
        if success:
            console.print("\n[bold #a6e3a1]✅ FFmpeg installation successful![/bold #a6e3a1]")
            console.print("[#89dceb]You can now run TrackTidy normally to use all features.[/#89dceb]")
        else:
            console.print("\n[bold #f38ba8]❌ FFmpeg installation failed.[/bold #f38ba8]")
            console.print("[#89dceb]Please try again or install manually.[/#89dceb]")
        sys.exit(0 if success else 1)
    
    # Normal program execution
    asyncio.run(main_menu())

if __name__ == "__main__":
    main()
