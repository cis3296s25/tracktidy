"""
Metadata editing functionality for TrackTidy
"""
import os

from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from rich.console import Console
from rich.prompt import Prompt

console = Console()

async def edit_metadata_file(file_path, metadata_updates=None, silent=False):
    """Edit metadata for a single file with optional silent mode for batch processing"""
    try:
        # Load the audio file based on its format
        audio = None
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.mp3':
            try:
                audio = MP3(file_path, ID3=EasyID3)
            except Exception as e:
                if not silent:
                    console.print(f"[bold #f38ba8]❌ Error loading MP3 file:[/bold #f38ba8] {e}")
                    console.print("[#89dceb]The file might be corrupted or have no ID3 tag. Adding ID3 tag...[/#89dceb]")
                try:
                    # Try to add ID3 tag if it doesn't exist
                    from mutagen.id3 import ID3, ID3NoHeaderError
                    try:
                        audio = MP3(file_path)
                        audio.add_tags()
                        audio.save()
                        audio = MP3(file_path, ID3=EasyID3)
                    except ID3NoHeaderError:
                        audio = MP3(file_path)
                        audio.add_tags()
                        audio.save()
                        audio = MP3(file_path, ID3=EasyID3)
                except Exception as e2:
                    if not silent:
                        console.print(f"[bold #f38ba8]❌ Failed to add ID3 tag:[/bold #f38ba8] {e2}")
                    return False
        elif file_ext == '.flac':
            try:
                audio = FLAC(file_path)
            except Exception as e:
                if not silent:
                    console.print(f"[bold #f38ba8]❌ Error loading FLAC file:[/bold #f38ba8] {e}")
                return False
        else:
            # For other file types, use File from mutagen
            try:
                audio = File(file_path)
                if audio is None:
                    raise Exception("Unsupported audio format")
            except Exception as e:
                if not silent:
                    console.print(f"[bold #f38ba8]❌ Error loading audio file:[/bold #f38ba8] {e}")
                return False
        
        # Apply metadata updates if provided
        if metadata_updates:
            for field, value in metadata_updates.items():
                if value:  # Only update non-empty values
                    try:
                        if isinstance(audio, FLAC):
                            audio[field] = value
                        elif hasattr(audio, '__setitem__'):
                            audio[field] = value
                        else:
                            audio.tags[field] = value
                    except Exception as e:
                        if not silent:
                            console.print(f"[bold #f38ba8]❌ Error setting {field}:[/bold #f38ba8] {e}")
            
            try:
                audio.save()
                return True
            except Exception as e:
                if not silent:
                    console.print(f"[bold #f38ba8]❌ Error saving metadata:[/bold #f38ba8] {e}")
                return False
        
        return True
        
    except Exception as e:
        if not silent:
            console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")
        return False

