import sys
sys.path.insert(0, '.')
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

CHROMA_DIR = Path("modules/genai_rag/data/chroma")

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_collection(name="f1_knowledge", embedding_function=ef)

print(f"Total chunks: {collection.count()}")
print()

# Check what's actually in the collection
all_docs = collection.get(include=["documents", "metadatas"])
print("Sample chunks:")
for doc, meta in zip(all_docs["documents"][:5], all_docs["metadatas"][:5]):
    print(f"  [{meta.get('chunk_type')} | {meta.get('race')} | {meta.get('section')}]")
    print(f"  {doc[:150]}")
    print()

# Test retrieval directly
print("=" * 60)
print("Query: What lap did Verstappen pit in Bahrain?")
results = collection.query(
    query_texts=["What lap did Verstappen pit in Bahrain?"],
    n_results=5,
)
print("Top retrieved chunks:")
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"  [{meta.get('chunk_type')} | {meta.get('race')} | {meta.get('section')}]")
    print(f"  {doc[:200]}")
    print()