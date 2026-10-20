from datetime import datetime, timezone
from typing import List, Sequence

from preventia.catalog import InMemoryCollectionCatalog
from preventia.models import (
    CollectionStatus,
    DocumentChunk,
    KnowledgeCollection,
    RAGQuery,
    UserContext,
)
from preventia.retrieval import RetrievalService


class FakeEmbeddings:
    model_name = "BAAI/bge-m3"
    model_version = "test"
    dimension = 1024

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [[0.1] * 1024 for _ in texts]


class FakeStore:
    def search(self, collection, vector, user, limit):
        return [("chunk-1", 0.9, {"tenant_id": "other-tenant"})]


class Chunks:
    def get(self, chunk_id):
        return DocumentChunk(
            chunk_id=chunk_id,
            document_id="doc-1",
            document_version=1,
            collection_id="col-1",
            tenant_id="tenant-1",
            domain="prevencao",
            text="conteúdo autorizado",
            source_title="Política",
            source_locator="pagina-1",
            content_hash="sha256:test",
        )


def test_retrieval_does_not_trust_qdrant_payload_for_citation():
    collection = KnowledgeCollection(
        collection_id="col-1",
        display_name="Políticas",
        description="",
        qdrant_collection_name="policies",
        tenant_id="tenant-1",
        domain="prevencao",
        status=CollectionStatus.ACTIVE,
        embedding_model_version="test",
        last_successful_sync_at=datetime.now(timezone.utc),
    )
    user = UserContext(user_id="u-1", tenant_id="tenant-1")
    service = RetrievalService(
        catalog=InMemoryCollectionCatalog([collection]),
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        chunks=Chunks(),
    )

    response = service.query(user, RAGQuery(question="qual procedimento?"))

    assert response.has_sufficient_evidence is True
    assert response.evidence[0].chunk.tenant_id == "tenant-1"
