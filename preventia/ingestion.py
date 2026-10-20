"""Deterministic document chunking and idempotent ingestion primitives."""

import hashlib
import io
import re
from html import unescape
from typing import Dict, List, Protocol, Sequence

from .embeddings import EmbeddingProvider
from .models import DocumentChunk, KnowledgeCollection
from .qdrant_store import QdrantVectorStore


class ChunkRepository(Protocol):
    def save_many(self, chunks: Sequence[DocumentChunk]) -> None: ...

    def get(self, chunk_id: str) -> DocumentChunk: ...


class InMemoryChunkRepository:
    def __init__(self) -> None:
        self._chunks: Dict[str, DocumentChunk] = {}

    def save_many(self, chunks: Sequence[DocumentChunk]) -> None:
        self._chunks.update({chunk.chunk_id: chunk for chunk in chunks})

    def get(self, chunk_id: str) -> DocumentChunk:
        try:
            return self._chunks[chunk_id]
        except KeyError as exc:
            raise LookupError("Chunk não encontrado") from exc


def split_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size/overlap inválidos")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = end - overlap
    return chunks


class DocumentIngestionService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: QdrantVectorStore,
        chunk_repository: ChunkRepository,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.chunk_repository = chunk_repository

    def ingest_text(
        self,
        collection: KnowledgeCollection,
        document_id: str,
        document_version: int,
        title: str,
        text: str,
        source_locator_prefix: str = "texto",
    ) -> List[DocumentChunk]:
        pieces = split_text(text)
        chunks = [
            DocumentChunk(
                chunk_id=_chunk_id(
                    collection, document_id, document_version, index, piece
                ),
                document_id=document_id,
                document_version=document_version,
                collection_id=collection.collection_id,
                tenant_id=collection.tenant_id,
                domain=collection.domain,
                text=piece,
                source_title=title,
                source_locator=f"{source_locator_prefix}#{index + 1}",
                content_hash="sha256:"
                + hashlib.sha256(piece.encode("utf-8")).hexdigest(),
            )
            for index, piece in enumerate(pieces)
        ]
        vectors = self.embedding_provider.embed([chunk.text for chunk in chunks])
        self.vector_store.ensure_collection(collection)
        self.vector_store.upsert(collection, chunks, vectors)
        self.chunk_repository.save_many(chunks)
        return chunks

    def ingest_file(
        self,
        collection: KnowledgeCollection,
        document_id: str,
        document_version: int,
        title: str,
        filename: str,
        content: bytes,
    ) -> List[DocumentChunk]:
        """Extract supported source formats before the common chunk pipeline."""
        text = extract_text(filename, content)
        return self.ingest_text(
            collection=collection,
            document_id=document_id,
            document_version=document_version,
            title=title,
            text=text,
            source_locator_prefix=filename,
        )


def _chunk_id(
    collection: KnowledgeCollection,
    document_id: str,
    version: int,
    index: int,
    text: str,
) -> str:
    raw = "|".join(
        [
            collection.collection_id,
            document_id,
            str(version),
            str(index),
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        ]
    )
    return "chk_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from the V3 MVP formats without executing document data."""
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix in {"txt", "md"}:
        return _decode_text(content)
    if suffix == "html":
        html = _decode_text(content)
        return unescape(re.sub(r"<[^>]+>", " ", html))
    if suffix == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Instale pypdf para ingerir PDF") from exc
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Formato não suportado; use PDF, Markdown, HTML ou TXT")


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Encoding do documento não suportado")
