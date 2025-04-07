"""
YouTube service for TrackTidy
"""
import logging
import re
import os
from typing import Dict, Any, Optional, List
import yt_dlp

from ..services.ffmpeg import find_ffmpeg_executable, find_ffprobe_executable

logger = logging.getLogger("tracktidy")


class YouTubeClient:
    """Client for interacting with YouTube"""
    
    def __init__(self):
        """Initialize the YouTube client"""
        # Get FFmpeg and FFprobe paths from tracktidy's existing service
        self.ffmpeg_path = find_ffmpeg_executable()
        self.ffprobe_path = find_ffprobe_executable()
        
        if not self.ffmpeg_path or not self.ffprobe_path:
            logger.warning("FFmpeg or FFprobe path not found. Downloads may fail.")
            
        logger.debug(f"Using FFmpeg at: {self.ffmpeg_path}")
        logger.debug(f"Using FFprobe at: {self.ffprobe_path}")
        
        self.ytdlp_options = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        
        # Add FFmpeg path if available
        if self.ffmpeg_path and self.ffprobe_path:
            ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
            self.ytdlp_options['ffmpeg_location'] = ffmpeg_dir
    
    async def initialize(self):
        """Initialize the client (placeholder for consistency)"""
        # No initialization needed for YouTube
        pass
    
    async def search_best_match(self, query: str, duration: Optional[int] = None, limit: int = 5) -> Optional[str]:
        """
        Search YouTube for best matching video
        
        Args:
            query: Search query string
            duration: Track duration in seconds for better matching
            limit: Number of results to check
            
        Returns:
            YouTube URL of best match or None if no match found
        """
        # Prioritize searching on YouTube Music for better music matches
        search_term = f"ytsearch{limit}:{query}"  
        ytmusic_term = f"ytmsearch{limit}:{query}"  # YouTube Music search
        search_options = self.ytdlp_options.copy()
        search_options['format'] = 'bestaudio/best'
        search_options['quiet'] = True
        search_options['no_warnings'] = True
        search_options['extract_flat'] = 'in_playlist'
        search_options['skip_download'] = True
        search_options['noplaylist'] = False
        
        # Make sure we have ffmpeg location set
        if self.ffmpeg_path:
            search_options['ffmpeg_location'] = os.path.dirname(self.ffmpeg_path)
        
        try:
            # First try YouTube Music for better matches
            with yt_dlp.YoutubeDL(search_options) as ydl:
                logger.debug(f"Searching YouTube Music for: {query}")
                try:
                    # Try YouTube Music first
                    info = ydl.extract_info(ytmusic_term, download=False)
                    logger.debug("YouTube Music search successful")
                except Exception as e:
                    logger.debug(f"YouTube Music search failed: {e}, falling back to regular YouTube")
                    # Fall back to regular YouTube search
                    info = ydl.extract_info(search_term, download=False)
                
                if not info or 'entries' not in info:
                    logger.warning("No search results found")
                    return None
                
                entries = info['entries']
                if not entries or len(entries) == 0:
                    logger.warning("Empty search results")
                    return None
                
                # Filter out livestreams and find best match
                valid_entries = []
                for entry in entries:
                    if not entry or entry.get('is_live', False):
                        continue
                    valid_entries.append(entry)
                
                if not valid_entries:
                    logger.warning("No valid (non-livestream) results found")
                    return None
                
                # Score each entry based on how well it matches what we want
                scored_entries = []
                for entry in valid_entries:
                    if not entry.get('id'):
                        continue
                    
                    # Get full info for duration and other details
                    try:
                        url = f"https://www.youtube.com/watch?v={entry['id']}"
                        full_info = ydl.extract_info(url, download=False, process=True)
                        
                        # Basic score starts at 100
                        score = 100
                        
                        # Check duration if we have a target
                        if duration and 'duration' in full_info:
                            entry_duration = full_info['duration']
                            # Penalize by 1 point per second of difference
                            duration_diff = abs(entry_duration - duration)
                            if duration_diff > 30:  # More than 30 seconds difference
                                score -= min(40, duration_diff // 5)  # Max 40 point penalty
                        
                        # Prefer topic channels/official content (often better audio quality)
                        title = full_info.get('title', '').lower()
                        channel = full_info.get('channel', '').lower()
                        
                        if ' - topic' in channel:
                            score += 30
                        elif 'official' in title or 'official' in channel:
                            score += 20
                        elif 'vevo' in channel:
                            score += 15
                            
                        # Looking for keywords that suggest this is a full song
                        if 'full' in title and 'song' in title:
                            score += 5
                            
                        # Penalize common undesired terms
                        for term in ['cover', 'live', 'remix', 'instrumental', 'karaoke', 'reaction', 'concert']:
                            if term in title or term in channel:
                                score -= 25
                        
                        # Penalize videos with "lyrics" slightly (but they're often good matches)
                        if 'lyric' in title:
                            score -= 5
                            
                        # Favor higher view counts
                        if 'view_count' in full_info:
                            # Log-scale bonus for views (up to 10 points)
                            views = full_info['view_count']
                            if views > 0:
                                import math
                                view_bonus = min(10, math.log10(views))
                                score += view_bonus
                        
                        logger.debug(f"Score for '{title}': {score}")
                        scored_entries.append((score, full_info, url))
                        
                    except Exception as e:
                        logger.error(f"Error extracting full info for {entry['id']}: {e}")
                        continue
                
                # Sort by score and return the best match
                if scored_entries:
                    # Sort by score in descending order
                    scored_entries.sort(key=lambda x: x[0], reverse=True)
                    best_score, best_entry, best_url = scored_entries[0]
                    logger.info(f"Best match: '{best_entry.get('title')}' with score {best_score}")
                    return best_url
                
                # Fallback to first result if scoring fails
                return f"https://www.youtube.com/watch?v={valid_entries[0]['id']}"
                
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            # Fallback to simpler search
            return await self._simple_search(query)
        
    async def _simple_search(self, query: str) -> Optional[str]:
        """Simplified search as fallback"""
        search_options = self.ytdlp_options.copy()
        search_options['quiet'] = True
        search_options['no_warnings'] = True
        search_options['default_search'] = 'ytsearch'
        search_options['skip_download'] = True
        
        # Make sure we have ffmpeg location set
        if self.ffmpeg_path:
            search_options['ffmpeg_location'] = os.path.dirname(self.ffmpeg_path)
        
        try:
            with yt_dlp.YoutubeDL(search_options) as ydl:
                logger.debug(f"Performing simple search for: {query}")
                
                # Try YouTube Music first
                try:
                    info = ydl.extract_info(f"ytmsearch:{query}", download=False)
                except Exception:
                    # Fall back to regular YouTube
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    return None
                
                # Just return the first result
                return f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"
                
        except Exception as e:
            logger.error(f"Simple search failed: {e}")
            return None
        
    async def download(self, url: str, output_path: str, filename: str = None, quality: str = "320") -> str:
        """
        Download audio from a YouTube URL
        
        Args:
            url: YouTube URL
            output_path: Directory to save the file
            filename: Output filename without extension
            quality: Audio quality (bitrate for MP3)
            
        Returns:
            Path to downloaded file
        """
        # Add a message to the UI about what we're actually doing
        logger.info("Downloading highest quality audio available from YouTube Music/YouTube")
        
        os.makedirs(output_path, exist_ok=True)
        
        # Set up download options
        download_options = self.ytdlp_options.copy()
        download_options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }]
        
        # Make sure we're using our FFmpeg
        if self.ffmpeg_path:
            download_options['ffmpeg_location'] = os.path.dirname(self.ffmpeg_path)
            
        logger.debug(f"FFmpeg location: {download_options.get('ffmpeg_location')}")
        
        if filename:
            # Set custom output template
            download_options['outtmpl'] = os.path.join(output_path, f"{filename}.%(ext)s")
        else:
            # Use default template with title
            download_options['outtmpl'] = os.path.join(output_path, '%(title)s.%(ext)s')
        
        # Perform the download
        try:
            with yt_dlp.YoutubeDL(download_options) as ydl:
                logger.debug(f"Downloading audio from: {url}")
                info = ydl.extract_info(url, download=True)
                
                if filename:
                    output_file = os.path.join(output_path, f"{filename}.mp3")
                else:
                    title = info.get('title', 'download')
                    # Clean filename
                    title = re.sub(r'[\\/*?:"<>|]', '', title)
                    output_file = os.path.join(output_path, f"{title}.mp3")
                
                if os.path.exists(output_file):
                    return output_file
                    
                # Try to find the file in case the filename normalization was different
                mp3_files = [f for f in os.listdir(output_path) if f.endswith('.mp3')]
                if mp3_files:
                    # Return the most recently created file
                    newest_file = max(
                        [os.path.join(output_path, f) for f in mp3_files], 
                        key=os.path.getctime
                    )
                    return newest_file
                
                return None
                
        except Exception as e:
            logger.error(f"Error downloading from YouTube: {e}")
            return None
