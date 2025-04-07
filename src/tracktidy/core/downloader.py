"""
Music download functionality for TrackTidy
"""
import os
import asyncio
import logging
import re
from typing import List, Optional, Dict, Any, Tuple, Union
from pathlib import Path
from urllib.parse import urlparse

from ..providers.base import BaseProvider, Track, Album, Playlist
from ..providers.spotify_youtube import SpotifyYouTubeProvider
from ..providers.tidal_provider import TidalProvider

logger = logging.getLogger("tracktidy")


class MusicDownloader:
    """Core music downloading functionality for TrackTidy"""
    
    def __init__(self):
        """Initialize the music downloader with available providers"""
        self.providers = {}
        self.current_provider = None
    
    async def initialize_provider(self, provider_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Initialize and set the active provider
        
        Args:
            provider_name: Name of the provider to initialize
            config: Configuration dictionary for the provider
            
        Returns:
            True if provider was successfully initialized, False otherwise
        """
        try:
            if provider_name == "spotify-youtube":
                self.providers[provider_name] = SpotifyYouTubeProvider(config)
                await self.providers[provider_name].initialize()
            elif provider_name == "tidal":
                self.providers[provider_name] = TidalProvider(config)
                await self.providers[provider_name].initialize()
            else:
                return False
                
            self.current_provider = self.providers[provider_name]
            return True
        except Exception as e:
            logger.error(f"Error initializing provider {provider_name}: {e}")
            return False
    
    async def download_from_url(self, url: str, output_dir: str, quality: int = None) -> List[str]:
        """
        Parse URL and download content
        
        Args:
            url: URL to parse and download (Spotify or Tidal)
            output_dir: Directory to save downloaded files
            quality: Quality level for download (0-4)
            
        Returns:
            List of paths to downloaded files
        """
        if not self.current_provider:
            raise ValueError("No provider initialized")
            
        # Identify the URL type
        if "spotify.com" in url or "open.spotify.com" in url:
            # Parse Spotify URL
            provider = self.providers.get("spotify-youtube")
            if not provider:
                raise ValueError("Spotify provider not initialized")
                
            # Extract the Spotify ID and type from the URL
            item_type, item_id = provider.extract_spotify_id(url)
            
            # Download based on the item type
            if item_type == "track":
                track = await provider.get_track(item_id)
                filepath = await provider.download_track(track, output_dir, quality)
                return [filepath] if filepath else []
                
            elif item_type == "album":
                album = await provider.get_album(item_id)
                
                # Create album directory
                safe_artist = re.sub(r'[\\/*?:"<>|]', '', album.artist)
                safe_title = re.sub(r'[\\/*?:"<>|]', '', album.title)
                album_dir = os.path.join(output_dir, f"{safe_artist} - {safe_title}")
                os.makedirs(album_dir, exist_ok=True)
                
                # Download each track in the album
                filepaths = []
                for track in album.tracks:
                    filepath = await provider.download_track(track, album_dir, quality)
                    if filepath:
                        filepaths.append(filepath)
                
                return filepaths
                
            elif item_type == "playlist":
                playlist = await provider.get_playlist(item_id)
                
                # Create playlist directory
                safe_title = re.sub(r'[\\/*?:"<>|]', '', playlist.title)
                playlist_dir = os.path.join(output_dir, f"Playlist - {safe_title}")
                os.makedirs(playlist_dir, exist_ok=True)
                
                # Download each track in the playlist
                filepaths = []
                for track in playlist.tracks:
                    filepath = await provider.download_track(track, playlist_dir, quality)
                    if filepath:
                        filepaths.append(filepath)
                
                return filepaths
                
            else:
                raise ValueError(f"Unsupported Spotify item type: {item_type}")
                
        elif "tidal.com" in url:
            # For future implementation of Tidal downloads
            raise NotImplementedError("Tidal downloads not yet implemented")
            
        else:
            raise ValueError(f"Unsupported URL: {url}")
        
    async def download_track(self, track_id: str, output_dir: str, quality: int = None) -> str:
        """
        Download a single track
        
        Args:
            track_id: Spotify or Tidal track ID
            output_dir: Directory to save the file
            quality: Quality level for download (0-4)
            
        Returns:
            Path to downloaded file
        """
        if not self.current_provider:
            raise ValueError("No provider initialized")
            
        track = await self.current_provider.get_track(track_id)
        return await self.current_provider.download_track(track, output_dir, quality)
        
    async def download_album(self, album_id: str, output_dir: str, quality: int = None) -> List[str]:
        """
        Download an entire album
        
        Args:
            album_id: Spotify or Tidal album ID
            output_dir: Directory to save files
            quality: Quality level for download (0-4)
            
        Returns:
            List of paths to downloaded files
        """
        if not self.current_provider:
            raise ValueError("No provider initialized")
            
        album = await self.current_provider.get_album(album_id)
        
        # Create album directory
        safe_artist = re.sub(r'[\\/*?:"<>|]', '', album.artist)
        safe_title = re.sub(r'[\\/*?:"<>|]', '', album.title)
        album_dir = os.path.join(output_dir, f"{safe_artist} - {safe_title}")
        os.makedirs(album_dir, exist_ok=True)
        
        # Download each track in the album
        filepaths = []
        for track in album.tracks:
            filepath = await self.current_provider.download_track(track, album_dir, quality)
            if filepath:
                filepaths.append(filepath)
        
        return filepaths
        
    async def download_playlist(self, playlist_id: str, output_dir: str, quality: int = None) -> List[str]:
        """
        Download an entire playlist
        
        Args:
            playlist_id: Spotify or Tidal playlist ID
            output_dir: Directory to save files
            quality: Quality level for download (0-4)
            
        Returns:
            List of paths to downloaded files
        """
        if not self.current_provider:
            raise ValueError("No provider initialized")
            
        playlist = await self.current_provider.get_playlist(playlist_id)
        
        # Create playlist directory
        safe_title = re.sub(r'[\\/*?:"<>|]', '', playlist.title)
        playlist_dir = os.path.join(output_dir, f"Playlist - {safe_title}")
        os.makedirs(playlist_dir, exist_ok=True)
        
        # Download each track in the playlist
        filepaths = []
        for track in playlist.tracks:
            filepath = await self.current_provider.download_track(track, playlist_dir, quality)
            if filepath:
                filepaths.append(filepath)
        
        return filepaths
        
    async def search_music(self, query: str, media_type: str = "track", limit: int = 10) -> List[Dict]:
        """
        Search for music content
        
        Args:
            query: Search query
            media_type: Type of media to search for (track, album, playlist)
            limit: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if not self.current_provider:
            raise ValueError("No provider initialized")
            
        return await self.current_provider.search(query, media_type, limit)
