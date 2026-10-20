from datetime import datetime, timezone

import pytest

from preventia.catalog import InMemoryCollectionCatalog
from preventia.models import CollectionStatus, KnowledgeCollection, UserContext


def collection(**overrides):
    values = dict(
        collection_id="col-1",
        display_name="Políticas",
        description="Políticas de prevenção",
        qdrant_collection_name="preventia_policies_v1",
        tenant_id="tenant-1",
        domain="prevencao",
        status=CollectionStatus.ACTIVE,
        embedding_model_version="model-sha",
        document_count=2,
        chunk_count=4,
        last_successful_sync_at=datetime.now(timezone.utc),
        allowed_unit_ids=["store-1"],
    )
    values.update(overrides)
    return KnowledgeCollection(**values)


def test_catalog_filters_by_tenant_and_unit_without_leaking_restricted_collections():
    catalog = InMemoryCollectionCatalog(
        [
            collection(),
            collection(
                collection_id="restricted",
                display_name="Restrita",
                allowed_unit_ids=["store-9"],
            ),
            collection(collection_id="other-tenant", tenant_id="tenant-2"),
        ]
    )
    user = UserContext(user_id="u-1", tenant_id="tenant-1", unit_ids=["store-1"])

    page = catalog.list_accessible(user, limit=20)

    assert [item.collection_id for item in page.items] == ["col-1"]


def test_inactive_collection_is_not_accessible():
    catalog = InMemoryCollectionCatalog([collection(status=CollectionStatus.PAUSED)])
    user = UserContext(user_id="u-1", tenant_id="tenant-1", unit_ids=["store-1"])

    with pytest.raises(LookupError):
        catalog.get_accessible(user, "col-1")
