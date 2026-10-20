"""Authorized knowledge collection catalog.

The in-memory implementation is deliberately injectable. Production wiring
should replace it with a PostgreSQL repository without changing retrieval APIs.
"""

import base64
import json
from typing import Dict, Iterable, Optional, Protocol

from .models import (
    CollectionPage,
    CollectionStatus,
    CollectionSummary,
    KnowledgeCollection,
    UserContext,
)


class CollectionCatalog(Protocol):
    def list_accessible(
        self, user: UserContext, limit: int, cursor: Optional[str] = None
    ) -> CollectionPage: ...

    def get_accessible(
        self, user: UserContext, collection_id: str
    ) -> KnowledgeCollection: ...


class InMemoryCollectionCatalog:
    def __init__(self, collections: Iterable[KnowledgeCollection] = ()) -> None:
        self._collections: Dict[str, KnowledgeCollection] = {
            item.collection_id: item for item in collections
        }

    def add(self, collection: KnowledgeCollection) -> None:
        self._collections[collection.collection_id] = collection

    def list_accessible(
        self, user: UserContext, limit: int, cursor: Optional[str] = None
    ) -> CollectionPage:
        if not 1 <= limit <= 100:
            raise ValueError("limit deve estar entre 1 e 100")
        offset = _decode_cursor(cursor)
        visible = [
            item
            for item in sorted(
                self._collections.values(), key=lambda value: value.display_name
            )
            if item.status == CollectionStatus.ACTIVE and _can_access(item, user)
        ]
        page = visible[offset : offset + limit]
        next_cursor = (
            _encode_cursor(offset + limit) if offset + limit < len(visible) else None
        )
        return CollectionPage(
            items=[
                CollectionSummary(
                    collection_id=item.collection_id,
                    display_name=item.display_name,
                    description=item.description,
                    status=item.status,
                    document_count=item.document_count,
                    chunk_count=item.chunk_count,
                    last_successful_sync_at=item.last_successful_sync_at,
                    embedding_model_name=item.embedding_model_name,
                    embedding_dimension=item.vector_size,
                )
                for item in page
            ],
            next_cursor=next_cursor,
        )

    def get_accessible(
        self, user: UserContext, collection_id: str
    ) -> KnowledgeCollection:
        item = self._collections.get(collection_id)
        if (
            item is None
            or item.status != CollectionStatus.ACTIVE
            or not _can_access(item, user)
        ):
            raise LookupError("Coleção não encontrada ou não autorizada")
        return item


def _can_access(collection: KnowledgeCollection, user: UserContext) -> bool:
    if collection.tenant_id != user.tenant_id:
        return False
    if collection.allowed_group_ids and not set(
        collection.allowed_group_ids
    ).intersection(user.group_ids):
        return False
    if collection.allowed_unit_ids and not set(
        collection.allowed_unit_ids
    ).intersection(user.unit_ids):
        return False
    if collection.allowed_region_ids and not set(
        collection.allowed_region_ids
    ).intersection(user.region_ids):
        return False
    if collection.allowed_classifications and not set(
        collection.allowed_classifications
    ).intersection(user.classifications):
        return False
    return True


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"offset": offset}).encode()).decode()


def _decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        offset = int(payload["offset"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("cursor inválido") from exc
    if offset < 0:
        raise ValueError("cursor inválido")
    return offset
