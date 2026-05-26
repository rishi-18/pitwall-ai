"""
Hybrid BM25 + vector retriever for F1 race knowledge.
"""

import os

from langchain_chroma import Chroma

from langchain_community.retrievers import (
    BM25Retriever
)

from langchain.retrievers import (
    EnsembleRetriever
)

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

CHROMA_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    "/tmp/chroma"
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TOP_K = 6


def build_hybrid_retriever(
    documents: list
) -> EnsembleRetriever:

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    vectorstore = Chroma(
        collection_name="f1_knowledge",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    vector_retriever = vectorstore.as_retriever(
        search_kwargs={"k": TOP_K}
    )

    bm25_retriever = BM25Retriever.from_documents(
        documents,
        k=TOP_K
    )

    return EnsembleRetriever(
        retrievers=[
            bm25_retriever,
            vector_retriever
        ],
        weights=[0.4, 0.6],
    )
