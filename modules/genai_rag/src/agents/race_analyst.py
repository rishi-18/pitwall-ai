"""
LangGraph race analyst agent.
"""

import os

from typing import (
    TypedDict,
    Annotated,
    List,
)

from langchain_groq import ChatGroq

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
)

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.graph.message import (
    add_messages
)

GROQ_MODEL = "llama-3.1-70b-versatile"


class AgentState(TypedDict):

    messages: Annotated[
        List[BaseMessage],
        add_messages
    ]

    retrieved_docs: List[str]

    db_results: List[dict]

    query_type: str


def build_race_analyst_agent(
    retriever,
    db_query_fn
):

    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        streaming=True,
    )

    def route_query(
        state: AgentState
    ) -> AgentState:

        query = (
            state["messages"][-1]
            .content
            .lower()
        )

        has_numbers = any(
            w in query
            for w in [
                "lap time",
                "gap",
                "speed",
                "sector",
                "pace"
            ]
        )

        has_narrative = any(
            w in query
            for w in [
                "why",
                "what happened",
                "explain",
                "describe"
            ]
        )

        if has_numbers and has_narrative:
            state["query_type"] = "hybrid"

        elif has_numbers:
            state["query_type"] = "structured"

        else:
            state["query_type"] = "semantic"

        return state

    def retrieve_docs(
        state: AgentState
    ) -> AgentState:

        query = state["messages"][-1].content

        docs = retriever.invoke(query)

        state["retrieved_docs"] = [
            d.page_content
            for d in docs
        ]

        return state

    def query_db(
        state: AgentState
    ) -> AgentState:

        query = state["messages"][-1].content

        results = db_query_fn(query)

        state["db_results"] = results

        return state

    def generate_answer(
        state: AgentState
    ) -> AgentState:

        context_parts = []

        if state.get("retrieved_docs"):

            context_parts.append(
                "DOCUMENTS:\n"
                + "\n---\n".join(
                    state["retrieved_docs"]
                )
            )

        if state.get("db_results"):

            context_parts.append(
                "DATA:\n"
                + str(state["db_results"])
            )

        context = "\n\n".join(
            context_parts
        )

        prompt = f"""
You are an expert F1 race analyst.

Answer only using provided context.

Context:
{context}

Question:
{state["messages"][-1].content}
"""

        response = llm.invoke([
            HumanMessage(content=prompt)
        ])

        state["messages"] = [
            AIMessage(
                content=response.content
            )
        ]

        return state

    def router(
        state: AgentState
    ) -> str:

        qt = state.get(
            "query_type",
            "semantic"
        )

        if qt == "structured":
            return "query_db"

        elif qt == "hybrid":
            return "retrieve_docs"

        return "retrieve_docs"

    graph = StateGraph(AgentState)

    graph.add_node(
        "route_query",
        route_query
    )

    graph.add_node(
        "retrieve_docs",
        retrieve_docs
    )

    graph.add_node(
        "query_db",
        query_db
    )

    graph.add_node(
        "generate_answer",
        generate_answer
    )

    graph.add_edge(
        START,
        "route_query"
    )

    graph.add_conditional_edges(
        "route_query",
        router,
        {
            "retrieve_docs": "retrieve_docs",
            "query_db": "query_db",
        }
    )

    graph.add_edge(
        "retrieve_docs",
        "generate_answer"
    )

    graph.add_edge(
        "query_db",
        "generate_answer"
    )

    graph.add_edge(
        "generate_answer",
        END
    )

    return graph.compile()
