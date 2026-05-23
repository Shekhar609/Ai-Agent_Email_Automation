"""Tools available to agents.

`kb_search` is real (Chroma-backed). Others are stubs returning marker strings,
to be wired to real providers in later phases.
"""
import asyncio

from langchain_core.tools import tool

from app.vectorstore import chroma_client


@tool
async def kb_search(query: str, user_id: str, n_results: int = 3) -> list[dict]:
    """Search the user's email knowledge base for semantically similar past emails.

    Args:
        query: text to search for
        user_id: the user's UUID as a string (scopes results to that user)
        n_results: how many results to return (default 3)
    """
    results = await asyncio.to_thread(
        chroma_client.search, user_id=user_id, query=query, n_results=n_results
    )
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    return [{"text": d, **(m or {})} for d, m in zip(docs, metas)]


@tool
async def web_search(query: str) -> str:
    """Web search. STUB until phase 4 wires a real provider."""
    return f"[stub] web_search would query: {query}"


@tool
async def calendar_lookup(participant_email: str, days_ahead: int = 14) -> str:
    """Look up availability for a participant. STUB until Google Calendar wired in phase 4."""
    return f"[stub] availability for {participant_email} over next {days_ahead} days"


@tool
async def crm_lookup(email: str) -> dict:
    """Look up customer info in CRM. STUB."""
    return {"email": email, "tier": "unknown", "notes": "(stub — wire real CRM in phase 4)"}


ALL_TOOLS = [kb_search, web_search, calendar_lookup, crm_lookup]
