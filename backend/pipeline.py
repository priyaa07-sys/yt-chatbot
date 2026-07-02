from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from yt_extract import extract_video_id, fetch_transcript, get_video_metadata
from embedding import chunk_text, embed_texts
from database import create_video, create_chunks, get_video, list_videos
from llm_engine import query_video, QueryResult


@dataclass
class ProcessedVideo:
    """Result of processing a YouTube video."""
    video_id: str
    title: str
    author: str
    segment_count: int
    status: str


def process_youtube_video(
    url: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> ProcessedVideo:
    """
    Full pipeline: YouTube URL → Transcript → Chunks → Embeddings → DB

    Args:
        url: YouTube video URL (any supported format)
        chunk_size: Characters per text chunk
        chunk_overlap: Overlap between consecutive chunks

    Returns:
        ProcessedVideo dataclass with video metadata and processing stats
    """
    print(f"▶ Processing YouTube video: {url}")

    yt_video_id = extract_video_id(url)
    print(f"  → Video ID: {yt_video_id}")

    print("  → Fetching video metadata...")
    metadata = get_video_metadata(yt_video_id)
    print(f"  → Title: {metadata.title}")
    print(f"  → Channel: {metadata.author}")

    print("  → Fetching transcript...")
    transcript = fetch_transcript(yt_video_id)
    print(f"  → Fetched {len(transcript)} characters of transcript")

    print("  → Chunking transcript...")
    chunks = chunk_text(transcript, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"  → Created {len(chunks)} chunks")

    print("  → Generating embeddings...")
    embeddings = embed_texts(chunks)
    print(f"  → Generated {len(embeddings)} embeddings")

    print("  → Storing in database...")
    db_video_id = create_video(
        video_url=url,
        transcript=transcript,
        title=metadata.title,
        author=metadata.author,
        segment_count=len(chunks),
    )

    create_chunks(db_video_id, list(zip(chunks, embeddings)))
    print(f"  ✓ Video stored with ID: {db_video_id}")

    return ProcessedVideo(
        video_id=db_video_id,
        title=metadata.title,
        author=metadata.author,
        segment_count=len(chunks),
        status="ready",
    )


def ask_question(question: str, video_id: Optional[str] = None) -> QueryResult:
    """
    Ask a question about a processed YouTube video's transcript.

    Args:
        question: The user's question
        video_id: DB video ID (UUID). If None, searches across all videos.

    Returns:
        QueryResult with answer and source references
    """
    return query_video(question, video_id=video_id)

if __name__ == "__main__":
    import sys
    from database import init_db

    print("=" * 60)
    print(" chat about a yt_video")
    print("=" * 60)

    init_db()

    if len(sys.argv) > 1:
        video_url = sys.argv[1]

        result = process_youtube_video(video_url)
        print(f"\n✅ Video processed successfully!")
        print(f"   Title: {result.title}")
        print(f"   Chunks: {result.segment_count}")

        print("\n Ask questions about the video (type 'quit' to exit):\n")

        while True:
            question = input("You: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not question:
                continue

            answer = ask_question(question, video_id=result.video_id)
            print(f"\n🤖 Assistant:\n{answer.answer}\n")
    else:
        print("\nUsage:")
        print("  python pipeline.py <youtube_url>")
        print("\nExample:")
        print('  python pipeline.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"')