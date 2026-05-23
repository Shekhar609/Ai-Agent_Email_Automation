import asyncio

from app.agents.state import WorkflowState
from app.core.logging import get_logger
from app.vectorstore import chroma_client

logger = get_logger(__name__)


async def retrieve_context(state: WorkflowState) -> dict:
    email = state.get("email", {})
    subject = email.get("subject") or ""
    body = (email.get("body_plain") or "")[:500]
    query = f"{subject}\n{body}".strip()
    if not query:
        return {"retrieved_context": []}

    try:
        results = await asyncio.to_thread(
            chroma_client.search,
            user_id=state["user_id"],
            query=query,
            n_results=3,
        )
    except Exception as exc:
        logger.warning("workflow.retriever.failed", error=str(exc))
        return {"retrieved_context": []}

    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    out = [{"text": d, **(m or {})} for d, m in zip(docs, metas)]
    logger.info("workflow.retriever.done", email_id=state["email_id"], hits=len(out))
    return {"retrieved_context": out}
