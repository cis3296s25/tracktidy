"""
Audio and playlist file organizer UI for TrackTidy
"""
import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table

from src.tracktidy.core.organizer import organize_files_by_format

console = Console()

async def organizer_ui():
    """
    User interface for organizing audio and playlist files by format
    """
    while True:
        console.clear()
        
        # Display header
        header = Text("🗂️ File Organizer 🗂️", style="bold #f5c2e7")
        console.print(Panel(header, style="bold #cba6f7"))
        
        console.print("\n[bold #89b4fa]This tool helps you organize your audio and playlist files by format.[/bold #89b4fa]")
        console.print("[#89dceb]Files will be moved to separate folders based on their format (mp3_files, wav_files, m3u_files, pls_files, etc.)[/#89dceb]\n")
        
        # Display organizer options
        console.print("[#89b4fa]1.[/#89b4fa][bold] Organize Files by Format[/bold]")
        console.print("[#f38ba8]2.[/#f38ba8][bold] Return to Main Menu[/bold]")
        
        choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2"])
        
        if choice == "2":
            return
        
        # If we get here, the user selected option 1 (Organize Audio Files by Format)
        await organize_files()

async def organize_files():
    """
    Organize audio files by format
    """
    
    # Get directory containing audio files
    default_dir = os.path.expanduser("~/Music")
    if not os.path.exists(default_dir):
        default_dir = os.getcwd()
    
    directory = Prompt.ask(
        "[bold #a6e3a1]Enter the directory containing your audio files[/bold #a6e3a1]",
        default=default_dir
    )
    
    # Validate directory
    if not os.path.isdir(directory):
        console.print(f"[bold #f38ba8]Error: {directory} is not a valid directory[/bold #f38ba8]")
        input("\nPress Enter to return to the organizer menu...")
        return
    
    # Confirm with the user
    console.print(f"\n[bold #fab387]This will organize all audio and playlist files in {directory} into format-specific folders.[/bold #fab387]")
    console.print("[#f38ba8]Files will be moved from their current location to new folders.[/#f38ba8]")
    
    confirm = Prompt.ask(
        "[bold #f5c2e7]Do you want to continue?[/bold #f5c2e7]",
        choices=["y", "n"],
        default="y"
    )
    
    if confirm.lower() != "y":
        console.print("[bold #f38ba8]Operation cancelled.[/bold #f38ba8]")
        input("\nPress Enter to return to the organizer menu...")
        return
    
    # Organize the files
    console.print("\n[bold #89b4fa]Organizing files...[/bold #89b4fa]")
    
    try:
        success, stats, errors = await organize_files_by_format(directory)
        
        if success:
            console.print(f"\n[bold #a6e3a1]✅ Successfully organized {stats['moved_files']} of {stats['total_files']} files![/bold #a6e3a1]")
            
            # Display stats in a table
            table = Table(title="Organization Summary", show_header=True, header_style="bold #cba6f7")
            table.add_column("Format", style="#89b4fa")
            table.add_column("Files", style="#a6e3a1")
            table.add_column("Folder", style="#89dceb")
            
            for format_name, count in stats['formats'].items():
                folder_name = f"{format_name}_files"
                folder_path = os.path.join(directory, folder_name)
                table.add_row(format_name, str(count), folder_path)
            
            console.print(table)
            
            if errors:
                console.print("\n[bold #f38ba8]The following errors occurred:[/bold #f38ba8]")
                for error in errors:
                    console.print(f"[#f38ba8]- {error}[/#f38ba8]")
        else:
            console.print(f"\n[bold #f38ba8]❌ Failed to organize audio files.[/bold #f38ba8]")
            
            if errors:
                console.print("\n[bold #f38ba8]Errors:[/bold #f38ba8]")
                for error in errors:
                    console.print(f"[#f38ba8]- {error}[/#f38ba8]")
    
    except Exception as e:
        console.print(f"\n[bold #f38ba8]❌ Error: {e}[/bold #f38ba8]")
    
    input("\nPress Enter to return to the organizer menu...")