"""
Document processor - chunks scraped documents and loads into ChromaDB.
Chunking strategy: section-based (not fixed-size) for race reports.
Each section becomes one chunk - preserves narrative coherence.
"""
import json
import structlog
from pathlib import Path

log = structlog.get_logger()
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"


def load_documents() -> list[dict]:
    """Load scraped race reports."""
    path = DATA_DIR / "race_reports.json"
    if not path.exists():
        raise FileNotFoundError(f"No documents found at {path}. Run scraper first.")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def chunk_documents(documents: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Convert documents into chunks for embedding.
    Strategy: one chunk per section - preserves context better than fixed-size splits.
    """
    texts = []
    metadatas = []

    for doc in documents:
        for section_name, section_text in doc.get("sections", {}).items():
            if len(section_text) < 100:
                continue
            # Prepend title and section for retrieval context
            chunk = f"{doc['title']} - {section_name}\n\n{section_text}"
            texts.append(chunk)
            metadatas.append({
                "source": doc["source"],
                "title": doc["title"],
                "slug": doc["slug"],
                "section": section_name,
                "url": doc["url"],
            })

    log.info("chunks_created", total=len(texts))
    return texts, metadatas


def load_into_chromadb(texts: list[str], metadatas: list[dict]) -> int:
    """Embed chunks and store in ChromaDB."""
    import chromadb
    from chromadb.utils import embedding_functions

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name="f1_knowledge",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Insert in batches
    batch_size = 50
    inserted = 0
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]
        batch_ids = [f"doc_{i + j}" for j in range(len(batch_texts))]
        collection.upsert(
            documents=batch_texts,
            metadatas=batch_metas,
            ids=batch_ids,
        )
        inserted += len(batch_texts)
        log.info("batch_inserted", inserted=inserted, total=len(texts))

    return inserted


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    texts, metadatas = chunk_documents(docs)
    print(f"Created {len(texts)} chunks")
    print("Loading into ChromaDB...")
    inserted = load_into_chromadb(texts, metadatas)
    print(f"Inserted {inserted} chunks into ChromaDB")