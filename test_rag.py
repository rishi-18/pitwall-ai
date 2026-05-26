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

print(f"Total chunks in ChromaDB: {collection.count()}")
print()

queries = [
    "Who won the Australian Grand Prix?",
    "What tyre strategy did Verstappen use in Bahrain?",
    "What happened to Verstappen in Australia?",
]

for query in queries:
    print(f"Q: {query}")
    results = collection.query(query_texts=[query], n_results=2)
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        print(f"  [{meta.get('race')} - {meta.get('section', meta.get('type'))}]")
        print(f"  {doc[:200]}")
    print()