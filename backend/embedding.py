from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from yt_extract import fetch_transcript

load_dotenv(Path(__file__).parent / ".env")

def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model="nomic-embed-text",
        temperature=0,
    )

def embed_text(text: str) -> List[float]:
    model = get_embedding_model()
    return model.embed_query(text)

def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    return model.embed_documents(texts)

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)