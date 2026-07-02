import sqlite3
import sqlite_vec
import struct
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "data" / "app.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


@contextmanager
def db_connection():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_connection() as conn:
       
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id           TEXT PRIMARY KEY,
                video_url    TEXT NOT NULL,
                title        TEXT,
                author       TEXT,
                transcript   TEXT,
                segment_count INTEGER,
                status       TEXT DEFAULT 'processing',
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id          TEXT PRIMARY KEY,
                video_id    TEXT NOT NULL,
                content     TEXT NOT NULL,
                chunk_index INTEGER
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(
                chunk_id  TEXT PRIMARY KEY,
                embedding FLOAT[768]
            )
        """)

    print(f"✓ Database initialised at {DB_PATH}")

def generate_id() -> str:
    return str(uuid.uuid4())


def _pack(embedding: List[float]) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding)


def create_video(
    video_url: str,
    transcript: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    segment_count: Optional[int] = None,) -> str:
    video_id = generate_id()
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO videos
                (id, video_url, title, author, transcript, segment_count, status)
            VALUES (?, ?, ?, ?, ?, ?, 'ready')
            """,
            (video_id, video_url, title, author, transcript, segment_count),
        )
    return video_id


def get_video(video_id: str) -> Optional[dict]:
    with db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM videos WHERE id = ?", (video_id,)
        ).fetchone()
        return dict(row) if row else None


def list_videos() -> List[dict]:
    with db_connection() as conn:
        rows = conn.execute(
            """SELECT id, video_url, title, author, segment_count, status, created_at
               FROM videos ORDER BY created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

def create_chunks(video_id: str, chunks: List[Tuple[str, List[float]]]):
    
    with db_connection() as conn:
        for idx, (content, embedding) in enumerate(chunks):
            chunk_id = generate_id()

            # 1. Text/metadata row
            conn.execute(
                "INSERT INTO chunks (id, video_id, content, chunk_index) VALUES (?, ?, ?, ?)",
                (chunk_id, video_id, content, idx),
            )

            # 2. Embedding row (vec0)
            conn.execute(
                "INSERT INTO chunk_vectors (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, _pack(embedding)),
            )


def search_similar_chunks(
    query_embedding: List[float],
    video_id: Optional[str] = None,
    limit: int = 5,
) -> List[dict]:

    fetch_k = limit * 4 if video_id else limit

    with db_connection() as conn:
        # Step 1 — KNN search (vec0 only)
        knn_rows = conn.execute(
            """
            SELECT chunk_id, distance
            FROM chunk_vectors
            WHERE embedding MATCH ?
            LIMIT ?
            """,
            (_pack(query_embedding), fetch_k),
        ).fetchall()

        if not knn_rows:
            return []

        chunk_ids = [r["chunk_id"] for r in knn_rows]
        distance_map = {r["chunk_id"]: r["distance"] for r in knn_rows}

        placeholders = ",".join("?" * len(chunk_ids))
        meta_rows = conn.execute(
            f"SELECT id, video_id, content, chunk_index FROM chunks WHERE id IN ({placeholders})",
            chunk_ids,
        ).fetchall()

    results = []
    for row in meta_rows:
        d = dict(row)
        d["distance"] = distance_map[d["id"]]
        if video_id and d["video_id"] != video_id:
            continue
        results.append(d)

    results.sort(key=lambda x: x["distance"])
    return results[:limit]


def delete_video(video_id: str):
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM chunks WHERE video_id = ?", (video_id,)
        ).fetchall()
        chunk_ids = [r["id"] for r in rows]

        if chunk_ids:
            placeholders = ",".join("?" * len(chunk_ids))
            conn.execute(
                f"DELETE FROM chunk_vectors WHERE chunk_id IN ({placeholders})",
                chunk_ids,
            )

        conn.execute("DELETE FROM chunks WHERE video_id = ?", (video_id,))
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))