from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")


class CounselorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    skills: List[str]
    identified_careers: List[dict]
    cv_data: str
    phase: str
    university_id: str
    retrieved_context: str   # shared context built by search nodes
    search_query: str        # reformulated query for retrieval


# ── Models ────────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
CHROMA_DIR = str(Path(__file__).parent / "chroma_db")

# Node A: O*NET general career database
_onet_vs = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name="onet_career_data",
)

# Node B: University-uploaded programs (multi-tenant)
_programs_vs = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name="university_programs",
)


# ── System prompt ─────────────────────────────────────────────────────────────
BASE_SYSTEM_PROMPT = """You are a career counselor helping adult students (25-55) explore career changes.

RESPONSE RULES — follow strictly:
- Be SHORT. Max 3-4 sentences per response during intake. No walls of text.
- One idea at a time. Don't dump all information at once.
- End every message with ONE simple question — never multiple.
- When suggesting a career/program, give just the name + one sentence on why it fits them.
- Use bullet points or bold ONLY when presenting a list of options. Never for regular conversation.
- Never repeat what the user said back to them.
- Respond in English.

FLOW:
1. First exchange: short empathetic response + one follow-up question.
2. After 2 exchanges: suggest 2-3 programs briefly (name + one-line reason each).
3. Only go deep on a program when the user explicitly asks for more details.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
QUERY_REFORM_PROMPT = """Extract a concise semantic search query (max 2 sentences) from this career counseling conversation.
Focus on: the person's background, skills, goals, and career interests.
Output ONLY the query text, nothing else."""

def query_reformulation_node(state: CounselorState) -> dict:
    """Reformulates the conversation into a focused semantic query for retrieval."""
    messages = state["messages"]
    cv_data = state.get("cv_data", "")

    if not messages:
        return {"search_query": "", "retrieved_context": ""}

    # Build a short summary of the conversation for the LLM
    convo = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Counselor'}: {m.content}"
        for m in messages[-8:]
        if isinstance(m.content, str)
    )
    if cv_data:
        convo += f"\n\nCV excerpt: {cv_data[:400]}"

    response = llm.invoke([
        {"role": "system", "content": QUERY_REFORM_PROMPT},
        {"role": "user", "content": convo},
    ])
    query = response.content if isinstance(response.content, str) else str(response.content)
    return {"search_query": query.strip(), "retrieved_context": ""}


def _build_query(messages: List[BaseMessage], cv_data: str) -> str:
    recent = [m.content for m in messages[-6:] if isinstance(m.content, str)]
    parts = recent + ([cv_data[:500]] if cv_data else [])
    return " ".join(parts)


def _last_user_message(messages: List[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage) and isinstance(m.content, str):
            return m.content
    return ""


# ── Search nodes (RAG) ────────────────────────────────────────────────────────
def onet_search_node(state: CounselorState) -> dict:
    """Searches the O*NET general career database."""
    query = state.get("search_query") or _build_query(state["messages"], state.get("cv_data", ""))

    if not query.strip():
        return {"retrieved_context": ""}

    try:
        results = _onet_vs.similarity_search(query, k=3)
    except Exception:
        return {"retrieved_context": ""}

    if not results:
        return {"retrieved_context": ""}

    context = "\n\n[General career paths (O*NET):]\n"
    for r in results:
        title = r.metadata.get("title", "Career")
        context += f"\n• **{title}**: {r.page_content[:350]}\n"
    return {"retrieved_context": context}


def programs_search_node(state: CounselorState) -> dict:
    """Searches the university's uploaded program PDFs."""
    university_id = state.get("university_id", "laguardia")
    query = state.get("search_query") or _build_query(state["messages"], state.get("cv_data", ""))

    if not query.strip():
        return {"retrieved_context": state.get("retrieved_context", "")}

    try:
        results = _programs_vs.similarity_search(
            query, k=3, filter={"university_id": university_id}
        )
    except Exception:
        return {"retrieved_context": state.get("retrieved_context", "")}

    if not results:
        return {"retrieved_context": state.get("retrieved_context", "")}

    # University programs take priority — prepend them
    context = "\n\n[Programs offered by this institution — prioritize these:]\n"
    for r in results:
        name = r.metadata.get("program_name", "Program")
        context += f"\n• **{name}**: {r.page_content[:350]}\n"

    # Append O*NET context if it exists
    existing = state.get("retrieved_context", "")
    return {"retrieved_context": context + existing}


# ── Counselor nodes ───────────────────────────────────────────────────────────
WELCOME_MESSAGE = (
    "Thanks for connecting today. To start, what made you decide to explore "
    "new career options at this moment?"
)


def intake_node(state: CounselorState) -> dict:
    """Main conversation node. Uses retrieved_context built by search nodes."""
    messages = state["messages"]
    cv_data = state.get("cv_data", "")
    retrieved_context = state.get("retrieved_context", "")

    if not messages:
        return {"messages": [AIMessage(content=WELCOME_MESSAGE)], "phase": "intake"}

    cv_context = (
        f"\n\n[User's CV:\n{cv_data[:800]}\nReference specific skills from it.]\n"
        if cv_data else ""
    )

    system = BASE_SYSTEM_PROMPT + cv_context + retrieved_context

    response = llm.invoke(
        [{"role": "system", "content": system}] + messages[-20:]
    )
    return {"messages": [response], "phase": "intake", "retrieved_context": ""}


def detail_node(state: CounselorState) -> dict:
    """Deep dive on a specific program/career. Uses retrieved_context from search nodes."""
    messages = state["messages"]
    cv_data = state.get("cv_data", "")
    retrieved_context = state.get("retrieved_context", "")

    cv_context = f"\n\n[User's CV:\n{cv_data[:800]}\n]\n" if cv_data else ""

    detail_instruction = (
        "\n[Answer thoroughly: what students learn, requirements, outcomes, "
        "duration, salary range if available, and why it fits this person.]\n"
    )

    system = BASE_SYSTEM_PROMPT + cv_context + retrieved_context + detail_instruction

    response = llm.invoke(
        [{"role": "system", "content": system}] + messages[-20:]
    )
    return {"messages": [response], "phase": "detail", "retrieved_context": ""}


# ── Router ────────────────────────────────────────────────────────────────────
DETAIL_TRIGGERS = [
    "tell me more", "more about", "more info", "more information",
    "details", "explain", "what is", "what does", "how do i",
    "requirements", "salary", "how much", "what would i do",
    "career path", "education", "degree", "certification",
    "day to day", "typical day", "responsibilities",
]


def route_message(state: CounselorState) -> str:
    last = _last_user_message(state["messages"]).lower()
    if any(kw in last for kw in DETAIL_TRIGGERS):
        return "detail"
    return "intake"


# ── Graph ─────────────────────────────────────────────────────────────────────
workflow = StateGraph(CounselorState)

workflow.add_node("query_reform", query_reformulation_node)
workflow.add_node("onet_search", onet_search_node)
workflow.add_node("programs_search", programs_search_node)
workflow.add_node("intake", intake_node)
workflow.add_node("detail", detail_node)

# START → query reformulation → O*NET → university programs → counselor
workflow.add_edge(START, "query_reform")
workflow.add_edge("query_reform", "onet_search")
workflow.add_edge("onet_search", "programs_search")
workflow.add_conditional_edges(
    "programs_search",
    route_message,
    {"intake": "intake", "detail": "detail"},
)
workflow.add_edge("intake", END)
workflow.add_edge("detail", END)

app = workflow.compile()
