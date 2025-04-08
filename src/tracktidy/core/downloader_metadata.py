"""
Metadata embedding functionality for downloaded music files
"""
import os
import logging
import requests
from typing import Optional
import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK, TCON, USLT

from ..providers.base import Track

logger = logging.getLogger("tracktidy")

def embed_metadata(file_path: str, track: Track) -> bool:
    """
    Embed metadata into a downloaded audio file
    
    Args:
        file_path: Path to the audio file
        track: Track object containing metadata
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"Cannot embed metadata: File does not exist: {file_path}")
        return False
        
    try:
        # Check file type and use appropriate metadata handling
        if file_path.lower().endswith('.mp3'):
            return embed_mp3_metadata(file_path, track)
        else:
            logger.warning(f"Metadata embedding not supported for {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error embedding metadata: {e}")
        return False

def embed_mp3_metadata(file_path: str, track: Track) -> bool:
    """
    Embed metadata into an MP3 file
    
    Args:
        file_path: Path to the MP3 file
        track: Track object containing metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Try to load existing ID3 tags or create new ones
        try:
            audio = ID3(file_path)
        except mutagen.id3.ID3NoHeaderError:
            # If no ID3 header exists, create one
            audio = ID3()
            
        # Add title
        if track.title:
            audio['TIT2'] = TIT2(encoding=3, text=track.title)
            
        # Add artist
        if track.artist:
            audio['TPE1'] = TPE1(encoding=3, text=track.artist)
            
        # Add album
        if track.album:
            audio['TALB'] = TALB(encoding=3, text=track.album)
            
        # Add release date
        if track.release_date:
            audio['TDRC'] = TDRC(encoding=3, text=track.release_date)
            
        # Add track number (if available)
        if hasattr(track, 'track_number') and track.track_number:
            audio['TRCK'] = TRCK(encoding=3, text=str(track.track_number))
            
        # Add genre (if available)
        if hasattr(track, 'genre') and track.genre:
            audio['TCON'] = TCON(encoding=3, text=track.genre)
            
        # Add lyrics (if available)
        if hasattr(track, 'lyrics') and track.lyrics:
            audio['USLT'] = USLT(encoding=3, lang='eng', desc='', text=track.lyrics)
            
        # Add YouTube source URL as comment (if available)
        if hasattr(track, 'youtube_url') and track.youtube_url:
            from mutagen.id3 import COMM
            audio['COMM'] = COMM(
                encoding=3,
                lang='eng',
                desc='YouTube Source',
                text=track.youtube_url
            )
        
        # Add album art if available
        if track.cover_url:
            cover_art_data = download_cover_art(track.cover_url)
            if cover_art_data:
                audio['APIC'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=cover_art_data
                )
        
        # Save the changes
        audio.save(file_path)
        logger.info(f"Successfully embedded metadata for {track.title}")
        return True
        
    except Exception as e:
        logger.error(f"Error embedding MP3 metadata: {e}")
        return False

def download_cover_art(cover_url: str) -> Optional[bytes]:
    """
    Download album artwork from URL
    
    Args:
        cover_url: URL to the cover art image
        
    Returns:
        Image data as bytes or None if download failed
    """
    try:
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading cover art: {e}")
        return None
