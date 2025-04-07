"""
Provider that gets metadata from Spotify and downloads audio from YouTube
"""
import re
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import time

from ..services.spotify import get_spotify_credentials, initialize_spotify_client
from ..services.youtube import YouTubeClient
from ..core.downloader_metadata import embed_metadata
from .base import BaseProvider, Track, Album, Playlist

logger = logging.getLogger("tracktidy")


class SpotifyYouTubeProvider(BaseProvider):
    """Provider that gets metadata from Spotify and downloads audio from YouTube"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the SpotifyYouTube provider"""
        self.config = config or {}
        self.spotify = None
        self.youtube = None
        
    async def initialize(self):
        """Initialize Spotify and YouTube clients"""
        # Get Spotify credentials from existing TrackTidy code
        client_id, client_secret = get_spotify_credentials()
        
        if not client_id or not client_secret:
            raise ValueError("Spotify credentials are required for music downloading")
        
        # Initialize Spotify client
        self.spotify = initialize_spotify_client(client_id, client_secret)
        if not self.spotify:
            raise ValueError("Failed to initialize Spotify client")
            
        # Initialize YouTube client
        self.youtube = YouTubeClient()
        await self.youtube.initialize()
    
    def extract_spotify_id(self, url: str, type_hint: str = None) -> Tuple[str, str]:
        """
        Extract the Spotify ID and type from a Spotify URL
        
        Args:
            url: Spotify URL
            type_hint: Type hint (track, album, playlist)
            
        Returns:
            Tuple of (item_type, item_id)
        """
        parsed = urlparse(url)
        if not parsed.netloc in ['open.spotify.com', 'spotify.com']:
            raise ValueError(f"Not a Spotify URL: {url}")
            
        path_parts = parsed.path.split('/')
        if len(path_parts) < 3:
            raise ValueError(f"Invalid Spotify URL format: {url}")
            
        # Handle URLs with or without the 'open.' prefix and with localized domains
        if path_parts[1] in ['track', 'album', 'playlist', 'artist']:
            item_type = path_parts[1]
            item_id = path_parts[2].split('?')[0]  # Remove query parameters
            return item_type, item_id
        
        raise ValueError(f"Unsupported Spotify URL: {url}")
    
    async def get_track(self, track_id: str) -> Track:
        """Get track metadata from Spotify by ID"""
        try:
            # Get track details from Spotify
            track_info = self.spotify.track(track_id)
            
            # Extract relevant information
            artists = ", ".join([artist['name'] for artist in track_info['artists']])
            album_name = track_info['album']['name']
            cover_url = track_info['album']['images'][0]['url'] if track_info['album']['images'] else None
            
            # Create a Track object
            track = Track(
                id=track_id,
                title=track_info['name'],
                artist=artists,
                album=album_name,
                cover_url=cover_url,
                duration=track_info['duration_ms'] // 1000,  # Convert ms to seconds
                release_date=track_info['album']['release_date'],
                isrc=track_info.get('external_ids', {}).get('isrc'),
                explicit=track_info.get('explicit', False)
            )
            
            return track
            
        except Exception as e:
            logger.error(f"Error getting track from Spotify: {e}")
            raise
        
    async def get_album(self, album_id: str) -> Album:
        """Get album metadata and tracks from Spotify by ID"""
        try:
            # Get album details from Spotify
            album_info = self.spotify.album(album_id)
            
            # Extract album metadata
            artists = ", ".join([artist['name'] for artist in album_info['artists']])
            cover_url = album_info['images'][0]['url'] if album_info['images'] else None
            
            # Get all tracks for the album
            tracks = []
            items = album_info['tracks']['items']
            
            # Handle pagination for albums with more than 50 tracks
            while album_info['tracks']['next']:
                album_info['tracks'] = self.spotify.next(album_info['tracks'])
                items.extend(album_info['tracks']['items'])
            
            # Create Track objects for each track in the album
            for item in items:
                track_artists = ", ".join([artist['name'] for artist in item['artists']])
                
                track = Track(
                    id=item['id'],
                    title=item['name'],
                    artist=track_artists,
                    album=album_info['name'],
                    duration=item['duration_ms'] // 1000,
                    cover_url=cover_url,
                    release_date=album_info['release_date'],
                    explicit=item.get('explicit', False)
                )
                tracks.append(track)
            
            # Create the Album object
            album = Album(
                id=album_id,
                title=album_info['name'],
                artist=artists,
                cover_url=cover_url,
                tracks=tracks,
                release_date=album_info['release_date'],
                upc=album_info.get('external_ids', {}).get('upc')
            )
            
            return album
            
        except Exception as e:
            logger.error(f"Error getting album from Spotify: {e}")
            raise
        
    async def get_playlist(self, playlist_id: str) -> Playlist:
        """Get playlist metadata and tracks from Spotify by ID"""
        try:
            # Get playlist details from Spotify
            playlist_info = self.spotify.playlist(playlist_id)
            
            # Extract playlist metadata
            cover_url = playlist_info['images'][0]['url'] if playlist_info['images'] else None
            
            # Get all tracks from the playlist
            tracks = []
            items = playlist_info['tracks']['items']
            
            # Handle pagination for playlists with more than 100 tracks
            while playlist_info['tracks']['next']:
                playlist_info['tracks'] = self.spotify.next(playlist_info['tracks'])
                items.extend(playlist_info['tracks']['items'])
            
            # Create Track objects for each track in the playlist
            for item in items:
                if not item['track']:  # Skip unavailable tracks
                    continue
                    
                track_info = item['track']
                artists = ", ".join([artist['name'] for artist in track_info['artists']])
                
                track = Track(
                    id=track_info['id'],
                    title=track_info['name'],
                    artist=artists,
                    album=track_info['album']['name'],
                    duration=track_info['duration_ms'] // 1000,
                    cover_url=track_info['album']['images'][0]['url'] if track_info['album']['images'] else None,
                    release_date=track_info['album']['release_date'],
                    isrc=track_info.get('external_ids', {}).get('isrc'),
                    explicit=track_info.get('explicit', False)
                )
                tracks.append(track)
            
            # Create the Playlist object
            playlist = Playlist(
                id=playlist_id,
                title=playlist_info['name'],
                creator=playlist_info['owner']['display_name'],
                tracks=tracks,
                cover_url=cover_url
            )
            
            return playlist
            
        except Exception as e:
            logger.error(f"Error getting playlist from Spotify: {e}")
            raise
        
    async def search(self, query: str, type: str = "track", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for music content on Spotify"""
        try:
            if type not in ["track", "album", "playlist", "artist"]:
                raise ValueError(f"Invalid search type: {type}")
                
            # Perform search via Spotify API
            results = self.spotify.search(q=query, type=type, limit=limit)
            
            # Extract relevant information based on the search type
            items = []
            if type == "track":
                for item in results['tracks']['items']:
                    items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'artist': ", ".join([artist['name'] for artist in item['artists']]),
                        'album': item['album']['name'],
                        'duration': item['duration_ms'] // 1000,
                        'cover_url': item['album']['images'][0]['url'] if item['album']['images'] else None,
                        'type': 'track'
                    })
            elif type == "album":
                for item in results['albums']['items']:
                    items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'artist': ", ".join([artist['name'] for artist in item['artists']]),
                        'cover_url': item['images'][0]['url'] if item['images'] else None,
                        'type': 'album'
                    })
            elif type == "playlist":
                for item in results['playlists']['items']:
                    items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'owner': item['owner']['display_name'],
                        'tracks_count': item['tracks']['total'],
                        'cover_url': item['images'][0]['url'] if item['images'] else None,
                        'type': 'playlist'
                    })
            elif type == "artist":
                for item in results['artists']['items']:
                    items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'popularity': item['popularity'],
                        'cover_url': item['images'][0]['url'] if item['images'] else None,
                        'type': 'artist'
                    })
            
            return items
            
        except Exception as e:
            logger.error(f"Error searching Spotify: {e}")
            raise
        
    async def download_track(self, track: Track, output_path: str, quality: int = None) -> str:
        """Download a track from YouTube using metadata from Spotify"""
        try:
            # Form a search query for YouTube
            search_query = f"{track.title} {track.artist}"
            
            # Remove any featuring artists for a cleaner search
            search_query = re.sub(r'\(feat\..*?\)', '', search_query)
            search_query = re.sub(r'\bft\..*?$', '', search_query)
            
            # Show some debug info
            logger.info(f"Searching for: {search_query}")
            logger.info(f"Track duration: {track.duration} seconds")
            
            # Search for the track on YouTube
            youtube_url = await self.youtube.search_best_match(
                search_query,
                duration=track.duration
            )
            
            if not youtube_url:
                logger.error(f"No YouTube match found for: {track.title} by {track.artist}")
                raise Exception(f"Could not find YouTube match for: {track.title} by {track.artist}")
            
            logger.info(f"Found YouTube match: {youtube_url}")
            
            # Generate a clean filename for the track
            filename = f"{track.artist} - {track.title}"
            # Remove characters that are invalid in filenames
            filename = re.sub(r'[\\/*?:"<>|]', '', filename)
            
            # Download the track from YouTube
            quality_str = "320" if quality is None or quality >= 1 else "128"
            
            # Add a small delay to make sure YouTube doesn't throttle us
            time.sleep(1)
            
            # Perform the download
            download_path = await self.youtube.download(youtube_url, output_path, filename, quality_str)
            
            if not download_path or not os.path.exists(download_path):
                logger.error(f"Download failed for {track.title} by {track.artist}")
                raise Exception(f"Download failed for {track.title} by {track.artist}")
                
            # Embed metadata from Spotify into the downloaded file
            logger.info(f"Embedding metadata for {track.title}")
            embed_metadata(download_path, track)
                
            logger.info(f"Successfully downloaded: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Error downloading track: {e}")
            raise
