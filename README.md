# TrackTidy

TrackTidy is an all-in-one music manager program made for DJs and music enthusiasts who want a lightweight yet powerful way to manage their audio files. The application features a styled command-line interface with robust functionality for managing your music collection.

![TrackTidy Screenshot](landing.png)

## Features

TrackTidy currently offers the following features:

- **Metadata Editor**: Edit track metadata including title, artist, album, and genre
- **Audio Conversion**: Convert audio files between different formats (mp3, wav, flac, aac, ogg)
- **Cover Art Fetching**: Search and download album artwork from Spotify and embed it in your MP3 files
- **Batch Processing**: Process multiple files at once for metadata editing and audio conversion

## Planned Features

The following features are planned for future releases:

- **Audio Editing**: Normalize audio, trim tracks, add fades
- **Playlist Generator**: Export selected tracks to `.m3u` or `.pls` format
- **Music Downloader**: Download music from various sources
- **GUI Version**: A graphical user interface alternative

## Requirements

- Python 3.7 or higher
- FFmpeg (for audio conversion)
- Spotify API credentials (for cover art fetching)

## Dependencies

TrackTidy depends on the following Python libraries:

- rich - For the styled command line interface
- mutagen - For audio metadata manipulation
- spotipy - For Spotify API access
- requests - For HTTP requests

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/tracktidy.git
   cd tracktidy
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install FFmpeg:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` or equivalent for your distribution

## Usage

Run the program with:
```
python tracktidy.py
```

### Metadata Editor

1. Select option 1 from the main menu
2. Enter the path to the audio file
3. View current metadata
4. Enter new values or press Enter to keep current values

### Audio Converter

1. Select option 2 from the main menu
2. Enter the path to the audio file
3. Choose the output format
4. Wait for conversion to complete

### Cover Art Fetcher

1. Select option 3 from the main menu
2. Enter your Spotify API credentials if prompted (only required the first time)
3. Enter the song name and artist
4. Enter the path to the MP3 file
5. Cover art will be downloaded and embedded in the file

### Batch Processing

1. Select option 4 from the main menu
2. Choose between batch metadata editing or batch audio conversion
3. Enter the directory containing the files to process
4. Follow the prompts to apply changes to multiple files at once

## Getting Spotify API Credentials

To use the Cover Art Fetcher feature, you'll need Spotify API credentials:

1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Log in with your Spotify account
3. Create a new application
4. Copy the Client ID and Client Secret
5. Enter these credentials when prompted by TrackTidy

## Development

This project is structured as follows:

- `tracktidy.py` - Main application with menu system
- `metadata_editor.py` - Module for editing audio metadata
- `audio_converter.py` - Module for converting audio formats
- `fetch_cover_art.py` - Module for fetching and embedding cover art
- `batch_processor.py` - Module for batch processing multiple files

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
