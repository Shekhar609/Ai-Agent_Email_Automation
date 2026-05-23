from functools import lru_cache
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

COLLECTION_NAME = "emails"


@lru_cache(maxsize=1)
def get_client():
    s = get_settings()
    return chromadb.HttpClient(
        host=s.chroma_host,
        port=s.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_collection():
    return get_client().get_or_create_collection(name=COLLECTION_NAME)


def upsert_email(
    *,
    email_id: str,
    user_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    coll = get_collection()
    md = {"user_id": user_id}
    if metadata:
        md.update({k: v for k, v in metadata.items() if v is not None})
    coll.upsert(ids=[email_id], documents=[text], metadatas=[md])


def search(*, user_id: str, query: str, n_results: int = 5) -> dict:
    return get_collection().query(
        query_texts=[query],
        n_results=n_results,
        where={"user_id": user_id},
    )
