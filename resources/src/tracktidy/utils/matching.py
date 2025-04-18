"""
Matching utilities for TrackTidy
"""
import logging
import re
from typing import List, Dict, Tuple, Optional
from math import exp

logger = logging.getLogger("tracktidy")

# List of forbidden words that indicate a non-original track
FORBIDDEN_WORDS = [
    "bassboosted",
    "remix",
    "remastered",
    "remaster",
    "reverb",
    "bassboost",
    "live",
    "acoustic",
    "8daudio",
    "concert",
    "live",
    "acapella",
    "slowed",
    "instrumental",
    "remix",
    "cover",
    "reverb",
    "nightcore",
    "edit",
    "vip",
    "extended",
    "rework",
]

def slugify(text: str) -> str:
    """
    Convert text to a normalized form for better matching
    
    Args:
        text: The text to slugify
        
    Returns:
        Slugified text
    """
    if not text:
        return ""
        
    # Convert to lowercase and replace special chars with '-'
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def calculate_string_ratio(str1: str, str2: str) -> float:
    """
    Calculate the similarity ratio between two strings
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity ratio (0-100)
    """
    from difflib import SequenceMatcher
    
    if not str1 or not str2:
        return 0.0
        
    return SequenceMatcher(None, str1, str2).ratio() * 100

def check_common_words(title: str, video_title: str) -> bool:
    """
    Check if there are common words between the track title and video title
    
    Args:
        title: Track title
        video_title: Video title
        
    Returns:
        True if common words found
    """
    title_words = set(slugify(title).split('-'))
    video_title = slugify(video_title)
    
    for word in title_words:
        if word and word in video_title:
            return True
            
    return False

def check_forbidden_words(title: str, video_title: str) -> Tuple[bool, List[str]]:
    """
    Check if video title contains forbidden words
    
    Args:
        title: Original track title (to exclude legitimate words)
        video_title: Video title to check
        
    Returns:
        Tuple of (has_forbidden, [forbidden_words])
    """
    title_slug = slugify(title).replace('-', '')
    video_slug = slugify(video_title).replace('-', '')
    
    words = []
    for word in FORBIDDEN_WORDS:
        if word in video_slug and word not in title_slug:
            words.append(word)
            
    return len(words) > 0, words
    
def calculate_title_match(track_title: str, video_title: str) -> float:
    """
    Calculate title match score
    
    Args:
        track_title: Original track title
        video_title: Video title
        
    Returns:
        Match score (0-100)
    """
    # Create slugified versions
    track_slug = slugify(track_title)
    video_slug = slugify(video_title)
    
    # Calculate initial match
    match_score = calculate_string_ratio(track_slug, video_slug)
    
    # Check for forbidden words
    has_forbidden, forbidden_words = check_forbidden_words(track_title, video_title)
    if has_forbidden:
        # Penalize for each forbidden word
        for _ in forbidden_words:
            match_score -= 15
    
    return max(0, match_score)

def calculate_artist_match(track_artists: List[str], video_title: str, channel: str) -> float:
    """
    Calculate artist match score
    
    Args:
        track_artists: List of artist names
        video_title: Video title
        channel: Channel name
        
    Returns:
        Match score (0-100)
    """
    if not track_artists:
        return 0.0
        
    # Primary artist match
    primary_artist = track_artists[0]
    primary_artist_slug = slugify(primary_artist)
    
    # Check if primary artist is in the title
    video_title_slug = slugify(video_title)
    channel_slug = slugify(channel)
    
    # Check title match
    if primary_artist_slug in video_title_slug:
        match_score = 90.0
    # Check channel match
    elif primary_artist_slug in channel_slug:
        match_score = 80.0
    # Check partial match
    elif any(word in video_title_slug for word in primary_artist_slug.split('-')):
        match_score = 70.0
    else:
        match_score = calculate_string_ratio(primary_artist_slug, channel_slug) / 2
    
    # Check for additional artists
    if len(track_artists) > 1:
        additional_score = 0
        for artist in track_artists[1:]:
            artist_slug = slugify(artist)
            if artist_slug in video_title_slug or artist_slug in channel_slug:
                additional_score += 10
                
        # Average the additional score with a maximum bonus of 10 per artist
        bonus = min(additional_score, 10 * len(track_artists[1:]))
        match_score = (match_score + bonus) / (1 + (len(track_artists) > 1))
    
    return min(match_score, 100.0)

def calculate_duration_match(track_duration: int, video_duration: int) -> float:
    """
    Calculate duration match using exponential penalty
    
    Args:
        track_duration: Track duration in seconds
        video_duration: Video duration in seconds
        
    Returns:
        Match score (0-100)
    """
    if track_duration <= 0 or video_duration <= 0:
        return 50.0  # Default middle score if duration unknown
        
    time_diff = abs(track_duration - video_duration)
    score = exp(-0.1 * time_diff)  # Exponential decay for differences
    return score * 100

def score_video(
    track_title: str, 
    track_artists: List[str], 
    track_duration: int,
    video_title: str,
    video_channel: str,
    video_duration: int,
    is_verified: bool = False
) -> Tuple[float, Dict[str, float]]:
    """
    Score a YouTube video for match quality
    
    Args:
        track_title: Original track title
        track_artists: List of artists
        track_duration: Track duration in seconds
        video_title: YouTube video title
        video_channel: YouTube channel name
        video_duration: Video duration in seconds
        is_verified: Whether this is a "verified" music video
        
    Returns:
        Tuple of (total_score, detailed_scores)
    """
    # Skip videos with no common words in title
    if not check_common_words(track_title, video_title):
        return 0, {"reason": "No common words found"}
    
    # Calculate individual scores
    title_score = calculate_title_match(track_title, video_title)
    artist_score = calculate_artist_match(track_artists, video_title, video_channel)
    duration_score = calculate_duration_match(track_duration, video_duration)
    
    # Apply quality bonuses
    bonuses = 0
    
    # Official content bonus
    if " - topic" in video_channel.lower():
        bonuses += 15
    elif "official" in video_title.lower() or "official" in video_channel.lower():
        bonuses += 10
    elif "vevo" in video_channel.lower():
        bonuses += 8
    
    # Audio/song keyword bonus  
    if "official audio" in video_title.lower():
        bonuses += 10
    elif "audio" in video_title.lower():
        bonuses += 5
    
    # Verified content (from YT Music) gets a bonus
    if is_verified:
        bonuses += 10
    
    # Calculate weighted score
    if title_score < 60:
        return 0, {"reason": "Title score too low", "title_score": title_score}
        
    if artist_score < 50 and not is_verified:
        return 0, {"reason": "Artist score too low", "artist_score": artist_score}
        
    # Higher weight on title and artist match, lower on duration
    if is_verified:
        # For verified tracks, we trust the title match more
        total_score = (title_score * 0.5) + (artist_score * 0.3) + (duration_score * 0.2) + bonuses
    else:
        # For non-verified, we need more artist match confidence
        total_score = (title_score * 0.4) + (artist_score * 0.4) + (duration_score * 0.2) + bonuses
    
    # Cap at 100
    total_score = min(total_score, 100)
    
    return total_score, {
        "title_score": title_score,
        "artist_score": artist_score,
        "duration_score": duration_score,
        "bonuses": bonuses,
        "total_score": total_score
    }
