"""
Audio file organizer module for TrackTidy
Organizes audio files by format into separate folders
"""
import os
import shutil
from typing import Dict, List, Tuple
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

# Common audio file extensions
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']

def scan_directory_for_audio_files(directory: str) -> List[str]:
    """
    Scan a directory for audio files
    
    Args:
        directory: Directory to scan for audio files
        
    Returns:
        List of audio file paths
    """
    audio_files = []
    
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in AUDIO_EXTENSIONS:
                    audio_files.append(file_path)
    except Exception as e:
        console.print(f"[bold #f38ba8]Error scanning directory: {e}[/bold #f38ba8]")
    
    return audio_files

def group_files_by_format(files: List[str]) -> Dict[str, List[str]]:
    """
    Group audio files by their format
    
    Args:
        files: List of audio file paths
        
    Returns:
        Dictionary mapping format extensions to lists of file paths
    """
    grouped_files = {}
    
    for file_path in files:
        file_ext = os.path.splitext(file_path)[1].lower()
        # Remove the dot from the extension
        format_name = file_ext[1:] if file_ext.startswith('.') else file_ext
        
        if format_name not in grouped_files:
            grouped_files[format_name] = []
        
        grouped_files[format_name].append(file_path)
    
    return grouped_files

def create_format_folders(base_directory: str, formats: List[str]) -> Dict[str, str]:
    """
    Create folders for each audio format
    
    Args:
        base_directory: Base directory where format folders will be created
        formats: List of audio formats
        
    Returns:
        Dictionary mapping format names to folder paths
    """
    format_folders = {}
    
    for format_name in formats:
        folder_name = f"{format_name}_files"
        folder_path = os.path.join(base_directory, folder_name)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            format_folders[format_name] = folder_path
        except Exception as e:
            console.print(f"[bold #f38ba8]Error creating folder for {format_name}: {e}[/bold #f38ba8]")
    
    return format_folders

def move_files_to_format_folders(grouped_files: Dict[str, List[str]], format_folders: Dict[str, str]) -> Tuple[int, int, List[str]]:
    """
    Move audio files to their respective format folders
    
    Args:
        grouped_files: Dictionary mapping format extensions to lists of file paths
        format_folders: Dictionary mapping format names to folder paths
        
    Returns:
        Tuple containing (number of files moved, total number of files, list of errors)
    """
    total_files = sum(len(files) for files in grouped_files.values())
    moved_files = 0
    errors = []
    
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold green]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("Moving files...", total=total_files)
        
        for format_name, files in grouped_files.items():
            if format_name in format_folders:
                folder_path = format_folders[format_name]
                
                for file_path in files:
                    try:
                        # Get the filename without the path
                        file_name = os.path.basename(file_path)
                        # Create the destination path
                        dest_path = os.path.join(folder_path, file_name)
                        
                        # Check if the file already exists in the destination
                        if os.path.exists(dest_path):
                            # Add a number to the filename to make it unique
                            base_name, ext = os.path.splitext(file_name)
                            counter = 1
                            while os.path.exists(dest_path):
                                new_name = f"{base_name}_{counter}{ext}"
                                dest_path = os.path.join(folder_path, new_name)
                                counter += 1
                        
                        # Move the file
                        shutil.move(file_path, dest_path)
                        moved_files += 1
                    except Exception as e:
                        error_msg = f"Error moving {file_path}: {e}"
                        errors.append(error_msg)
                    
                    # Update progress
                    progress.update(task, advance=1)
    
    return moved_files, total_files, errors

async def organize_audio_files_by_format(directory: str) -> Tuple[bool, Dict[str, int], List[str]]:
    """
    Organize audio files in a directory by their format
    
    Args:
        directory: Directory containing audio files to organize
        
    Returns:
        Tuple containing (success status, stats dictionary, list of errors)
    """
    # Validate directory
    if not os.path.isdir(directory):
        return False, {}, [f"Invalid directory: {directory}"]
    
    # Scan directory for audio files
    console.print(f"[bold #89b4fa]Scanning {directory} for audio files...[/bold #89b4fa]")
    audio_files = scan_directory_for_audio_files(directory)
    
    if not audio_files:
        return False, {}, ["No audio files found in the directory"]
    
    # Group files by format
    grouped_files = group_files_by_format(audio_files)
    
    # Create format folders
    format_folders = create_format_folders(directory, list(grouped_files.keys()))
    
    # Move files to format folders
    console.print("[bold #89b4fa]Moving files to format folders...[/bold #89b4fa]")
    moved_files, total_files, errors = move_files_to_format_folders(grouped_files, format_folders)
    
    # Prepare stats
    stats = {
        "total_files": total_files,
        "moved_files": moved_files,
        "formats": {format_name: len(files) for format_name, files in grouped_files.items()}
    }
    
    return moved_files > 0, stats, errors