"""
Document processor - hierarchical chunking strategy.

Three chunk types:
1. Summary chunks - one per document, always retrieved
2. Sliding window chunks - 400 token windows with 80 token overlap
3. Fact chunks - atomic sentences for BM25 keyword retrieval

This gives the RAG pipeline both semantic depth and keyword precision.
"""
import json
import re
import structlog
from pathlib import Path

log = structlog.get_logger()
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"

# Chunking parameters
CHUNK_SIZE = 400        # tokens (approx 300 words)
CHUNK_OVERLAP = 80      # tokens overlap between consecutive chunks
MIN_CHUNK_SIZE = 50     # discard chunks smaller than this


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return len(text) // 4


def sliding_window_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks by sentence boundaries.
    Overlap preserves context across chunk boundaries.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return []

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = estimate_tokens(sentence)

        if current_size + sentence_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(' '.join(current_chunk))

            # Keep last N tokens worth of sentences for overlap
            overlap_chunk = []
            overlap_size = 0
            for s in reversed(current_chunk):
                if overlap_size + estimate_tokens(s) <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_size += estimate_tokens(s)
                else:
                    break
            current_chunk = overlap_chunk
            current_size = overlap_size

        current_chunk.append(sentence)
        current_size += sentence_size

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return [c for c in chunks if estimate_tokens(c) >= MIN_CHUNK_SIZE]


def extract_facts(text: str) -> list[str]:
    """
    Extract atomic fact sentences for BM25 keyword retrieval.
    Targets sentences with numbers, names, or specific events.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    facts = []
    for s in sentences:
        s = s.strip()
        # Include sentences with numbers, driver names, or key F1 terms
        has_number = bool(re.search(r'\d+', s))
        has_f1_term = any(term in s.lower() for term in [
            'pit', 'lap', 'tyre', 'tire', 'verstappen', 'leclerc',
            'hamilton', 'sainz', 'norris', 'perez', 'fastest',
            'safety car', 'retired', 'dnf', 'pole', 'strategy',
            'soft', 'medium', 'hard', 'compound', 'sector',
        ])
        if (has_number or has_f1_term) and len(s) > 30:
            facts.append(s)
    return facts


def load_documents() -> list[dict]:
    path = DATA_DIR / "race_reports.json"
    if not path.exists():
        raise FileNotFoundError(f"No documents at {path}. Run scraper first.")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_chunks(documents: list[dict]) -> tuple[list[str], list[dict], list[str]]:
    """
    Build three types of chunks from documents.
    Returns: (texts, metadatas, ids)
    """
    texts = []
    metadatas = []
    ids = []
    chunk_idx = 0

    for doc in documents:
        slug = doc.get('slug', 'unknown')
        title = doc.get('title', '')
        sections = doc.get('sections', {})

        # Full document text
        full_text = ' '.join(sections.values())

        # --- Type 1: Summary chunk (always retrieved) ---
        summary = sections.get('summary', sections.get('race_result', ''))
        if summary and len(summary) > 50:
            texts.append(f"SUMMARY: {title}\n{summary}")
            metadatas.append({
                "race": slug, "title": title,
                "chunk_type": "summary", "section": "summary",
            })
            ids.append(f"{slug}_summary")

        # --- Type 2: Sliding window chunks per section ---
        for section_name, section_text in sections.items():
            if len(section_text) < 100:
                continue
            # Prepend title + section for retrieval context
            prefixed = f"{title} - {section_name}:\n{section_text}"
            window_chunks = sliding_window_chunks(prefixed)

            for i, chunk in enumerate(window_chunks):
                texts.append(chunk)
                metadatas.append({
                    "race": slug, "title": title,
                    "chunk_type": "window",
                    "section": section_name,
                    "chunk_index": i,
                })
                ids.append(f"{slug}_{section_name}_w{i}_{chunk_idx}")
                chunk_idx += 1

        # --- Type 3: Fact chunks for BM25 ---
        facts = extract_facts(full_text)
        for i, fact in enumerate(facts):
            fact_with_context = f"{title}: {fact}"
            texts.append(fact_with_context)
            metadatas.append({
                "race": slug, "title": title,
                "chunk_type": "fact",
                "section": "facts",
            })
            ids.append(f"{slug}_fact_{i}_{chunk_idx}")
            chunk_idx += 1

    log.info("chunks_built",
             total=len(texts),
             summaries=sum(1 for m in metadatas if m['chunk_type'] == 'summary'),
             windows=sum(1 for m in metadatas if m['chunk_type'] == 'window'),
             facts=sum(1 for m in metadatas if m['chunk_type'] == 'fact'))

    return texts, metadatas, ids


def load_into_chromadb(texts: list[str], metadatas: list[dict], ids: list[str]) -> int:
    """Embed chunks and store in ChromaDB."""
    import chromadb
    from chromadb.utils import embedding_functions

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete existing collection to rebuild clean
    try:
        client.delete_collection("f1_knowledge")
        log.info("existing_collection_deleted")
    except Exception:
        pass

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.create_collection(
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
        batch_ids = ids[i:i + batch_size]
        collection.upsert(
            documents=batch_texts,
            metadatas=batch_metas,
            ids=batch_ids,
        )
        inserted += len(batch_texts)

    log.info("chromadb_loaded", total=inserted)
    return inserted


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")

    texts, metadatas, ids = build_chunks(docs)
    print(f"\nChunk breakdown:")
    print(f"  Summary chunks: {sum(1 for m in metadatas if m['chunk_type'] == 'summary')}")
    print(f"  Window chunks:  {sum(1 for m in metadatas if m['chunk_type'] == 'window')}")
    print(f"  Fact chunks:    {sum(1 for m in metadatas if m['chunk_type'] == 'fact')}")
    print(f"  Total:          {len(texts)}")

    print("\nLoading into ChromaDB...")
    inserted = load_into_chromadb(texts, metadatas, ids)
    print(f"Inserted {inserted} chunks")