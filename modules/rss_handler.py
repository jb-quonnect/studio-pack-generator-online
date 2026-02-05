"""
Studio Pack Generator Online - RSS Handler

Handles RSS feed parsing and podcast episode management:
- Parse RSS/Atom feeds using feedparser
- Extract episode metadata (title, description, duration, image)
- Download audio enclosures
- Split episodes into parts based on user settings
"""

import os
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import requests

try:
    import feedparser
except ImportError:
    feedparser = None

from .utils import sanitize_filename, ensure_dir, format_duration


logger = logging.getLogger(__name__)


@dataclass
class RssEpisode:
    """Represents a single podcast episode."""
    
    title: str
    url: str  # Audio URL
    description: str = ""
    duration: float = 0.0  # In seconds
    image_url: Optional[str] = None
    published: Optional[str] = None
    season: Optional[int] = None
    episode_number: Optional[int] = None
    guid: str = ""
    
    # Local paths after download
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    
    # Selection state
    selected: bool = True


@dataclass
class RssFeed:
    """Represents a parsed RSS feed."""
    
    title: str
    description: str = ""
    image_url: Optional[str] = None
    link: str = ""
    episodes: List[RssEpisode] = field(default_factory=list)
    
    # Metadata
    author: str = ""
    language: str = "fr"


