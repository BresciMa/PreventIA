"""Qdrant adapter. No Qdrant credential is exposed beyond this module."""

from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from .embeddings import validate_vectors
from .models import DocumentChunk, KnowledgeCollection, UserContext


class QdrantStoreError(RuntimeError):
    """Safe infrastructure error; the provider error is not exposed."""


class QdrantVectorStore:
    def __init__(
        self,
        url: Optional[str],
        api_key: Optional[str],
        timeout_seconds: float,
        client: Optional[Any] = None,
    ) -> None:
        if client is not None:
            self._client = client
            return
        if not url:
            raise ValueError("URL do Qdrant é obrigatória")
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError("Instale qdrant-client para habilitar o Qdrant") from exc
        self._client = QdrantClient(url=url, api_key=api_key, timeout=timeout_seconds)

    def ensure_collection(self, collection: KnowledgeCollection) -> None:
        try:
            from qdrant_client.http import models

            existing = {
                item.name for item in self._client.get_collections().collections
            }
            if collection.qdrant_collection_name not in existing:
                self._client.create_collection(
                    collection_name=collection.qdrant_collection_name,
                    vectors_config=models.VectorParams(
                        size=1024, distance=models.Distance.COSINE
                    ),
                    on_disk_payload=True,
                )
                return
            info = self._client.get_collection(collection.qdrant_collection_name)
            size = _vector_size(info)
            if size != 1024:
                raise ValueError("Collection Qdrant incompatível com BAAI/bge-m3")
        except ValueError:
            raise
        except Exception as exc:
            raise QdrantStoreError("Qdrant indisponível") from exc

    def upsert(
        self,
        collection: KnowledgeCollection,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        try:
            from qdrant_client.http import models

            validate_vectors(vectors, 1024)
            if len(chunks) != len(vectors):
                raise ValueError("Quantidade de chunks e vetores não coincide")
            points = [
                models.PointStruct(
                    id=_point_id(chunk.chunk_id),
                    vector=list(vector),
                    payload=_payload(chunk),
                )
                for chunk, vector in zip(chunks, vectors)
            ]
            self._client.upsert(
                collection_name=collection.qdrant_collection_name,
                points=points,
                wait=True,
            )
        except ValueError:
            raise
        except Exception as exc:
            raise QdrantStoreError("Qdrant indisponível") from exc

    def search(
        self,
        collection: KnowledgeCollection,
        vector: Sequence[float],
        user: UserContext,
        limit: int,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        try:
            from qdrant_client.http import models

            validate_vectors([vector], 1024)
            must = [
                models.FieldCondition(
                    key="tenant_id", match=models.MatchValue(value=user.tenant_id)
                ),
                models.FieldCondition(
                    key="status", match=models.MatchValue(value="published")
                ),
                models.FieldCondition(
                    key="classification",
                    match=models.MatchAny(any=user.classifications),
                ),
            ]
            should = []
            if user.unit_ids:
                should.append(
                    models.FieldCondition(
                        key="unit_ids", match=models.MatchAny(any=user.unit_ids)
                    )
                )
            if user.region_ids:
                should.append(
                    models.FieldCondition(
                        key="region_ids", match=models.MatchAny(any=user.region_ids)
                    )
                )
            # A scope supplied by the identity is always part of the vector filter;
            # client-supplied raw Qdrant filters never reach this adapter.
            query_filter = models.Filter(
                must=must,
                should=should or None,
                min_should=1 if should else None,
            )
            if hasattr(self._client, "query_points"):
                hits = self._client.query_points(
                    collection_name=collection.qdrant_collection_name,
                    query=list(vector),
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                ).points
            else:
                hits = self._client.search(
                    collection_name=collection.qdrant_collection_name,
                    query_vector=list(vector),
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                )
            result = []
            for hit in hits:
                payload = dict(hit.payload or {})
                chunk_id = payload.get("chunk_id")
                if not chunk_id:
                    continue
                result.append((str(chunk_id), float(hit.score), payload))
            return result
        except ValueError:
            raise
        except Exception as exc:
            raise QdrantStoreError("Qdrant indisponível") from exc


def _payload(chunk: DocumentChunk) -> Dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_version": chunk.document_version,
        "collection_id": chunk.collection_id,
        "tenant_id": chunk.tenant_id,
        "domain": chunk.domain,
        "unit_ids": chunk.unit_ids,
        "region_ids": chunk.region_ids,
        "classification": chunk.classification,
        "status": chunk.status,
        "valid_from": chunk.valid_from.isoformat() if chunk.valid_from else None,
        "valid_to": chunk.valid_to.isoformat() if chunk.valid_to else None,
        "source_title": chunk.source_title,
        "source_locator": chunk.source_locator,
        "content_hash": chunk.content_hash,
    }


def _point_id(chunk_id: str) -> UUID:
    """Qdrant accepts UUID/int point IDs; the domain ID stays in the payload."""
    import hashlib

    return UUID(bytes=hashlib.sha256(chunk_id.encode("utf-8")).digest()[:16], version=4)


def _vector_size(info: Any) -> Optional[int]:
    config = getattr(info, "config", None)
    params = getattr(config, "params", None)
    vectors = getattr(params, "vectors", None)
    if isinstance(vectors, dict):
        vectors = next(iter(vectors.values()), None)
    return getattr(vectors, "size", None)
