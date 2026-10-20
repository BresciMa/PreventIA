from qdrant_client import QdrantClient

from preventia.models import (
    CollectionStatus,
    DocumentChunk,
    KnowledgeCollection,
    UserContext,
)
from preventia.qdrant_store import QdrantVectorStore


def test_qdrant_adapter_uses_stable_point_ids_and_returns_domain_chunk_id():
    collection = KnowledgeCollection(
        collection_id="col-1",
        display_name="Políticas",
        description="",
        qdrant_collection_name="policies",
        tenant_id="tenant-1",
        domain="prevencao",
        status=CollectionStatus.ACTIVE,
        embedding_model_version="test",
    )
    chunk = DocumentChunk(
        chunk_id="chk_abc",
        document_id="doc-1",
        document_version=1,
        collection_id="col-1",
        tenant_id="tenant-1",
        domain="prevencao",
        text="procedimento",
        source_title="Política",
        source_locator="pagina-1",
        content_hash="sha256:test",
    )
    store = QdrantVectorStore(
        url=None,
        api_key=None,
        timeout_seconds=3,
        client=QdrantClient(path=":memory:"),
    )
    store.ensure_collection(collection)
    store.upsert(collection, [chunk], [[0.1] * 1024])

    hits = store.search(
        collection,
        [0.1] * 1024,
        UserContext(user_id="user-1", tenant_id="tenant-1"),
        limit=1,
    )

    assert hits[0][0] == "chk_abc"