def scan_directory_for_audio(directory_path):
    """Scan a directory for supported audio files"""
    supported_extensions = ['.mp3', '.flac', '.m4a', '.ogg']
    audio_files = []
    
    try:
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in supported_extensions:
                    audio_files.append(file_path)
    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error scanning directory:[/bold #f38ba8] {e}")
    
    return audio_files

async def edit_metadata():
    """Interactive metadata editing UI"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Metadata Editor 🎵[/bold #f5e0dc]")
    
    # Display options menu
    console.print("\n[#89b4fa]1.[/#89b4fa][bold] Edit file metadata[/bold]")
    console.print("[#f38ba8]2.[/#f38ba8][bold] Return to Main Menu[/bold]")
    
    choice = Prompt.ask("\n[#cba6f7]Select an option[/#cba6f7]", choices=["1", "2"])
    
    if choice == "2":
        return
    
    # Ask for the file path
    while True:
        console.print("[#f38ba8]Type 'menu' at any prompt to return to the main menu[/#f38ba8]")
        console.print("[#94e2d5]Supported file formats: MP3, FLAC, M4A, OGG[/#94e2d5]")
        console.print("[#94e2d5]You can enter a file path or a folder path containing audio files[/#94e2d5]")
        path = Prompt.ask("[#89dceb]Enter the path to the audio file or folder[/#89dceb]").strip()
        
        if path.lower() == 'menu':
            return
            
        # Check if path is a directory
        if os.path.isdir(path):
            # Scan directory for audio files
            audio_files = scan_directory_for_audio(path)
            
            if not audio_files:
                console.print("[bold #f38ba8]❌ No supported audio files found in the directory![/bold #f38ba8]")
                continue
                
            # Display list of found audio files
            console.print("\n[#f9e2af]Found the following audio files:[/#f9e2af]")
            for i, file_path in enumerate(audio_files):
                console.print(f"[#89b4fa]{i+1}.[/#89b4fa] {os.path.basename(file_path)}")
                
            # Let user select a file
            file_choice = Prompt.ask(
                "\n[#cba6f7]Select a file by number (or type 'menu' to return)[/#cba6f7]",
                choices=[str(i+1) for i in range(len(audio_files))] + ["menu"]
            )
            
            if file_choice.lower() == 'menu':
                return
                
            file_path = audio_files[int(file_choice) - 1]
            console.print(f"[#94e2d5]Selected:[/#94e2d5] {file_path}")
            break
            
        elif os.path.isfile(path):
            file_path = path
            # Check if file has a supported extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.mp3', '.flac', '.m4a', '.ogg']:
                console.print("[bold #f38ba8]❌ Error: Unsupported file format! Supported formats: MP3, FLAC, M4A, OGG[/bold #f38ba8]")
                continue
            break
        else:
            console.print("[bold #f38ba8]❌ Error: Path not found! Please enter a valid file or folder path.[/bold #f38ba8]")
            continue

    # Load the audio file and define metadata fields
    metadata_fields = ["title", "artist", "album", "genre"]
    
    try:
        # Load the audio file based on its format
        audio = None
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.mp3':
            try:
                audio = MP3(file_path, ID3=EasyID3)
            except Exception as e:
                console.print(f"[bold #f38ba8]❌ Error loading MP3 file:[/bold #f38ba8] {e}")
                console.print("[#89dceb]The file might be corrupted or have no ID3 tag. Adding ID3 tag...[/#89dceb]")
                try:
                    # Try to add ID3 tag if it doesn't exist
                    from mutagen.id3 import ID3, ID3NoHeaderError
                    try:
                        audio = MP3(file_path)
                        audio.add_tags()
                        audio.save()
                        audio = MP3(file_path, ID3=EasyID3)
                    except ID3NoHeaderError:
                        audio = MP3(file_path)
                        audio.add_tags()
                        audio.save()
                        audio = MP3(file_path, ID3=EasyID3)
                except Exception as e2:
                    console.print(f"[bold #f38ba8]❌ Failed to add ID3 tag:[/bold #f38ba8] {e2}")
                    Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                    return
        elif file_ext == '.flac':
            try:
                audio = FLAC(file_path)
            except Exception as e:
                console.print(f"[bold #f38ba8]❌ Error loading FLAC file:[/bold #f38ba8] {e}")
                Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                return
        else:
            # For other file types, use File from mutagen
            try:
                audio = File(file_path)
                if audio is None:
                    raise Exception("Unsupported audio format")
            except Exception as e:
                console.print(f"[bold #f38ba8]❌ Error loading audio file:[/bold #f38ba8] {e}")
                Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
                return
                
        console.print("\n[#f9e2af]--- Current Metadata ---[/#f9e2af]")
        current_metadata = {}  # Store current values
        
        for field in metadata_fields:
            try:
                # Handle different audio libraries differently
                if isinstance(audio, FLAC):
                    value = audio.get(field, ["[Not Set]"])
                elif hasattr(audio, 'get'):
                    value = audio.get(field, ["[Not Set]"])
                else:
                    value = audio.tags.get(field, ["[Not Set]"])
                
                current_metadata[field] = value[0] if value and value[0] != "[Not Set]" else ""
                console.print(f"[#94e2d5]{field.capitalize()}[/#94e2d5]: {value[0] if value else '[Not Set]'}")
            except Exception as e:
                console.print(f"[#f38ba8]Couldn't read {field}: {e}[/#f38ba8]")
                current_metadata[field] = ""

        console.print("\n[#cba6f7]Enter new metadata values (press Enter to keep current value):[/#cba6f7]")

        # Prompt user for new metadata input
        console.print("[#f38ba8]Type 'menu' at any prompt to return to the main menu[/#f38ba8]")
        metadata_updates = {}
        for field in metadata_fields:
            new_value = Prompt.ask(f"[#89b4fa]{field.capitalize()}[/#89b4fa]", default=current_metadata[field]).strip()
            if new_value.lower() == 'menu':
                return
            if new_value and new_value != current_metadata[field]:
                metadata_updates[field] = new_value
        
        if metadata_updates:
            # Call the helper function to apply updates
            if await edit_metadata_file(file_path, metadata_updates):
                console.print("\n[bold #a6e3a1]✅ Metadata updated successfully![/bold #a6e3a1]")
                
                # Reload the file to show updated metadata
                if file_ext == '.mp3':
                    audio = MP3(file_path, ID3=EasyID3)
                elif file_ext == '.flac':
                    audio = FLAC(file_path)
                else:
                    audio = File(file_path)
                
                # Show the updated metadata
                console.print("\n[#f9e2af]--- Updated Metadata ---[/#f9e2af]")
                for field in metadata_fields:
                    try:
                        if isinstance(audio, FLAC):
                            value = audio.get(field, ["[Not Set]"])
                        elif hasattr(audio, 'get'):
                            value = audio.get(field, ["[Not Set]"])
                        else:
                            value = audio.tags.get(field, ["[Not Set]"])
                        
                        console.print(f"[#94e2d5]{field.capitalize()}[/#94e2d5]: {', '.join(value) if value else '[Not Set]'}")
                    except Exception as e:
                        console.print(f"[#f38ba8]Couldn't read updated {field}: {e}[/#f38ba8]")
            else:
                console.print("\n[bold #f38ba8]❌ Failed to update metadata![/bold #f38ba8]")
        else:
            console.print("\n[#89dceb]No changes made to metadata.[/#89dceb]")
            
        # Pause before returning to the menu
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
