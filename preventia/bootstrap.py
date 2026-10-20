"""Dependency wiring for local development and tests.

Production should replace the in-memory catalog/chunk repository with
PostgreSQL and object storage adapters, while retaining the service contracts.
"""

import json
import os
from typing import List

from .catalog import InMemoryCollectionCatalog
from .config import Settings
from .embeddings import BGEEmbeddingProvider
from .ingestion import InMemoryChunkRepository
from .models import KnowledgeCollection
from .qdrant_store import QdrantVectorStore
from .retrieval import RetrievalService


def load_local_collections() -> List[KnowledgeCollection]:
    raw = os.getenv("PREVENTIA_COLLECTIONS_JSON", "[]")
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("PREVENTIA_COLLECTIONS_JSON deve ser um JSON válido") from exc
    if not isinstance(values, list):
        raise ValueError("PREVENTIA_COLLECTIONS_JSON deve ser uma lista")
    return [KnowledgeCollection.model_validate(value) for value in values]


def build_catalog(settings: Settings) -> InMemoryCollectionCatalog:
    collections = load_local_collections()
    for collection in collections:
        if collection.embedding_model_name != settings.embedding_model_name:
            raise ValueError("Collection cadastrada usa modelo incompatível")
        if collection.vector_size != settings.embedding_dimension:
            raise ValueError("Collection cadastrada usa dimensão incompatível")
    return InMemoryCollectionCatalog(collections)


def build_embedding_provider(settings: Settings) -> BGEEmbeddingProvider:
    return BGEEmbeddingProvider(model_version=settings.embedding_model_version)


def build_retrieval_service(settings: Settings) -> RetrievalService:
    if not settings.qdrant_url:
        raise RuntimeError("PREVENTIA_QDRANT_URL não configurada")
    catalog = build_catalog(settings)
    embeddings = build_embedding_provider(settings)
    vector_store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout_seconds=settings.qdrant_timeout_seconds,
    )
    return RetrievalService(
        catalog=catalog,
        embeddings=embeddings,
        vector_store=vector_store,
        chunks=InMemoryChunkRepository(),
        min_relevance=settings.rag_min_relevance,
        max_context_chunks=settings.rag_max_context_chunks,
    )