def parse_duration(duration_str: str) -> float:
    """
    Parse duration string to seconds.
    
    Supports formats:
    - HH:MM:SS
    - MM:SS
    - Seconds as integer
    
    Args:
        duration_str: Duration string
        
    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0
    
    try:
        # Try integer seconds
        return float(duration_str)
    except ValueError:
        pass
    
    # Try HH:MM:SS or MM:SS
    parts = duration_str.split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        pass
    
    return 0.0


def parse_rss_feed(url: str) -> Optional[RssFeed]:
    """
    Parse an RSS feed from URL.
    
    Args:
        url: RSS feed URL
        
    Returns:
        RssFeed object or None if failed
    """
    if feedparser is None:
        logger.error("feedparser not installed")
        return None
    
    try:
        logger.info(f"Parsing RSS feed: {url}")
        
        # Parse the feed
        feed = feedparser.parse(url)
        
        if feed.bozo and not feed.entries:
            logger.error(f"Failed to parse RSS: {feed.bozo_exception}")
            return None
        
        # Extract feed metadata
        rss_feed = RssFeed(
            title=feed.feed.get('title', 'Unknown Podcast'),
            description=feed.feed.get('description', ''),
            link=feed.feed.get('link', ''),
            author=feed.feed.get('author', ''),
            language=feed.feed.get('language', 'fr')
        )
        
        # Get feed image
        if 'image' in feed.feed:
            rss_feed.image_url = feed.feed.image.get('href') or feed.feed.image.get('url')
        elif 'itunes_image' in feed.feed:
            rss_feed.image_url = feed.feed.itunes_image.get('href')
        
        # Parse episodes
        for entry in feed.entries:
            episode = parse_episode(entry)
            if episode:
                rss_feed.episodes.append(episode)
        
        logger.info(f"Parsed {len(rss_feed.episodes)} episodes from {rss_feed.title}")
        return rss_feed
        
    except Exception as e:
        logger.error(f"Failed to parse RSS feed: {e}")
        return None


def parse_episode(entry: Dict) -> Optional[RssEpisode]:
    """
    Parse a single episode entry from feedparser.
    
    Args:
        entry: Feedparser entry dict
        
    Returns:
        RssEpisode or None if no audio enclosure
    """
    # Find audio enclosure
    audio_url = None
    for enclosure in entry.get('enclosures', []):
        if 'audio' in enclosure.get('type', ''):
            audio_url = enclosure.get('href') or enclosure.get('url')
            break
    
    # Also check media content
    if not audio_url:
        for media in entry.get('media_content', []):
            if 'audio' in media.get('type', ''):
                audio_url = media.get('url')
                break
    
    # Also check links
    if not audio_url:
        for link in entry.get('links', []):
            if 'audio' in link.get('type', ''):
                audio_url = link.get('href')
                break
    
    if not audio_url:
        return None  # No audio found
    
    # Get title
    title = entry.get('title', 'Untitled Episode')
    
    # Get description
    description = ''
    if 'summary' in entry:
        description = entry['summary']
    elif 'description' in entry:
        description = entry['description']
    
    # Strip HTML from description
    description = re.sub(r'<[^>]+>', '', description)[:500]
    
    # Get duration
    duration = 0.0
    if 'itunes_duration' in entry:
        duration = parse_duration(entry['itunes_duration'])
    
    # Get image
    image_url = None
    if 'image' in entry:
        image_url = entry['image'].get('href')
    elif 'itunes_image' in entry:
        image_url = entry['itunes_image'].get('href')
    
    # Get season/episode numbers
    season = None
    episode_num = None
    
    if 'itunes_season' in entry:
        try:
            season = int(entry['itunes_season'])
        except (ValueError, TypeError):
            pass
    
    if 'itunes_episode' in entry:
        try:
            episode_num = int(entry['itunes_episode'])
        except (ValueError, TypeError):
            pass
    
    # Get GUID
    guid = entry.get('id', '') or entry.get('guid', '')
    
    # Get published date
    published = entry.get('published', '')
    
    return RssEpisode(
        title=title,
        url=audio_url,
        description=description,
        duration=duration,
        image_url=image_url,
        season=season,
        episode_number=episode_num,
        guid=guid,
        published=published
    )


def download_episode_audio(
    episode: RssEpisode,
    output_dir: str,
    progress_callback=None
) -> bool:
    """
    Download the audio file for an episode.
    
    Args:
        episode: RssEpisode object
        output_dir: Directory to save to
        progress_callback: Optional callback for progress updates
        
    Returns:
        True if successful
    """
    if not episode.url:
        return False
    
    try:
        ensure_dir(output_dir)
        
        # Generate filename
        filename = sanitize_filename(episode.title)[:100]
        
        # Determine extension from URL
        parsed = urlparse(episode.url)
        ext = os.path.splitext(parsed.path)[1] or '.mp3'
        
        output_path = os.path.join(output_dir, f"{filename}{ext}")
        
        # Download with streaming
        logger.info(f"Downloading: {episode.title}")
        
        response = requests.get(episode.url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size:
                        progress_callback(downloaded / total_size)
        
        episode.audio_path = output_path
        logger.info(f"Downloaded: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download episode: {e}")
        return False


def download_episode_image(episode: RssEpisode, output_dir: str) -> bool:
    """
    Download the image for an episode.
    
    Args:
        episode: RssEpisode object
        output_dir: Directory to save to
        
    Returns:
        True if successful
    """
    if not episode.image_url:
        return False
    
    try:
        ensure_dir(output_dir)
        
        filename = sanitize_filename(episode.title)[:100]
        
        # Determine extension
        parsed = urlparse(episode.image_url)
        ext = os.path.splitext(parsed.path)[1] or '.jpg'
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'
        
        output_path = os.path.join(output_dir, f"{filename}.item{ext}")
        
        response = requests.get(episode.image_url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        episode.image_path = output_path
        return True
        
    except Exception as e:
        logger.error(f"Failed to download episode image: {e}")
        return False


def download_feed_image(feed: RssFeed, output_dir: str) -> Optional[str]:
    """
    Download the main image from a podcast feed.
    
    Args:
        feed: RssFeed object with image_url
        output_dir: Directory to save to
        
    Returns:
        Path to downloaded image or None if failed
    """
    if not feed.image_url:
        logger.info("No feed image URL available")
        return None
    
    try:
        ensure_dir(output_dir)
        
        filename = sanitize_filename(feed.title)[:50]
        
        # Determine extension
        parsed = urlparse(feed.image_url)
        ext = os.path.splitext(parsed.path)[1] or '.jpg'
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'
        
        output_path = os.path.join(output_dir, f"{filename}_cover{ext}")
        
        logger.info(f"Downloading feed image: {feed.image_url}")
        response = requests.get(feed.image_url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded feed image: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download feed image: {e}")
        return None


def split_episodes_into_parts(
    episodes: List[RssEpisode],
    episodes_per_part: int = 10
) -> List[List[RssEpisode]]:
    """
    Split episodes into parts based on the specified size.
    
    Args:
        episodes: List of episodes
        episodes_per_part: Number of episodes per part
        
    Returns:
        List of lists, each representing a part
    """
    if episodes_per_part <= 0:
        episodes_per_part = 10
    
    parts = []
    for i in range(0, len(episodes), episodes_per_part):
        parts.append(episodes[i:i + episodes_per_part])
    
    return parts


def group_episodes_by_season(
    episodes: List[RssEpisode]
) -> Dict[Optional[int], List[RssEpisode]]:
    """
    Group episodes by season number.
    
    Args:
        episodes: List of episodes
        
    Returns:
        Dictionary with season number as key, episodes as value
    """
    seasons: Dict[Optional[int], List[RssEpisode]] = {}
    
    for episode in episodes:
        season = episode.season
        if season not in seasons:
            seasons[season] = []
        seasons[season].append(episode)
    
    return seasons


def filter_episodes_by_duration(
    episodes: List[RssEpisode],
    min_duration: float = 0
) -> List[RssEpisode]:
    """
    Filter episodes by minimum duration.
    
    Args:
        episodes: List of episodes
        min_duration: Minimum duration in seconds
        
    Returns:
        Filtered list of episodes
    """
    if min_duration <= 0:
        return episodes
    
    return [ep for ep in episodes if ep.duration >= min_duration]


def get_selected_episodes(episodes: List[RssEpisode]) -> List[RssEpisode]:
    """
    Get only the selected episodes.
    
    Args:
        episodes: List of all episodes
        
    Returns:
        List of selected episodes
    """
    return [ep for ep in episodes if ep.selected]
