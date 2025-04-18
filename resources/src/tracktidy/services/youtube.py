"""
YouTube service for TrackTidy
"""
import logging
import re
import os
import json
from typing import Optional, List, Callable, Dict, Tuple, Any
import yt_dlp

from ..utils.matching import score_video
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
    
    async def search_best_match(self, query: str, duration: Optional[int] = None, limit: int = 10, artists: Optional[List[str]] = None) -> Optional[str]:
        """
        Search YouTube for best matching video
        
        Args:
            query: Search query string
            duration: Track duration in seconds for better matching
            limit: Number of results to check
            artists: List of artist names for better matching
            
        Returns:
            YouTube URL of best match or None if no match found
        """
        # For debugging log
        logger.info(f"Searching for: {query}, duration: {duration}")
        
        # Normalize artist list
        if artists is None:
            # Try to extract artists from the query as a fallback
            parts = query.split(' - ', 1)
            if len(parts) > 1:
                artists = [parts[0]]
            else:
                artists = []
                
        # Create a more specific query for official content
        artist_str = artists[0] if artists else ""
        official_query = f"{artist_str} {query.split(' - ')[-1]} official audio".strip()
        
        # Try to use ytmusicapi if possible for more accurate results
        try:
            from ytmusicapi import YTMusic
            ytmusic = YTMusic()
            
            # First search with YTMusic API which will give more accurate results
            logger.info(f"Searching YouTube Music API for: {query}")
            search_results = ytmusic.search(query, filter="songs", limit=limit)
            
            # Check if we got valid results
            if search_results and len(search_results) > 0:
                # Score each result
                scored_entries = []
                for result in search_results:
                    # Skip items without videoId
                    if 'videoId' not in result:
                        continue
                        
                    # Extract information
                    video_id = result['videoId']
                    video_title = result['title']
                    artist_names = [artist['name'] for artist in result['artists']] if 'artists' in result else []
                    video_duration = 0
                    if 'duration' in result and result['duration']:
                        duration_parts = result['duration'].split(':')
                        if len(duration_parts) == 2:  # MM:SS format
                            video_duration = int(duration_parts[0]) * 60 + int(duration_parts[1])
                        elif len(duration_parts) == 3:  # HH:MM:SS format
                            video_duration = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
                    
                    # Get the channel name (usually the main artist for Topic channels)
                    video_channel = artist_names[0] if artist_names else ""
                    
                    # Score this result
                    score, details = score_video(
                        track_title=query,
                        track_artists=artists,
                        track_duration=duration or 0,
                        video_title=video_title,
                        video_channel=video_channel,
                        video_duration=video_duration,
                        is_verified=True  # YouTube Music results are verified
                    )
                    
                    if score > 0:
                        # Create a music.youtube.com URL
                        url = f"https://music.youtube.com/watch?v={video_id}"
                        scored_entries.append((score, result, url, details))
                        logger.info(f"YTMusic result: {video_title} - Score: {score}")
                
                # If we found good matches, return the best one
                if scored_entries:
                    # Sort by score
                    scored_entries.sort(key=lambda x: x[0], reverse=True)
                    best_result = scored_entries[0]
                    
                    # If score is good, return it
                    if best_result[0] >= 70:
                        logger.info(f"Using YouTube Music result: {best_result[1]['title']} (Score: {best_result[0]})")
                        return best_result[2]  # Return the music.youtube.com URL
                    else:
                        logger.info(f"Best YouTube Music result had low score: {best_result[0]}")
            else:
                logger.info("No results from YouTube Music API")
                
        except Exception as e:
            logger.info(f"YouTube Music API error: {e}, falling back to yt-dlp")
        
        # Fall back to yt-dlp method if ytmusicapi fails or returns poor results
        # Create search queries for different strategies
        search_strategies = [
            {"query": query, "source": "music"},  # Try YouTube Music first
            {"query": official_query, "source": "music"},  # YouTube Music with "official audio"
            {"query": query, "source": "youtube"},  # Try regular YouTube
            {"query": official_query, "source": "youtube"}  # YouTube with "official audio"
        ]
        
        best_match = None
        best_score = 0
        best_match_details = {}
        
        # Try each search strategy until we find a good match
        for strategy in search_strategies:
            strategy_query = strategy["query"]
            source = strategy["source"]
            is_music = source == "music"  # YouTube Music results are considered verified
            
            logger.info(f"Trying search strategy: {strategy}")
            
            # Format the search term based on the source
            if source == "music":
                search_term = f"ytmsearch{limit}:{strategy_query}"  # YouTube Music search
            else:
                search_term = f"ytsearch{limit}:{strategy_query}"  # Regular YouTube search
                
            # Configure search options
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
                with yt_dlp.YoutubeDL(search_options) as ydl:
                    logger.info(f"Executing search: {search_term}")
                    
                    try:
                        # Perform the search
                        info = ydl.extract_info(search_term, download=False)
                        
                        if not info or 'entries' not in info or not info['entries']:
                            logger.info(f"No results for strategy: {strategy}")
                            continue
                            
                        entries = info['entries']
                        
                        # Filter out livestreams
                        valid_entries = []
                        for entry in entries:
                            if not entry or entry.get('is_live', False):
                                continue
                            valid_entries.append(entry)
                        
                        if not valid_entries:
                            logger.info("No valid (non-livestream) results found")
                            continue
                            
                        # Process and score each entry
                        scored_entries = []
                        for entry in valid_entries:
                            if not entry.get('id'):
                                continue
                                
                            # Skip channel IDs (common error)
                            if entry['id'].startswith('UC'):
                                logger.info(f"Skipping channel ID: {entry['id']}")
                                continue
                            
                            # Get full info for each candidate to score properly
                            try:
                                # Create URL based on source
                                if source == "music" and is_music:
                                    url = f"https://music.youtube.com/watch?v={entry['id']}"
                                else:
                                    url = f"https://www.youtube.com/watch?v={entry['id']}"
                                    
                                # Get detailed info
                                full_info = ydl.extract_info(url, download=False, process=True)
                                
                                # Extract needed information for scoring
                                video_title = full_info.get('title', '')
                                video_channel = full_info.get('channel', '')
                                video_duration = full_info.get('duration', 0)
                                
                                logger.info(f"Scoring: {video_title} by {video_channel}")
                                
                                # Score this video match
                                score, details = score_video(
                                    track_title=query,
                                    track_artists=artists,
                                    track_duration=duration or 0,
                                    video_title=video_title,
                                    video_channel=video_channel,
                                    video_duration=video_duration,
                                    is_verified=is_music
                                )
                                
                                if score > 0:  # Only consider valid matches
                                    scored_entries.append((score, full_info, url, details))
                                    logger.info(f"Score: {score}, Details: {details}")
                                    
                            except Exception as e:
                                logger.info(f"Error scoring entry {entry['id']}: {e}")
                                continue
                        
                        # Find the best match from this strategy
                        if scored_entries:
                            # Sort by score in descending order
                            scored_entries.sort(key=lambda x: x[0], reverse=True)
                            strategy_best = scored_entries[0]
                            
                            # Check if this is better than our current best match
                            if strategy_best[0] > best_score:
                                best_score = strategy_best[0]
                                best_match = strategy_best[2]  # URL
                                best_match_details = {
                                    "title": strategy_best[1].get('title', ''),
                                    "channel": strategy_best[1].get('channel', ''),
                                    "score": best_score,
                                    "details": strategy_best[3],
                                    "strategy": strategy
                                }
                                
                                # If we found an excellent match (>85), stop searching
                                if best_score > 85:
                                    logger.info(f"Found excellent match: {best_match} with score {best_score}")
                                    break
                                    
                    except Exception as e:
                        logger.info(f"Search error: {e}, trying next strategy")
                
            except Exception as e:
                logger.error(f"YoutubeDL error: {e}")
        
        # Log the best match we found
        if best_match:
            logger.info(f"Best match: {best_match} with score {best_score}")
            logger.info(f"Match details: {json.dumps(best_match_details)}")
            return best_match
        else:
            logger.warning(f"No suitable match found for: {query}")
            return None
        
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
                    
                    # Ensure we actually got useful results
                    if info and 'entries' in info and info['entries']:
                        video_id = info['entries'][0]['id']
                        if video_id.startswith('UC'):  # This is a channel ID, not a video ID
                            logger.error(f"Received channel ID instead of video ID: {video_id}")
                            # Fallback to regular YouTube search
                            raise Exception("Channel ID received, trying regular YouTube")
                        return f"https://www.youtube.com/watch?v={video_id}"
                    else:
                        raise Exception("No results from YouTube Music")
                        
                except Exception as e:
                    logger.debug(f"YouTube Music search failed in simple search: {e}")
                    # Fall back to regular YouTube
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)
                    
                    if not info or 'entries' not in info or not info['entries']:
                        return None
                        
                    # Verify we have a valid video ID, not a channel ID
                    video_id = info['entries'][0]['id']
                    if video_id.startswith('UC'):  # This is a channel ID, not a video ID
                        logger.error(f"Received channel ID instead of video ID: {video_id}")
                        return None
                        
                    # Get the full video info to make sure it exists and is accessible
                    try:
                        url = f"https://www.youtube.com/watch?v={video_id}"
                        full_info = ydl.extract_info(url, download=False, process=True)
                        # If we got here, video exists and is accessible
                        return url
                    except Exception as e:
                        logger.error(f"Error verifying video: {e}")
                        return None
                
        except Exception as e:
            logger.error(f"Simple search failed: {e}")
            return None
        
    async def download(self, url: str, output_path: str, filename: str = None, quality: str = "320",
                      progress_callback: Optional[Callable[[str, float, str], None]] = None) -> str:
        """
        Download audio from a YouTube URL
        
        Args:
            url: YouTube URL
            output_path: Directory to save the file
            filename: Output filename without extension
            quality: Audio quality (bitrate for MP3)
            progress_callback: Callback function for progress updates
            
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
        
        # Custom progress hook to track download progress
        def progress_hook(d):
            if d['status'] == 'downloading':
                if progress_callback:
                    # Extract percentage from _percent_str which is like "100.0%"
                    percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
                    try:
                        percent = float(percent_str) if percent_str else 0
                    except ValueError:
                        percent = 0
                        
                    # Extract download speed
                    speed = d.get('_speed_str', 'unknown speed')
                    
                    # Call the progress callback with status info
                    status = f"Downloading: {percent:.1f}% ({speed})"
                    progress_callback('download', percent / 100.0, status)
                    
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback('download', 1.0, "Download complete, processing...")
                    
            elif d['status'] == 'error':
                if progress_callback:
                    progress_callback('error', 0, f"Error: {d.get('error', 'unknown error')}")
        
        # Add our custom progress hook
        download_options['progress_hooks'] = [progress_hook]
        
        # Perform the download
        try:
            with yt_dlp.YoutubeDL(download_options) as ydl:
                logger.debug(f"Downloading audio from: {url}")
                
                # Start download process
                if progress_callback:
                    progress_callback('start', 0, "Starting download...")
                    
                info = ydl.extract_info(url, download=True)
                
                # Signal post-processing step
                if progress_callback:
                    progress_callback('processing', 0, "Converting audio...")
                
                # Wait a moment for file operations to complete
                import time
                time.sleep(0.5)  # Reduced wait time for better responsiveness
                
                if filename:
                    output_file = os.path.join(output_path, f"{filename}.mp3")
                else:
                    title = info.get('title', 'download')
                    # Clean filename
                    title = re.sub(r'[\\/*?:"<>|]', '', title)
                    output_file = os.path.join(output_path, f"{title}.mp3")
                
                if os.path.exists(output_file):
                    # Signal completion
                    if progress_callback:
                        progress_callback('complete', 1.0, "Download complete!")
                    return output_file
                    
                # Try to find the file in case the filename normalization was different
                mp3_files = [f for f in os.listdir(output_path) if f.endswith('.mp3')]
                if mp3_files:
                    # Return the most recently created file
                    newest_file = max(
                        [os.path.join(output_path, f) for f in mp3_files], 
                        key=os.path.getctime
                    )
                    
                    # Signal completion
                    if progress_callback:
                        progress_callback('complete', 1.0, "Download complete!")
                    return newest_file
                
                # Signal failure
                if progress_callback:
                    progress_callback('error', 0, "Download failed - couldn't find output file")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading from YouTube: {e}")
            # Signal error through callback
            if progress_callback:
                progress_callback('error', 0, f"Error: {str(e)}")
            return None
