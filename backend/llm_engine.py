import logging
from typing import TypedDict, List, Optional
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

from embedding import embed_text
from database import search_similar_chunks

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL       = "llama3.2:1b"


@dataclass
class SourceReference:
    content: str
    chunk_index: int
    video_id: str
    relevance_score: float


@dataclass
class QueryResult:
    answer: str
    sources: List[SourceReference]
    query: str


class RAGState(TypedDict):
    question: str
    video_id: Optional[str]
    context:  List[dict]
    answer:   str


def retrieve(state: RAGState) -> dict:
    logger.info("[retrieve] question: %s", state["question"])
    query_embedding = embed_text(state["question"])
    chunks = search_similar_chunks(
        query_embedding=query_embedding,
        video_id=state.get("video_id"),
        limit=5,
    )
    logger.info("[retrieve] found %d chunks", len(chunks))
    return {"context": chunks}


_GENERATE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful assistant that answers questions based on a YouTube video transcript.

Rules:
- Answer strictly from the provided transcript segments.
- If the context is insufficient, say so — never invent facts.
- Cite segments using [Segment X] notation where helpful.
- Be concise but complete.""",
    ),
    (
        "human",
        "Transcript segments:\n{context}\n\nQuestion: {question}",
    ),
])

def generate(state: RAGState) -> dict:
    logger.info("[generate] generating answer")
    if not state["context"]:
        return {
            "answer": "I couldn't find relevant information in the transcript to answer your question."
        }

    context_str = "\n\n".join(
        f"[Segment {i + 1}]\n{c['content']}"
        for i, c in enumerate(state["context"])
    )
    llm   = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
    chain = _GENERATE_PROMPT | llm | StrOutputParser()
    answer = chain.invoke({"context": context_str, "question": state["question"]})
    logger.info("[generate] done")
    return {"answer": answer}



def build_rag_graph():
    builder = StateGraph(RAGState)

    builder.add_node("retrieve", retrieve)
    builder.add_node("generate", generate)

    builder.add_edge(START,      "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


def query_video(
    question: str,
    video_id: Optional[str] = None,
) -> QueryResult:
    graph  = build_rag_graph()
    result = graph.invoke({
        "question": question,
        "video_id": video_id,
        "context":  [],
        "answer":   "",
    })

    sources = [
        SourceReference(
            content=c["content"],
            chunk_index=c["chunk_index"],
            video_id=c["video_id"],
            relevance_score=c.get("distance", 0.0),
        )
        for c in result["context"]
    ]

    return QueryResult(
        answer=result["answer"],
        sources=sources,
        query=question,
    )