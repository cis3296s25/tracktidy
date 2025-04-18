"""
File organization UI for TrackTidy
"""
import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.tracktidy.core.organizer import organize_files_by_format

console = Console()

async def organizer_ui():
    """
    User interface for organizing files by format
    """
    console.clear()
    
    # Display header
    header = Text("🗂️ File Organizer 🗂️", style="bold #f5c2e7")
    console.print(Panel(header, style="bold #cba6f7"))
    
    console.print("\n[bold #89b4fa]This tool helps you organize audio files by their format/extension.[/bold #89b4fa]")
    console.print("[#89dceb]Audio files will be moved to subdirectories named after their extensions (e.g., mp3_files, wav_files).[/#89dceb]\n")
    
    # Get directory to organize
    default_dir = os.path.expanduser("~/Music")
    if not os.path.exists(default_dir):
        default_dir = os.getcwd()
    
    directory = Prompt.ask(
        "[bold #a6e3a1]Enter the directory containing files to organize[/bold #a6e3a1]",
        default=default_dir
    )
    
    # Validate directory
    if not os.path.isdir(directory):
        console.print(f"[bold #f38ba8]Error: {directory} is not a valid directory[/bold #f38ba8]")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Ask if user wants to organize specific formats or all formats
    organize_specific = Confirm.ask(
        "[bold #fab387]Do you want to organize specific file formats only?[/bold #fab387]",
        default=False
    )
    
    extensions_to_organize = None
    if organize_specific:
        # Ask for specific extensions
        extensions_input = Prompt.ask(
            "[bold #b4befe]Enter file extensions to organize (comma-separated, e.g., 'mp3,wav,flac')[/bold #b4befe]"
        )
        
        # Parse and validate extensions
        if extensions_input:
            extensions_to_organize = [ext.strip().lower() for ext in extensions_input.split(',') if ext.strip()]
            
            if not extensions_to_organize:
                console.print("[bold #f38ba8]No valid extensions provided. Will organize all audio file formats.[/bold #f38ba8]")
                extensions_to_organize = None
        else:
            console.print("[bold #f38ba8]No extensions provided. Will organize all audio file formats.[/bold #f38ba8]")
    
    # Confirm before proceeding
    console.print(f"\n[bold #89b4fa]Ready to organize audio files in: {directory}[/bold #89b4fa]")
    if extensions_to_organize:
        console.print(f"[bold #89b4fa]Will organize these formats: {', '.join(extensions_to_organize)}[/bold #89b4fa]")
    else:
        console.print("[bold #89b4fa]Will organize all file formats[/bold #89b4fa]")
    
    proceed = Confirm.ask("[bold #cba6f7]Proceed with organization?[/bold #cba6f7]")
    if not proceed:
        console.print("[#f38ba8]Operation cancelled.[/#f38ba8]")
        input("\nPress Enter to return to the main menu...")
        return
    
    # Show progress spinner during organization
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[#89b4fa]Organizing audio files...[/#89b4fa]", total=1)
        
        # Call the core function to organize files
        files_moved, formats_organized, errors = await organize_files_by_format(
            directory, 
            extensions_to_organize
        )
        
        progress.update(task, completed=1)
    
    # Display results
    if files_moved > 0:
        console.print(f"\n[bold #a6e3a1]✅ Successfully organized {files_moved} audio files into {formats_organized} format directories![/bold #a6e3a1]")
    else:
        console.print("\n[bold #f38ba8]No files were organized.[/bold #f38ba8]")
    
    # Display any errors
    if errors:
        console.print("\n[#f38ba8]Errors or skipped files:[/#f38ba8]")
        for error in errors[:10]:  # Show only first 10 errors to avoid cluttering the screen
            console.print(f"[#f38ba8]- {error}[/#f38ba8]")
        
        if len(errors) > 10:
            console.print(f"[#f38ba8]... and {len(errors) - 10} more errors[/#f38ba8]")
    
    input("\nPress Enter to return to the main menu...")