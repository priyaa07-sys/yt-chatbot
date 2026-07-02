import re
from dataclasses import dataclass


def extract_video_id(url: str) -> str:
    """
    Extract the 11-character YouTube video ID from various URL formats.
    Supports:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
      - https://youtube.com/shorts/VIDEO_ID
    """
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(
        f"Could not extract a valid YouTube video ID from the URL: '{url}'. "
        "Please provide a valid YouTube link."
    )


@dataclass
class VideoMetadata:
    video_id: str
    title: str = "Unknown Title"
    author: str = "Unknown Channel"
    length_seconds: int = 0


def get_video_metadata(video_id: str) -> VideoMetadata:
    """
    Fetch video metadata via pytube with a safe fallback.
    pytube is unreliable against YouTube changes, so failures are silenced.
    """
    try:
        from pytube import YouTube  # type: ignore

        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return VideoMetadata(
            video_id=video_id,
            title=yt.title or f"Video ({video_id})",
            author=yt.author or "Unknown Channel",
            length_seconds=yt.length or 0,
        )
    except Exception:
        return VideoMetadata(
            video_id=video_id,
            title=f"YouTube Video ({video_id})",
            author="Unknown Channel",
            length_seconds=0,
        )


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> str:
    """
    Fetch the transcript for a YouTube video.

    IMPORTANT — API version note:
    youtube-transcript-api >= 1.0.0 removed the old class-method style:
        YouTubeTranscriptApi.get_transcript(video_id)   ← BROKEN in v1+
    It now requires instantiation:
        YouTubeTranscriptApi().fetch(video_id)           ← CORRECT for v1+

    Args:
        video_id: The 11-character YouTube video ID.
        languages: Preferred language codes e.g. ['en', 'en-US'].
                   Falls back to any available transcript if preferred not found.

    Returns:
        Full transcript as a single plain-text string (timestamps stripped).

    Raises:
        RuntimeError: If no transcript is available for the video.
    """
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    from youtube_transcript_api._errors import (             # type: ignore
        TranscriptsDisabled,
        NoTranscriptFound,
        # TranscriptionUndefined,
    )

    # v1.0+ requires an instance — DO NOT call as a class method
    api = YouTubeTranscriptApi()

    preferred = languages or ["en", "en-US", "en-GB"]

    try:
        fetched = api.fetch(video_id, languages=preferred)
    except NoTranscriptFound:
        # Preferred language not available — fall back to any transcript
        try:
            transcript_list = api.list(video_id)
            fetched = next(iter(transcript_list)).fetch()
        except StopIteration:
            raise RuntimeError(
                "No transcripts are available for this video."
            )
    except TranscriptsDisabled:
        raise RuntimeError(
            "Transcripts are disabled for this video. "
            "Please try a video that has captions/subtitles enabled."
        )
    
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript: {str(e)}")

    # FetchedTranscript is iterable; each snippet exposes a .text attribute
    segments = [snippet.text.strip() for snippet in fetched if snippet.text.strip()]
    if not segments:
        raise RuntimeError("Transcript was fetched but contained no text.")

    return " ".join(segments)


def extract_transcript_from_url(url: str) -> tuple[str, VideoMetadata]:
    """High-level helper: YouTube URL → (transcript_text, VideoMetadata)."""
    video_id = extract_video_id(url)
    transcript = fetch_transcript(video_id)
    metadata = get_video_metadata(video_id)
    return transcript, metadata