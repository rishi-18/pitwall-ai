# genai_rag/ — GenAI / RAG Module

## What it does

Natural language interface over F1 knowledge using:
- LangChain
- LangGraph
- ChromaDB
- Groq LLMs

## Architecture

User Query
    +--? LangGraph Agent
              +-- ChromaDB Retriever
              +-- TimescaleDB Query Tool
              +-- Groq LLM

## Key files

- src/pipeline/retriever.py
- src/agents/race_analyst.py
- src/agents/tools.py
- src/ingest/scraper.py
- src/ingest/doc_processor.py
