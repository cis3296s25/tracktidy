import os
import asyncio
import glob
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Import existing modules
from metadata_editor import edit_metadata_file
from audio_converter import convert_audio_file

console = Console()

async def batch_process():
    """Main batch processing function that presents batch operation options"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Batch Processor 🎵[/bold #f5e0dc]\n")
    
    console.print("[#89b4fa]1.[/#89b4fa][bold] Batch Metadata Editing[/bold]")
    console.print("[#b4befe]2.[/#b4befe][bold] Batch Audio Conversion[/bold]")
    console.print("[#f38ba8]3.[/#f38ba8][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2", "3"])
    
    if choice == "1":
        await batch_metadata()
    elif choice == "2":
        await batch_convert()
    # Option 3 just returns to main menu

async def get_files_for_batch(file_type="audio", extensions=None):
    """Get a list of files for batch processing"""
    if extensions is None:
        if file_type == "audio":
            extensions = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac']
        elif file_type == "mp3":
            extensions = ['.mp3']
    
    console.print("\n[#89dceb]Batch processing allows you to process multiple files at once.[/#89dceb]")
    console.print(f"[#89dceb]Supported extensions: {', '.join(extensions)}[/#89dceb]")
    
    while True:
        # Ask for directory
        directory = Prompt.ask("[#cba6f7]Enter directory path containing files to process[/#cba6f7]").strip()
        
        if not os.path.isdir(directory):
            console.print("[bold #f38ba8]❌ Error: Directory not found![/bold #f38ba8]")
            continue
        
        # Find all files with the specified extensions
        files = []
        seen_paths = set()  # Track seen file paths to avoid duplicates
        
        for ext in extensions:
            pattern = os.path.join(directory, f"*{ext}")
            for file_path in glob.glob(pattern):
                # Only add if we haven't seen this path before
                if file_path not in seen_paths:
                    files.append(file_path)
                    seen_paths.add(file_path)
                    
            # Also check for uppercase extensions
            pattern = os.path.join(directory, f"*{ext.upper()}")
            for file_path in glob.glob(pattern):
                if file_path not in seen_paths:
                    files.append(file_path)
                    seen_paths.add(file_path)
        
        if not files:
            console.print(f"[bold #f38ba8]❌ No matching files found in {directory}[/bold #f38ba8]")
            retry = Confirm.ask("[#cba6f7]Try another directory?[/#cba6f7]")
            if not retry:
                return []
            continue
        
        # Sort files by name
        files.sort()
        
        # Display found files
        console.print(f"\n[#a6e3a1]Found {len(files)} files:[/#a6e3a1]")
        for i, file in enumerate(files, 1):
            console.print(f"[#94e2d5]{i}.[/#94e2d5] {os.path.basename(file)}")
        
        # Confirm selection
        use_files = Confirm.ask("\n[#cba6f7]Process these files?[/#cba6f7]")
        if use_files:
            return files
        
        retry = Confirm.ask("[#cba6f7]Try another directory?[/#cba6f7]")
        if not retry:
            return []

async def batch_metadata():
    """Batch edit metadata for multiple files"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Batch Metadata Editor 🎵[/bold #f5e0dc]\n")
    
    # Get files
    files = await get_files_for_batch(file_type="audio")
    if not files:
        console.print("[#f38ba8]Batch operation cancelled.[/#f38ba8]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the batch menu...[/#89b4fa]")
        return
    
    # Ask which metadata fields to edit
    console.print("\n[#cba6f7]Select metadata fields to edit:[/#cba6f7]")
    
    edit_title = Confirm.ask("[#89b4fa]Edit Title?[/#89b4fa]", default=False)
    edit_artist = Confirm.ask("[#89b4fa]Edit Artist?[/#89b4fa]", default=False)
    edit_album = Confirm.ask("[#89b4fa]Edit Album?[/#89b4fa]", default=False)
    edit_genre = Confirm.ask("[#89b4fa]Edit Genre?[/#89b4fa]", default=False)
    
    if not any([edit_title, edit_artist, edit_album, edit_genre]):
        console.print("[#f38ba8]No fields selected for editing.[/#f38ba8]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the batch menu...[/#89b4fa]")
        return
    
    # Get new values
    metadata_updates = {}
    
    if edit_title:
        metadata_updates['title'] = Prompt.ask("[#cba6f7]New Title (or {n} for track number, {filename} for filename)[/#cba6f7]").strip()
    
    if edit_artist:
        metadata_updates['artist'] = Prompt.ask("[#cba6f7]New Artist[/#cba6f7]").strip()
    
    if edit_album:
        metadata_updates['album'] = Prompt.ask("[#cba6f7]New Album[/#cba6f7]").strip()
    
    if edit_genre:
        metadata_updates['genre'] = Prompt.ask("[#cba6f7]New Genre[/#cba6f7]").strip()
    
    # Process files
    results = {"success": 0, "failed": 0, "errors": []}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[#89b4fa]Processing files...[/#89b4fa]", total=len(files))
        
        for file in files:
            filename = os.path.basename(file)
            progress.update(task, description=f"[#89b4fa]Processing {filename}...[/#89b4fa]")
            
            # Prepare metadata for this specific file
            file_metadata = metadata_updates.copy()
            
            # Handle special placeholders
            if edit_title and '{filename}' in file_metadata['title']:
                base_filename = os.path.splitext(filename)[0]
                file_metadata['title'] = file_metadata['title'].replace('{filename}', base_filename)
            
            if edit_title and '{n}' in file_metadata['title']:
                # Try to extract track number from filename (assumes format like "01 - Song Name.mp3")
                try:
                    track_num = filename.split(' ')[0]
                    if track_num.isdigit():
                        file_metadata['title'] = file_metadata['title'].replace('{n}', track_num)
                except:
                    # If extraction fails, just use the original placeholder
                    pass
            
            try:
                # Call the metadata editing function
                success = await edit_metadata_file(file, file_metadata, silent=True)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to update {filename}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error updating {filename}: {str(e)}")
            
            progress.advance(task)
    
    # Show results
    if results["success"] > 0:
        console.print(f"\n[bold #a6e3a1]✅ Successfully updated metadata for {results['success']} files![/bold #a6e3a1]")
    
    if results["failed"] > 0:
        console.print(f"[bold #f38ba8]❌ Failed to update {results['failed']} files.[/bold #f38ba8]")
        if results["errors"]:
            console.print("\n[#f38ba8]Errors:[/#f38ba8]")
            for error in results["errors"]:
                console.print(f"[#f38ba8]- {error}[/#f38ba8]")
    
    Prompt.ask("\n[#89b4fa]Press Enter to return to the batch menu...[/#89b4fa]")

async def batch_convert():
    """Batch convert multiple audio files"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Batch Audio Converter 🎵[/bold #f5e0dc]\n")
    
    # Get files
    files = await get_files_for_batch(file_type="audio")
    if not files:
        console.print("[#f38ba8]Batch operation cancelled.[/#f38ba8]")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the batch menu...[/#89b4fa]")
        return
    
    # Ask for output format
    valid_formats = ["mp3", "wav", "flac", "aac", "ogg"]
    output_format = Prompt.ask(
        "[#cba6f7]Enter the output format[/#cba6f7]",
        choices=valid_formats,
        default="mp3"
    ).strip().lower()
    
    # Ask for output directory
    while True:
        output_dir = Prompt.ask("[#cba6f7]Enter output directory (or press Enter to use the same directory)[/#cba6f7]").strip()
        
        if not output_dir:
            # Use same directory as input files
            output_dir = os.path.dirname(files[0])
            break
        
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
                console.print(f"[#a6e3a1]Created directory: {output_dir}[/#a6e3a1]")
                break
            except Exception as e:
                console.print(f"[bold #f38ba8]❌ Error creating directory: {e}[/bold #f38ba8]")
                continue
        else:
            break
    
    # Process files
    results = {"success": 0, "failed": 0, "errors": []}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[#89b4fa]Converting files...[/#89b4fa]", total=len(files))
        
        for file in files:
            filename = os.path.basename(file)
            progress.update(task, description=f"[#89b4fa]Converting {filename}...[/#89b4fa]")
            
            # Determine output file path
            base_name = os.path.splitext(os.path.basename(file))[0]
            output_file = os.path.join(output_dir, f"{base_name}.{output_format}")
            
            try:
                # Call the conversion function
                success = await convert_audio_file(file, output_file, silent=True)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to convert {filename}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error converting {filename}: {str(e)}")
            
            progress.advance(task)
    
    # Show results
    if results["success"] > 0:
        console.print(f"\n[bold #a6e3a1]✅ Successfully converted {results['success']} files![/bold #a6e3a1]")
        console.print(f"[#94e2d5]Files saved to: {output_dir}[/#94e2d5]")
    
    if results["failed"] > 0:
        console.print(f"[bold #f38ba8]❌ Failed to convert {results['failed']} files.[/bold #f38ba8]")
        if results["errors"]:
            console.print("\n[#f38ba8]Errors:[/#f38ba8]")
            for error in results["errors"]:
                console.print(f"[#f38ba8]- {error}[/#f38ba8]")
    
    Prompt.ask("\n[#89b4fa]Press Enter to return to the batch menu...[/#89b4fa]")
