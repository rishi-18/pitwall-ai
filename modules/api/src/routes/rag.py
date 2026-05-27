"""
RAG router - hybrid BM25 + vector retrieval with Groq streaming.

Retrieval strategy:
1. Vector search (ChromaDB) - semantic similarity
2. BM25 search - keyword matching for names, numbers, F1 terms
3. Reciprocal Rank Fusion - merges both ranked lists
4. Summary chunks - always included for baseline context
5. Groq Llama 3 - generates grounded streaming answer
"""
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import math

router = APIRouter()
CHROMA_DIR = Path("/app/modules/genai_rag/data/chroma")

# Cache retrievers after first load
_collection = None
_bm25 = None
_corpus = None
_corpus_metadata = None


def get_collection():
    global _collection
    if _collection is None:
        import chromadb
        from chromadb.utils import embedding_functions
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(
            name="f1_knowledge",
            embedding_function=ef
        )
    return _collection


def get_corpus():
    """Load all documents from ChromaDB for BM25 indexing."""
    global _corpus, _corpus_metadata
    if _corpus is None:
        collection = get_collection()
        result = collection.get(include=["documents", "metadatas"])
        _corpus = result["documents"]
        _corpus_metadata = result["metadatas"]
    return _corpus, _corpus_metadata


def get_bm25():
    """Build BM25 index from ChromaDB corpus."""
    global _bm25
    if _bm25 is None:
        from rank_bm25 import BM25Okapi
        corpus, _ = get_corpus()
        tokenized = [doc.lower().split() for doc in corpus]
        _bm25 = BM25Okapi(tokenized)
    return _bm25


def reciprocal_rank_fusion(vector_ids: list, bm25_ids: list, k: int = 60) -> list:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.
    RRF score = sum(1 / (k + rank)) for each list.
    k=60 is the standard constant that prevents high ranks from dominating.
    """
    scores = {}
    for rank, doc_id in enumerate(vector_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    for rank, doc_id in enumerate(bm25_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)


def hybrid_retrieve(query: str, n_results: int = 5) -> list[dict]:
    """
    Hybrid retrieval: vector search + BM25 + always include summaries.
    Returns list of {text, metadata, chunk_type} dicts.
    """
    collection = get_collection()
    corpus, corpus_metadata = get_corpus()
    bm25 = get_bm25()

    # --- Vector search ---
    # --- Vector search --- (no filter - search all chunk types)
    vector_results = collection.query(
        query_texts=[query],
        n_results=min(n_results * 2, len(corpus)),
    )
    vector_docs = vector_results["documents"][0]
    vector_metas = vector_results["metadatas"][0]
    vector_ids = list(range(len(vector_docs)))

    # --- BM25 search (fact chunks only) ---
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # Get top BM25 results from fact chunks only
    fact_indices = [i for i, m in enumerate(corpus_metadata)
                    if m.get("chunk_type") == "fact"]
    fact_scores = [(i, bm25_scores[i]) for i in fact_indices]
    # BM25 over all chunks
    all_scores = [(i, bm25_scores[i]) for i in range(len(corpus))]
    all_scores.sort(key=lambda x: x[1], reverse=True)
    bm25_top = [i for i, score in all_scores[:n_results * 2] if score > 0]

    # --- RRF merge ---
    merged = reciprocal_rank_fusion(vector_ids, bm25_top)
    top_indices = merged[:n_results]

    # Build results
    retrieved = []

    # Always include summary chunks first
    for i, meta in enumerate(corpus_metadata):
        if meta.get("chunk_type") == "summary":
            retrieved.append({
                "text": corpus[i],
                "metadata": meta,
                "chunk_type": "summary",
            })

    # Add RRF-ranked results
    for idx in top_indices:
        if idx < len(corpus):
            meta = corpus_metadata[idx]
            if meta.get("chunk_type") != "summary":  # avoid duplicates
                retrieved.append({
                    "text": corpus[idx],
                    "metadata": meta,
                    "chunk_type": meta.get("chunk_type", "unknown"),
                })

    return retrieved[:n_results + len([m for m in corpus_metadata if m.get("chunk_type") == "summary"])]


class RAGQuery(BaseModel):
    question: str
    session_key: int | None = None


@router.post("/query")
async def query_race_analyst(payload: RAGQuery):
    """
    Stream a grounded answer using hybrid BM25 + vector retrieval.
    """
    async def event_stream():
        try:
            chunks = hybrid_retrieve(payload.question, n_results=5)

            # Build context with chunk type labels
            context_parts = []
            for chunk in chunks:
                meta = chunk["metadata"]
                race = meta.get("race", "unknown")
                section = meta.get("section", "")
                ctype = chunk["chunk_type"]
                label = f"[{race} | {ctype} | {section}]"
                context_parts.append(f"{label}\n{chunk['text']}")

            context = "\n\n---\n\n".join(context_parts)

            prompt = f"""You are an expert F1 race analyst with access to telemetry data, race results, and strategy information.

Answer the question using ONLY the provided context. Be specific — cite driver names, lap numbers, and times where available.
If the context doesn't contain enough information to answer precisely, say so.

Context:
{context}

Question: {payload.question}

Answer:"""

            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))

            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=600,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {delta}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/status")
async def rag_status():
    """RAG pipeline status with chunk breakdown."""
    try:
        collection = get_collection()
        corpus, corpus_metadata = get_corpus()
        return {
            "status": "ok",
            "total_chunks": collection.count(),
            "chunk_types": {
                "summary": sum(1 for m in corpus_metadata if m.get("chunk_type") == "summary"),
                "window": sum(1 for m in corpus_metadata if m.get("chunk_type") == "window"),
                "fact": sum(1 for m in corpus_metadata if m.get("chunk_type") == "fact"),
            },
            "retrieval_strategy": "hybrid_bm25_vector_rrf",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}