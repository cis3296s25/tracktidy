"""
File organization module for TrackTidy
Organizes audio files in a directory by their format/extension
"""
import os
import shutil
from typing import Dict, List, Tuple, Set
from rich.console import Console

console = Console()

# List of common audio file extensions
AUDIO_EXTENSIONS = ['mp3', 'flac', 'wav', 'm4a', 'ogg', 'aac', 'wma', 'aiff', 'alac']

def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file without the dot
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension without the dot (lowercase)
    """
    _, ext = os.path.splitext(file_path)
    return ext[1:].lower() if ext else ""

def scan_directory(directory: str, audio_only: bool = True) -> Dict[str, List[str]]:
    """
    Scan a directory and categorize files by their extensions
    
    Args:
        directory: Directory to scan
        audio_only: If True, only include audio files (default: True)
        
    Returns:
        Dictionary mapping extensions to lists of file paths
    """
    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")
    
    # Dictionary to store files by extension
    files_by_extension = {}
    
    # Scan only the top level of the directory (no recursion)
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        # Skip directories
        if os.path.isdir(item_path):
            continue
        
        # Get file extension
        ext = get_file_extension(item_path)
        
        # Skip non-audio files if audio_only is True
        if audio_only and ext not in AUDIO_EXTENSIONS:
            continue
            
        if ext:
            if ext not in files_by_extension:
                files_by_extension[ext] = []
            files_by_extension[ext].append(item_path)
    
    return files_by_extension

def create_format_directories(directory: str, extensions: Set[str]) -> Dict[str, str]:
    """
    Create subdirectories for each file format
    
    Args:
        directory: Parent directory
        extensions: Set of file extensions to create directories for
        
    Returns:
        Dictionary mapping extensions to their directory paths
    """
    extension_dirs = {}
    
    for ext in extensions:
        # Create directory name (e.g., "mp3_files")
        dir_name = f"{ext}_files"
        dir_path = os.path.join(directory, dir_name)
        
        # Create directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        
        extension_dirs[ext] = dir_path
    
    return extension_dirs

async def organize_files_by_format(directory: str, extensions_to_organize: List[str] = None) -> Tuple[int, int, List[str]]:
    """
    Organize files in a directory by their format/extension
    
    Args:
        directory: Directory containing files to organize
        extensions_to_organize: Optional list of specific extensions to organize
                               (if None, organize all file types)
    
    Returns:
        Tuple containing (number of files moved, number of formats organized, list of errors)
    """
    # Scan directory for files
    try:
        files_by_extension = scan_directory(directory, audio_only=True)
    except ValueError as e:
        return 0, 0, [str(e)]
    
    # Filter extensions if specified
    if extensions_to_organize:
        extensions_to_organize = [ext.lower() for ext in extensions_to_organize]
        # Ensure only audio extensions are included
        extensions_to_organize = [ext for ext in extensions_to_organize if ext in AUDIO_EXTENSIONS]
        filtered_extensions = {}
        for ext, files in files_by_extension.items():
            if ext.lower() in extensions_to_organize:
                filtered_extensions[ext] = files
        files_by_extension = filtered_extensions
    
    # If no files found, return early
    if not files_by_extension:
        return 0, 0, ["No audio files found to organize"]
    
    # Create format directories
    extension_dirs = create_format_directories(directory, set(files_by_extension.keys()))
    
    # Move files to their respective format directories
    files_moved = 0
    errors = []
    
    for ext, files in files_by_extension.items():
        target_dir = extension_dirs[ext]
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_dir, file_name)
            
            # Skip if file already exists in target directory
            if os.path.exists(target_path):
                errors.append(f"Skipped {file_name}: File already exists in {target_dir}")
                continue
            
            try:
                # Move the file
                shutil.move(file_path, target_path)
                files_moved += 1
            except Exception as e:
                errors.append(f"Failed to move {file_name}: {str(e)}")
    
    return files_moved, len(files_by_extension), errors