"""
Provider that gets metadata from Spotify and downloads audio from YouTube
"""
import re
import os
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
        self.debug_mode = self.config.get('debug_mode', False)
        
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
            # Validate inputs
            if not query.strip():
                logger.error("Empty search query provided")
                return []
                
            if type not in ["track", "album", "playlist", "artist"]:
                logger.error(f"Invalid search type: {type}")
                return []
            
            # Sanitize the query to avoid special character issues
            query = query.strip()
            
            # Try-except block specific to the search call
            try:
                # Perform search via Spotify API
                results = self.spotify.search(q=query, type=type, limit=limit)
                
                # Debug output for API response when debug_mode is enabled
                if self.debug_mode:
                    import json
                    logger.info(f"Spotify API response:\n{json.dumps(results, indent=2)}")
                    # If you need to see playlist data specifically
                    if type == 'playlist' and 'playlists' in results:
                        for i, item in enumerate(results['playlists']['items']):
                            logger.info(f"Playlist {i+1} structure: {item.keys()}")
                            if 'owner' in item:
                                logger.info(f"Owner structure: {item['owner'].keys() if item['owner'] else 'None'}")
            except Exception as search_error:
                logger.error(f"Error during Spotify search: {search_error}")
                # Return empty results rather than raising an exception
                return []
            
            # Extract relevant information based on the search type
            items = []
            
            # Process tracks
            if type == "track" and results and 'tracks' in results and 'items' in results['tracks']:
                for item in results['tracks']['items']:
                    try:
                        # Skip items missing essential data
                        if not all(k in item for k in ['id', 'name', 'artists', 'album']):
                            continue
                            
                        # Get artists safely
                        artists = [artist['name'] for artist in item['artists'] if 'name' in artist]
                        artist_str = ", ".join(artists) if artists else "Unknown Artist"
                        
                        # Get album name safely
                        album_name = item['album']['name'] if 'name' in item['album'] else "Unknown Album"
                        
                        # Get cover URL safely
                        cover_url = None
                        if ('images' in item['album'] and item['album']['images'] and 
                            isinstance(item['album']['images'], list) and len(item['album']['images']) > 0):
                            cover_url = item['album']['images'][0].get('url')
                        
                        items.append({
                            'id': item['id'],
                            'name': item['name'],
                            'artist': artist_str,
                            'album': album_name,
                            'duration': item['duration_ms'] // 1000 if 'duration_ms' in item else 0,
                            'cover_url': cover_url,
                            'type': 'track'
                        })
                    except (KeyError, TypeError) as e:
                        # Silently skip problematic items
                        continue
            
            # Process albums        
            elif type == "album" and results and 'albums' in results and 'items' in results['albums']:
                for item in results['albums']['items']:
                    try:
                        # Skip items missing essential data
                        if not all(k in item for k in ['id', 'name', 'artists']):
                            continue
                            
                        # Get artists safely
                        artists = [artist['name'] for artist in item['artists'] if 'name' in artist]
                        artist_str = ", ".join(artists) if artists else "Unknown Artist"
                        
                        # Get cover URL safely
                        cover_url = None
                        if ('images' in item and item['images'] and 
                            isinstance(item['images'], list) and len(item['images']) > 0):
                            cover_url = item['images'][0].get('url')
                            
                        items.append({
                            'id': item['id'],
                            'name': item['name'],
                            'artist': artist_str,
                            'cover_url': cover_url,
                            'type': 'album'
                        })
                    except (KeyError, TypeError) as e:
                        # Silently skip problematic items
                        continue
            
            # Process playlists        
            elif type == "playlist" and results and 'playlists' in results and 'items' in results['playlists']:
                for item in results['playlists']['items']:
                    try:
                        # Check that necessary fields exist before trying to access them
                        if not all(k in item for k in ['id', 'name', 'owner', 'tracks']):
                            # Silently skip without logging - prevents console output
                            continue
                            
                        # Safely access owner's display name
                        owner_name = "Unknown"
                        if (item['owner'] is not None and 
                            isinstance(item['owner'], dict) and 
                            'display_name' in item['owner'] and 
                            item['owner']['display_name'] is not None):
                            owner_name = item['owner']['display_name']
                            
                        # Safely access tracks count
                        tracks_count = 0
                        if (item['tracks'] is not None and 
                            isinstance(item['tracks'], dict) and 
                            'total' in item['tracks'] and 
                            item['tracks']['total'] is not None):
                            tracks_count = item['tracks']['total']
                            
                        # Safely access cover image
                        cover_url = None
                        if ('images' in item and 
                            item['images'] is not None and 
                            len(item['images']) > 0 and 
                            isinstance(item['images'][0], dict) and 
                            'url' in item['images'][0] and 
                            item['images'][0]['url'] is not None):
                            cover_url = item['images'][0]['url']
                            
                        items.append({
                            'id': item['id'],
                            'name': item['name'],
                            'owner': owner_name,
                            'tracks_count': tracks_count,
                            'cover_url': cover_url,
                            'type': 'playlist'
                        })
                    except (KeyError, TypeError, AttributeError) as e:
                        # Silently skip errors - prevents error messages in console
                        continue
            
            # Process artists        
            elif type == "artist" and results and 'artists' in results and 'items' in results['artists']:
                for item in results['artists']['items']:
                    try:
                        # Skip items missing essential data
                        if not all(k in item for k in ['id', 'name']):
                            continue
                            
                        # Get popularity safely
                        popularity = item.get('popularity', 0)
                        
                        # Get cover URL safely
                        cover_url = None
                        if ('images' in item and item['images'] and 
                            isinstance(item['images'], list) and len(item['images']) > 0):
                            cover_url = item['images'][0].get('url')
                            
                        items.append({
                            'id': item['id'],
                            'name': item['name'],
                            'popularity': popularity,
                            'cover_url': cover_url,
                            'type': 'artist'
                        })
                    except (KeyError, TypeError) as e:
                        # Silently skip problematic items
                        continue
            
            return items
            
        except Exception as e:
            logger.error(f"Error in Spotify search function: {e}")
            # Return empty list instead of raising, to prevent UI crashes
            return []
        
    async def download_track(self, track: Track, output_path: str, quality: int = None, progress_callback=None) -> str:
        """Download a track from YouTube using metadata from Spotify"""
        try:
            # Form a search query for YouTube
            search_query = f"{track.title} {track.artist}"
            
            # Remove any featuring artists and common noise for a cleaner search
            search_query = re.sub(r'\(feat\..*?\)', '', search_query)  # Remove (feat. Artist)
            search_query = re.sub(r'\(ft\..*?\)', '', search_query)    # Remove (ft. Artist)
            search_query = re.sub(r'\bft\..*?$', '', search_query)     # Remove trailing ft. Artist
            search_query = re.sub(r'\[.*?\]', '', search_query)        # Remove [content in brackets]
            search_query = re.sub(r'\s+', ' ', search_query)           # Clean up extra spaces
            search_query = search_query.strip()                        # Remove leading/trailing spaces
            
            # Show some debug info
            logger.info(f"Searching for: {search_query}")
            logger.info(f"Track duration: {track.duration} seconds")
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback('search', 0.1, f"Searching for: {track.title}")
            
            # Search for the track on YouTube with artist information
            youtube_url = await self.youtube.search_best_match(
                search_query,
                duration=track.duration,
                artists=track.artist.split(', ')
            )
            
            if not youtube_url:
                logger.error(f"No YouTube match found for: {track.title} by {track.artist}")
                if progress_callback:
                    progress_callback('error', 0, f"No match found for: {track.title}")
                raise Exception(f"Could not find YouTube match for: {track.title} by {track.artist}")
            
            # Update the track with the YouTube URL for reference
            track.youtube_url = youtube_url
            logger.info(f"Found YouTube match: {youtube_url}")
            if progress_callback:
                progress_callback('found', 0.2, f"Found match for: {track.title}")
            
            # Generate a clean filename for the track
            filename = f"{track.artist} - {track.title}"
            # Remove characters that are invalid in filenames
            filename = re.sub(r'[\\/*?:"<>|]', '', filename)
            
            # Download the track from YouTube
            quality_str = "320" if quality is None or quality >= 1 else "128"
            
            # Add a small delay to avoid YouTube throttling
            time.sleep(0.5)  # Reduced wait time for better user experience
            
            # Define a download progress handler to pass through to the YouTube downloader
            def download_progress_handler(stage, percent, status):
                if progress_callback:
                    # Map the download stages to overall progress (0.2-0.8 range for download)
                    if stage == 'start':
                        progress_callback('download', 0.2, status)
                    elif stage == 'download':
                        # Map the download percent to 0.2-0.7 range
                        mapped_percent = 0.2 + (percent * 0.5)  # 0.5 is 50% of our progress space
                        progress_callback('download', mapped_percent, status)
                    elif stage == 'processing':
                        progress_callback('processing', 0.7, status)
                    elif stage == 'complete':
                        progress_callback('processing', 0.8, "Processing audio...")
                    elif stage == 'error':
                        progress_callback('error', percent, status)
            
            # Perform the download with progress tracking
            download_path = await self.youtube.download(
                youtube_url, 
                output_path, 
                filename, 
                quality_str,
                progress_callback=download_progress_handler
            )
            
            if not download_path or not os.path.exists(download_path):
                logger.error(f"Download failed for {track.title} by {track.artist}")
                if progress_callback:
                    progress_callback('error', 0, f"Download failed for {track.title}")
                raise Exception(f"Download failed for {track.title} by {track.artist}")
                
            # Embed metadata from Spotify into the downloaded file
            logger.info(f"Embedding metadata for {track.title}")
            if progress_callback:
                progress_callback('metadata', 0.9, f"Adding metadata to {track.title}")
                
            embed_metadata(download_path, track)
            
            # Signal completion    
            if progress_callback:
                progress_callback('complete', 1.0, f"Completed: {track.title}")
                
            logger.info(f"Successfully downloaded: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Error downloading track: {e}")
            raise
