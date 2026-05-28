"""
LangGraph race analyst agent.

Graph:
  START → classify_query → [retrieve_docs | query_db | hybrid] → generate → END

Query types:
  - "semantic": narrative questions → ChromaDB only
  - "structured": numerical/stats questions → TimescaleDB only  
  - "hybrid": questions needing both → both tools, merged context
"""
import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query_type: str
    retrieved_docs: List[str]
    db_results: List[dict]
    context: str


def classify_query(state: AgentState) -> AgentState:
    """
    Classify query to determine which tools to use.
    Numerical/stats → structured (DB)
    Why/explain/describe → semantic (ChromaDB)
    Both signals → hybrid
    """
    query = state["messages"][-1].content.lower()

    numerical_signals = [
        "lap", "speed", "time", "fastest", "average", "top speed",
        "sector", "gap", "position", "points", "how many", "what number",
        "how fast", "how long", "duration", "seconds", "km/h"
    ]
    narrative_signals = [
        "why", "how did", "explain", "describe", "what happened",
        "tell me about", "strategy", "reason", "because", "cause"
    ]

    has_numerical = any(s in query for s in numerical_signals)
    has_narrative = any(s in query for s in narrative_signals)

    if has_numerical and has_narrative:
        state["query_type"] = "hybrid"
    elif has_numerical:
        state["query_type"] = "structured"
    else:
        state["query_type"] = "semantic"

    return state


def retrieve_docs(state: AgentState) -> AgentState:
    """Retrieve from ChromaDB using hybrid BM25 + vector search."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        from rank_bm25 import BM25Okapi
        from pathlib import Path

        CHROMA_DIR = Path("/app/modules/genai_rag/data/chroma")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name="f1_knowledge", embedding_function=ef)

        query = state["messages"][-1].content

        # Vector search
        results = collection.query(query_texts=[query], n_results=5)
        docs = results["documents"][0]
        metas = results["metadatas"][0]

        # BM25 on full corpus
        all_docs = collection.get(include=["documents", "metadatas"])
        corpus = all_docs["documents"]
        tokenized = [d.lower().split() for d in corpus]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
        top_bm25_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
        bm25_docs = [corpus[i] for i in top_bm25_idx if scores[i] > 0]

        # Merge — vector first, then BM25 additions
        all_retrieved = docs + [d for d in bm25_docs if d not in docs]

        state["retrieved_docs"] = all_retrieved[:6]
    except Exception as e:
        state["retrieved_docs"] = [f"Retrieval error: {str(e)}"]

    return state


def query_db(state: AgentState) -> AgentState:
    """Query TimescaleDB for numerical telemetry and lap data."""
    try:
        import os
        from sqlalchemy import create_engine, text

        engine = create_engine(
            os.getenv("DATABASE_URL", "postgresql://pitwall:pitwall_secret@timescaledb:5432/pitwall")
        )

        query = state["messages"][-1].content.lower()
        results = []

        # Detect which session to query
        session_key = 9158  # default Bahrain race
        if "jeddah" in query or "saudi" in query:
            session_key = 9159
        elif "australia" in query or "melbourne" in query:
            session_key = 9160
        elif "qualifying" in query or "quali" in query:
            session_key = 9157

        with engine.connect() as conn:
            # Telemetry stats
            if any(w in query for w in ["speed", "fast", "top speed", "average speed"]):
                rows = conn.execute(text("""
                    SELECT driver_number,
                           ROUND(AVG(speed)::numeric, 1) as avg_speed,
                           MAX(speed) as top_speed
                    FROM telemetry
                    WHERE session_key = :key
                    GROUP BY driver_number
                    ORDER BY top_speed DESC
                    LIMIT 5
                """), {"key": session_key}).mappings().all()
                results.extend([dict(r) for r in rows])

            # Lap times
            if any(w in query for w in ["lap time", "fastest lap", "sector", "lap"]):
                rows = conn.execute(text("""
                    SELECT driver_number,
                           lap_number,
                           ROUND(lap_duration::numeric, 3) as lap_time,
                           compound,
                           tyre_age_laps
                    FROM laps
                    WHERE session_key = :key
                    AND lap_duration IS NOT NULL
                    ORDER BY lap_duration ASC
                    LIMIT 10
                """), {"key": session_key}).mappings().all()
                results.extend([dict(r) for r in rows])

        state["db_results"] = results
    except Exception as e:
        state["db_results"] = [{"error": str(e)}]

    return state


def generate_answer(state: AgentState) -> AgentState:
    """Generate grounded answer using Groq with all retrieved context."""
    from groq import Groq

    context_parts = []

    if state.get("retrieved_docs"):
        context_parts.append("KNOWLEDGE BASE:\n" + "\n---\n".join(state["retrieved_docs"][:4]))

    if state.get("db_results"):
        context_parts.append("LIVE DATABASE RESULTS:\n" + str(state["db_results"]))

    context = "\n\n".join(context_parts) if context_parts else "No context available."

    query_type_note = {
        "semantic": "narrative/contextual question",
        "structured": "numerical/statistical question",
        "hybrid": "question requiring both context and data",
    }.get(state.get("query_type", "semantic"), "")

    prompt = f"""You are an expert F1 race analyst. This is a {query_type_note}.
Answer using ONLY the provided context and database results.
Be specific — cite driver names, lap numbers, and times where available.
If information is missing, say so clearly rather than guessing.

{context}

Question: {state["messages"][-1].content}

Answer:"""

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
    )

    answer = response.choices[0].message.content
    state["messages"] = [AIMessage(content=answer)]
    return state


def route_after_classify(state: AgentState) -> str:
    qt = state.get("query_type", "semantic")
    if qt == "structured":
        return "query_db"
    elif qt == "hybrid":
        return "retrieve_docs"
    return "retrieve_docs"


def route_after_retrieve(state: AgentState) -> str:
    """After doc retrieval, also query DB if hybrid."""
    if state.get("query_type") == "hybrid":
        return "query_db"
    return "generate"


def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("classify_query", classify_query)
    graph.add_node("retrieve_docs", retrieve_docs)
    graph.add_node("query_db", query_db)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge(START, "classify_query")
    graph.add_conditional_edges("classify_query", route_after_classify, {
        "retrieve_docs": "retrieve_docs",
        "query_db": "query_db",
    })
    graph.add_conditional_edges("retrieve_docs", route_after_retrieve, {
        "query_db": "query_db",
        "generate": "generate_answer",
    })
    graph.add_edge("query_db", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()