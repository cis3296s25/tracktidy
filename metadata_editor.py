import os

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from rich.console import Console
from rich.prompt import Prompt

console = Console()

async def edit_metadata():
    console.print("\n[bold #f5e0dc]🎵 TrackTidy - Metadata Editor 🎵[/bold #f5e0dc]")

    # Ask for the file path
    while True:
        file_path = Prompt.ask("[#89dceb]Enter the path to the MP3 file[/#89dceb]").strip()
        if not os.path.isfile(file_path):
            console.print("[bold #f38ba8]❌ Error: File not found! Please enter a valid file path.[/bold #f38ba8]")
            continue
        break

    try:
        # Load the MP3 file and define metadata fields
        audio = MP3(file_path, ID3=EasyID3)
        metadata_fields = ["title", "artist", "album", "genre"]

        console.print("\n[#f9e2af]--- Current Metadata ---[/#f9e2af]")
        current_metadata = {}  # Store current values
        for field in metadata_fields:
            value = audio.get(field, ["[Not Set]"])
            current_metadata[field] = value[0]
            console.print(f"[#94e2d5]{field.capitalize()}[/#94e2d5]: {value[0]}")

        console.print("\n[#cba6f7]Enter new metadata values (press Enter to keep current value):[/#cba6f7]")

        # Prompt user for new metadata input
        for field in metadata_fields:
            new_value = Prompt.ask(f"[#89b4fa]{field.capitalize()}[/#89b4fa]", default=current_metadata[field]).strip()
            if new_value and new_value != current_metadata[field]:
                audio[field] = new_value

        audio.save()
        console.print("\n[bold #a6e3a1]✅ Metadata updated successfully![/bold #a6e3a1]")

        # Show the updated metadata
        console.print("\n[#f9e2af]--- Updated Metadata ---[/#f9e2af]")
        for field in metadata_fields:
            value = audio.get(field, ["[Not Set]"])
            console.print(f"[#94e2d5]{field.capitalize()}[/#94e2d5]: {', '.join(value)}")

        # Pause before returning to the menu
        Prompt.ask("\n[#89b4fa]Press Enter to return to the main menu...[/#89b4fa]")

    except Exception as e:
        console.print(f"[bold #f38ba8]❌ Error:[/bold #f38ba8] {e}")