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

async def edit_metadata():
    """Interactive metadata editing UI"""
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Metadata Editor 🎵[/bold #f5e0dc]")

    # Ask for the file path
    while True:
        file_path = Prompt.ask("[#89dceb]Enter the path to the audio file ['exit' for menu][/#89dceb]").strip()
        if file_path.strip().lower() == "exit":
            return
        if not os.path.isfile(file_path):
            console.print("[bold #f38ba8]❌ Error: File not found! Please enter a valid file path.[/bold #f38ba8]")
            continue
        
        # Check if file has a supported extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ['.mp3', '.flac', '.m4a', '.ogg']:
            console.print("[bold #f38ba8]❌ Error: Unsupported file format! Supported formats: MP3, FLAC, M4A, OGG[/bold #f38ba8]")
            continue
        
        break

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

        while True:
            console.print("\n[#cba6f7]Enter new metadata values (press Enter to keep current value):[/#cba6f7]")

            # Prompt user for new metadata input
            metadata_updates = {}
            for field in metadata_fields:
                new_value = Prompt.ask(f"[#89b4fa]{field.capitalize()}[/#89b4fa]", default=current_metadata[field]).strip()
                if new_value and new_value != current_metadata[field]:
                    metadata_updates[field] = new_value
            
            if metadata_updates:
                # Confirm changes
                while True:
                    console.print("\n[bold #f38ba8]Confirm metadata changes?\n[/bold #f38ba8]")
                    for field in metadata_fields:
                        try:
                            if isinstance(audio, FLAC):
                                value = audio.get(field, ["[Not Set]"])
                            elif hasattr(audio, 'get'):
                                value = audio.get(field, ["[Not Set]"])
                            else:
                                value = audio.tags.get(field, ["[Not Set]"])
                                
                            current_field = (
                                metadata_updates[field] if field in metadata_updates
                                else ', '.join(value) if value
                                else '[Not Set]'
                            )                           
                            console.print(f"[#f9e2af]{field.capitalize()}[/#f9e2af]: {current_field}")
                        except Exception as e:
                            console.print(f"[#f38ba8]Couldn't read updated {field}: {e}[/#f38ba8]")
                    
                    confirm_metadata_changes = Prompt.ask("\n[#a6e3a1](y/n)")
                    if confirm_metadata_changes != "y" and confirm_metadata_changes != "n":
                        console.print("\n[bold #f38ba8]❌ Error: Invalid confirmation! Enter: 'y' or 'n'[/bold #f38ba8]")
                        continue
                    else:
                        break
                if confirm_metadata_changes == "n":
                    continue

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
            
            break
            
        # Pause before returning to the menu
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")
