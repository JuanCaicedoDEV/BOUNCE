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
    university_id: str  # tenant identifier


# ── Models ───────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
CHROMA_DIR = str(Path(__file__).parent / "chroma_db")

# Legacy O*NET collection (fallback)
_onet_vs = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name="onet_career_data",
)

# University programs collection (multi-tenant, filtered by university_id)
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
- Never repeat what the user just said back to them.
- Respond in English.

FLOW:
1. First exchange: short empathetic response + one follow-up question.
2. After 2 exchanges: suggest 2-3 programs briefly (name + one-line reason each).
3. Only go deep on a program when the user explicitly asks for more details.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _search_programs(query: str, university_id: str, k: int = 3) -> str:
    """Search the university's uploaded programs first, fall back to O*NET."""
    if not query.strip():
        return ""

    context = ""

    # 1. University-specific programs (uploaded PDFs)
    try:
        results = _programs_vs.similarity_search(
            query,
            k=k,
            filter={"university_id": university_id},
        )
        if results:
            context += "\n\n[Programs offered by this institution:]\n"
            for r in results:
                name = r.metadata.get("program_name", "Program")
                context += f"\n• **{name}**: {r.page_content[:350]}\n"
            context += "\n[Prioritize suggesting these specific programs.]\n"
    except Exception:
        pass

    # 2. Fall back to O*NET general career data if no university programs found
    if not context:
        try:
            results = _onet_vs.similarity_search(query, k=k)
            if results:
                context += "\n\n[Relevant career paths:]\n"
                for r in results:
                    title = r.metadata.get("title", "Career")
                    context += f"\n• **{title}**: {r.page_content[:350]}\n"
        except Exception:
            pass

    return context


def _build_query(messages: List[BaseMessage], cv_data: str) -> str:
    recent = [m.content for m in messages[-6:] if isinstance(m.content, str)]
    parts = recent + ([cv_data[:500]] if cv_data else [])
    return " ".join(parts)


def _last_user_message(messages: List[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage) and isinstance(m.content, str):
            return m.content
    return ""


# ── Nodes ─────────────────────────────────────────────────────────────────────
WELCOME_MESSAGE = (
    "Thanks for connecting today. To start, what made you decide to explore "
    "new career options at this moment?"
)


def intake_node(state: CounselorState):
    messages = state["messages"]
    cv_data = state.get("cv_data", "")
    university_id = state.get("university_id", "laguardia")

    if not messages:
        return {"messages": [AIMessage(content=WELCOME_MESSAGE)], "phase": "intake"}

    query = _build_query(messages, cv_data)
    career_context = _search_programs(query, university_id, k=3)

    cv_context = ""
    if cv_data:
        cv_context = (
            f"\n\n[User's CV:\n{cv_data[:800]}\n"
            "Reference specific skills or experience from it.]\n"
        )

    system = BASE_SYSTEM_PROMPT + cv_context + career_context

    response = llm.invoke(
        [{"role": "system", "content": system}] + messages[-20:]
    )
    return {"messages": [response], "phase": "intake"}


def detail_node(state: CounselorState):
    messages = state["messages"]
    cv_data = state.get("cv_data", "")
    university_id = state.get("university_id", "laguardia")

    last_msg = _last_user_message(messages)

    # Deep search for this specific program
    detail_context = ""
    try:
        results = _programs_vs.similarity_search(
            last_msg, k=1, filter={"university_id": university_id}
        )
        if results:
            r = results[0]
            name = r.metadata.get("program_name", "Program")
            detail_context = (
                f"\n\n[Full details for '{name}':\n{r.page_content}\n"
                "Cover thoroughly: what students learn, requirements, career outcomes, "
                "duration, and why it fits this person.]\n"
            )
    except Exception:
        pass

    # Fall back to O*NET
    if not detail_context:
        try:
            results = _onet_vs.similarity_search(last_msg, k=1)
            if results:
                r = results[0]
                title = r.metadata.get("title", "Career")
                detail_context = (
                    f"\n\n[Details about '{title}':\n{r.page_content}\n"
                    "Cover: day-to-day tasks, skills, education pathway, salary.]\n"
                )
        except Exception:
            pass

    cv_context = f"\n\n[User's CV:\n{cv_data[:800]}\n]\n" if cv_data else ""
    system = BASE_SYSTEM_PROMPT + cv_context + detail_context

    response = llm.invoke(
        [{"role": "system", "content": system}] + messages[-20:]
    )
    return {"messages": [response], "phase": "detail"}


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


# ── Graph ──────────────────────────────────────────────────────────────────────
workflow = StateGraph(CounselorState)
workflow.add_node("intake", intake_node)
workflow.add_node("detail", detail_node)

workflow.add_conditional_edges(
    START,
    route_message,
    {"intake": "intake", "detail": "detail"},
)
workflow.add_edge("intake", END)
workflow.add_edge("detail", END)

app = workflow.compile()
