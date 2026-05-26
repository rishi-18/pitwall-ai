"""RAG router - GenAI race analyst with streaming responses."""
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class RAGQuery(BaseModel):
    question: str
    session_key: int | None = None


def get_retriever():
    """Build ChromaDB retriever - cached after first call."""
    import chromadb
    from chromadb.utils import embedding_functions
    from pathlib import Path

    CHROMA_DIR = Path("/app/modules/genai_rag/data/chroma")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name="f1_knowledge", embedding_function=ef)
    return collection


@router.post("/query")
async def query_race_analyst(payload: RAGQuery):
    """
    Stream a grounded answer from the RAG pipeline.
    Retrieves relevant F1 documents then generates answer via Groq.
    Returns Server-Sent Events for token-by-token streaming.
    """
    async def event_stream():
        try:
            # Retrieve relevant chunks
            collection = get_retriever()
            results = collection.query(
                query_texts=[payload.question],
                n_results=3,
            )

            context_parts = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                source = meta.get('race', meta.get('slug', 'unknown'))
                section = meta.get('section', meta.get('type', ''))
                context_parts.append(f"[{source} - {section}]\n{doc}")

            context = "\n\n---\n\n".join(context_parts)

            prompt = f"""You are an expert F1 race analyst. Answer the question using only the provided context.
Be specific, cite driver names and lap numbers where available.
If the context doesn't contain enough information, say so clearly.

Context:
{context}

Question: {payload.question}

Answer:"""

            # Stream from Groq
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))

            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=500,
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
    """Check RAG pipeline status - chunk count and collection info."""
    try:
        collection = get_retriever()
        return {"status": "ok", "chunks": collection.count()}
    except Exception as e:
        return {"status": "error", "error": str(e)}