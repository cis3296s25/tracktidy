"""
Base provider interface for all music source providers
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class Track:
    """Represents a track to be downloaded"""
    id: str
    title: str
    artist: str
    album: str
    cover_url: Optional[str] = None
    duration: Optional[int] = None
    release_date: Optional[str] = None
    isrc: Optional[str] = None
    quality: Optional[str] = None
    explicit: Optional[bool] = None
    youtube_url: Optional[str] = None


@dataclass
class Album:
    """Represents an album to be downloaded"""
    id: str
    title: str
    artist: str
    cover_url: Optional[str] = None
    tracks: Optional[List[Track]] = None
    release_date: Optional[str] = None
    upc: Optional[str] = None


@dataclass
class Playlist:
    """Represents a playlist to be downloaded"""
    id: str
    title: str
    creator: str
    tracks: List[Track]
    cover_url: Optional[str] = None


class BaseProvider(ABC):
    """Base provider interface for all music source providers"""
    
    @abstractmethod
    async def get_track(self, track_id: str) -> Track:
        """Get track metadata by ID"""
        pass
    
    @abstractmethod
    async def get_album(self, album_id: str) -> Album:
        """Get album metadata and tracks by ID"""
        pass
    
    @abstractmethod
    async def get_playlist(self, playlist_id: str) -> Playlist:
        """Get playlist metadata and tracks by ID"""
        pass
    
    @abstractmethod
    async def search(self, query: str, type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for music content"""
        pass
    
    @abstractmethod
    async def download_track(self, track: Track, output_path: str, quality: int = None) -> str:
        """Download a track to the specified path and return downloaded file path"""
        pass
