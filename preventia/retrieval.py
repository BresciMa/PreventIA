"""ACL-first retrieval and citation assembly."""

from datetime import date
from typing import List, Protocol, Sequence, Tuple, Dict, Any

from .catalog import CollectionCatalog
from .embeddings import EmbeddingProvider
from .models import (
    Citation,
    DocumentChunk,
    RAGQuery,
    RAGResponse,
    RetrievalHit,
    UserContext,
)


class SearchStore(Protocol):
    def search(
        self, collection: Any, vector: Sequence[float], user: UserContext, limit: int
    ) -> List[Tuple[str, float, Dict[str, Any]]]: ...


class ChunkReader(Protocol):
    def get(self, chunk_id: str) -> DocumentChunk: ...


class RetrievalService:
    def __init__(
        self,
        catalog: CollectionCatalog,
        embeddings: EmbeddingProvider,
        vector_store: SearchStore,
        chunks: ChunkReader,
        min_relevance: float = 0.35,
        max_context_chunks: int = 8,
    ) -> None:
        self.catalog = catalog
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.chunks = chunks
        self.min_relevance = min_relevance
        self.max_context_chunks = max_context_chunks

    def query(self, user: UserContext, request: RAGQuery) -> RAGResponse:
        collections = self._resolve_collections(user, request.collection_id)
        vector = self.embeddings.embed([request.question])[0]
        limit = min(request.top_k or self.max_context_chunks, self.max_context_chunks)
        candidates: List[RetrievalHit] = []
        for collection in collections:
            for chunk_id, score, _payload in self.vector_store.search(
                collection, vector, user, limit
            ):
                if score < self.min_relevance:
                    continue
                chunk = self.chunks.get(chunk_id)
                # The catalog check above and this defensive check avoid trusting
                # arbitrary payload values returned by the vector store.
                if (
                    chunk.collection_id != collection.collection_id
                    or not _chunk_is_visible(chunk, user)
                ):
                    continue
                candidates.append(
                    RetrievalHit(
                        chunk=chunk,
                        score=score,
                        citation=Citation(
                            citation_id="cit_" + chunk.chunk_id,
                            document_id=chunk.document_id,
                            document_version=chunk.document_version,
                            chunk_id=chunk.chunk_id,
                            source_title=chunk.source_title,
                            source_locator=chunk.source_locator,
                            content_hash=chunk.content_hash,
                        ),
                    )
                )
        candidates.sort(key=lambda item: item.score, reverse=True)
        evidence = candidates[:limit]
        if not evidence:
            return RAGResponse(
                answer_context="",
                evidence=[],
                has_sufficient_evidence=False,
                message="Não encontrei evidência suficiente nas coleções autorizadas.",
            )
        context = "\n\n".join(
            f"[{hit.citation.citation_id}] {hit.chunk.text}" for hit in evidence
        )
        return RAGResponse(
            answer_context=context,
            evidence=evidence,
            has_sufficient_evidence=True,
        )

    def _resolve_collections(self, user: UserContext, collection_id: str):
        if collection_id:
            return [self.catalog.get_accessible(user, collection_id)]
        page = self.catalog.list_accessible(user, limit=100)
        collections = []
        for summary in page.items:
            collections.append(self.catalog.get_accessible(user, summary.collection_id))
        if not collections:
            raise LookupError("Nenhuma coleção autorizada para consulta")
        return collections


def _chunk_is_visible(chunk: DocumentChunk, user: UserContext) -> bool:
    """Defense in depth for ACL and validity after controlled chunk loading."""
    if chunk.tenant_id != user.tenant_id or chunk.status != "published":
        return False
    if chunk.classification not in user.classifications:
        return False
    if chunk.unit_ids and not set(chunk.unit_ids).intersection(user.unit_ids):
        return False
    if chunk.region_ids and not set(chunk.region_ids).intersection(user.region_ids):
        return False
    today = date.today()
    if chunk.valid_from and chunk.valid_from > today:
        return False
    if chunk.valid_to and chunk.valid_to < today:
        return False
    return True
