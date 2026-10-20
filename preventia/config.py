"""Runtime configuration for the PreventIA backend.

Secrets are intentionally read from the environment and are never included in
API responses or logs.
"""

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class Settings:
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_model_version: str = "unresolved"
    embedding_dimension: int = 1024
    embedding_normalize: bool = True
    embedding_max_input_tokens: int = 8192
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    qdrant_timeout_seconds: float = 3.0
    qdrant_collection_page_size: int = 20
    rag_top_k: int = 8
    rag_min_relevance: float = 0.35
    rag_max_context_chunks: int = 8

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            embedding_model_name=os.getenv(
                "PREVENTIA_EMBEDDING_MODEL_NAME", "BAAI/bge-m3"
            ),
            embedding_model_version=os.getenv(
                "PREVENTIA_EMBEDDING_MODEL_VERSION", "unresolved"
            ),
            embedding_dimension=int(os.getenv("PREVENTIA_EMBEDDING_DIMENSION", "1024")),
            embedding_normalize=_parse_bool(
                os.getenv("PREVENTIA_EMBEDDING_NORMALIZE", "true")
            ),
            embedding_max_input_tokens=int(
                os.getenv("PREVENTIA_EMBEDDING_MAX_INPUT_TOKENS", "8192")
            ),
            qdrant_url=os.getenv("PREVENTIA_QDRANT_URL"),
            qdrant_api_key=os.getenv("PREVENTIA_QDRANT_API_KEY"),
            qdrant_timeout_seconds=float(
                os.getenv("PREVENTIA_QDRANT_TIMEOUT_SECONDS", "3")
            ),
            qdrant_collection_page_size=int(
                os.getenv("PREVENTIA_QDRANT_COLLECTION_PAGE_SIZE", "20")
            ),
            rag_top_k=int(os.getenv("PREVENTIA_RAG_TOP_K", "8")),
            rag_min_relevance=float(os.getenv("PREVENTIA_RAG_MIN_RELEVANCE", "0.35")),
            rag_max_context_chunks=int(
                os.getenv("PREVENTIA_RAG_MAX_CONTEXT_CHUNKS", "8")
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.embedding_model_name != "BAAI/bge-m3":
            raise ValueError("A V3 exige o modelo de embedding BAAI/bge-m3")
        if self.embedding_dimension != 1024:
            raise ValueError("BAAI/bge-m3 deve usar dimensão 1024 na V3")
        if not self.embedding_normalize:
            raise ValueError("Embeddings da V3 devem ser normalizados")
        if self.qdrant_url and self.embedding_model_version == "unresolved":
            raise ValueError(
                "PREVENTIA_EMBEDDING_MODEL_VERSION deve ser fixada ao usar Qdrant"
            )
        if self.qdrant_timeout_seconds <= 0:
            raise ValueError("PREVENTIA_QDRANT_TIMEOUT_SECONDS deve ser positivo")
        if not 1 <= self.qdrant_collection_page_size <= 100:
            raise ValueError("O tamanho da página deve estar entre 1 e 100")
        if not 1 <= self.rag_top_k <= 50:
            raise ValueError("PREVENTIA_RAG_TOP_K deve estar entre 1 e 50")
        if not 0 <= self.rag_min_relevance <= 1:
            raise ValueError("PREVENTIA_RAG_MIN_RELEVANCE deve estar entre 0 e 1")


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "sim"}:
        return True
    if normalized in {"0", "false", "no", "nao", "não"}:
        return False
    raise ValueError("Valor booleano inválido na configuração")
