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


# ── Models ──────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
CHROMA_DIR = str(Path(__file__).parent / "chroma_db")

vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name="onet_career_data"
)


# ── System prompt ────────────────────────────────────────────────────────────
BASE_SYSTEM_PROMPT = """You are a career counselor at LaGuardia Community College helping adult students (25-55) explore career changes.

RESPONSE RULES — follow strictly:
- Be SHORT. Max 3-4 sentences per response during intake. No walls of text.
- One idea at a time. Don't dump all information at once.
- End every message with ONE simple question — never multiple.
- When suggesting a career, give just the name + one sentence on why it fits them. Save details for when they ask.
- Use bullet points or bold ONLY when presenting a list of career options or comparing options. Never for regular conversation.
- Never repeat what the user just said back to them.
- Respond in English.

FLOW:
1. First exchange: understand their situation with a short empathetic response + one follow-up question.
2. After 2 exchanges: suggest 2-3 career options briefly (name + one-line reason each).
3. Only go deep on a career when the user explicitly asks for more details.
"""


# ── Helpers ──────────────────────────────────────────────────────────────────
def _search_careers(query: str, k: int = 3) -> str:
    """Search ChromaDB and format results as context."""
    if not query.strip():
        return ""
    try:
        results = vectorstore.similarity_search(query, k=k)
    except Exception:
        return ""
    if not results:
        return ""

    context = "\n\n[Career programs available at LaGuardia that may be relevant:]\n"
    for r in results:
        title = r.metadata.get("title", "Career Program")
        context += f"\n• {title}: {r.page_content[:400]}\n"
    context += "\n[Use this information to make personalized suggestions in your response.]\n"
    return context


def _build_query(messages: List[BaseMessage], cv_data: str) -> str:
    """Build a search query from recent conversation + CV."""
    recent = [
        m.content for m in messages[-6:]
        if isinstance(m.content, str)
    ]
    parts = recent + ([cv_data[:500]] if cv_data else [])
    return " ".join(parts)


def _last_user_message(messages: List[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage) and isinstance(m.content, str):
            return m.content
    return ""


# ── Nodes ────────────────────────────────────────────────────────────────────
WELCOME_MESSAGE = (
    "Thanks for connecting today. To start, what made you decide to explore "
    "new career options at this moment?"
)

def intake_node(state: CounselorState):
    """Main conversation node. Suggests careers proactively based on context."""
    messages = state["messages"]
    cv_data = state.get("cv_data", "")

    # Return welcome message if no messages yet (e.g. Studio cold start)
    if not messages:
        return {"messages": [AIMessage(content=WELCOME_MESSAGE)], "phase": "intake"}

    # Build career context from ChromaDB
    query = _build_query(messages, cv_data)
    career_context = _search_careers(query, k=3)

    # Add CV context if present
    cv_context = ""
    if cv_data:
        cv_context = f"\n\n[The user has uploaded their CV. Key content:\n{cv_data[:800]}\nUse this to personalize your responses.]\n"

    system = BASE_SYSTEM_PROMPT + cv_context + career_context

    response = llm.invoke(
        [{"role": "system", "content": system}] + messages[-20:]
    )
    return {"messages": [response], "phase": "intake"}


def detail_node(state: CounselorState):
    """Provides in-depth information about a specific career the user asked about."""
    messages = state["messages"]
    cv_data = state.get("cv_data", "")

    last_msg = _last_user_message(messages)

    # Search for the specific career they mentioned
    results = vectorstore.similarity_search(last_msg, k=1)
    detail_context = ""
    if results:
        r = results[0]
        title = r.metadata.get("title", "Career")
        detail_context = (
            f"\n\n[Detailed information about '{title}':\n{r.page_content}\n"
            "Use ALL of this detail to answer the user's question thoroughly. "
            "Cover: day-to-day tasks, required skills, education pathway, salary range if available, "
            "and how their background makes them a good fit.]\n"
        )

    cv_context = ""
    if cv_data:
        cv_context = f"\n\n[User's CV:\n{cv_data[:800]}\n]\n"

    system = BASE_SYSTEM_PROMPT + cv_context + detail_context

    response = llm.invoke(
        [{"role": "system", "content": system}] + messages[-20:]
    )
    return {"messages": [response], "phase": "detail"}


# ── Router ───────────────────────────────────────────────────────────────────
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
workflow.add_node("intake", intake_node)
workflow.add_node("detail", detail_node)

workflow.add_conditional_edges(
    START,
    route_message,
    {"intake": "intake", "detail": "detail"}
)
workflow.add_edge("intake", END)
workflow.add_edge("detail", END)

app = workflow.compile()
