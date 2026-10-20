"""Domain contracts shared by catalog, ingestion and retrieval services."""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CollectionStatus(str, Enum):
    DRAFT = "DRAFT"
    INDEXING = "INDEXING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REINDEXING = "REINDEXING"
    DEPRECATED = "DEPRECATED"
    DELETED = "DELETED"


class UserContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    group_ids: List[str] = Field(default_factory=list)
    unit_ids: List[str] = Field(default_factory=list)
    region_ids: List[str] = Field(default_factory=list)
    classifications: List[str] = Field(default_factory=lambda: ["internal"])
    is_curator: bool = False


class KnowledgeCollection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    collection_id: str
    display_name: str
    description: str
    qdrant_collection_name: str
    tenant_id: str
    domain: str
    status: CollectionStatus
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_model_version: str
    vector_size: int = 1024
    distance: str = "Cosine"
    document_count: int = 0
    chunk_count: int = 0
    last_successful_sync_at: Optional[datetime] = None
    allowed_group_ids: List[str] = Field(default_factory=list)
    allowed_unit_ids: List[str] = Field(default_factory=list)
    allowed_region_ids: List[str] = Field(default_factory=list)
    allowed_classifications: List[str] = Field(default_factory=list)


class CollectionSummary(BaseModel):
    collection_id: str
    display_name: str
    description: str
    status: CollectionStatus
    document_count: int
    chunk_count: int
    last_successful_sync_at: Optional[datetime]
    embedding_model_name: str
    embedding_dimension: int


class CollectionPage(BaseModel):
    items: List[CollectionSummary]
    next_cursor: Optional[str] = None


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_version: int
    collection_id: str
    tenant_id: str
    domain: str
    text: str
    source_title: str
    source_locator: str
    content_hash: str
    unit_ids: List[str] = Field(default_factory=list)
    region_ids: List[str] = Field(default_factory=list)
    classification: str = "internal"
    status: str = "published"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class Citation(BaseModel):
    citation_id: str
    document_id: str
    document_version: int
    chunk_id: str
    source_title: str
    source_locator: str
    content_hash: str


class RetrievalHit(BaseModel):
    chunk: DocumentChunk
    score: float
    citation: Citation


class RAGQuery(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    collection_id: Optional[str] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=50)


class RAGResponse(BaseModel):
    answer_context: str
    evidence: List[RetrievalHit]
    has_sufficient_evidence: bool
    message: Optional[str] = None


class CSVProfile(BaseModel):
    dataset_id: str
    filename: str
    encoding: str
    delimiter: str
    row_count: int
    columns: List[str]
    null_counts: dict
    numeric_columns: List[str]
    warnings: List[str] = Field(default_factory=list)


class CSVAnalysisPlan(BaseModel):
    operation: Literal["count", "sum", "mean", "min", "max"]
    column: Optional[str] = None
    group_by: Optional[str] = None
    filters: Dict[str, str] = Field(default_factory=dict)


class CSVAnalysisResult(BaseModel):
    dataset_id: str
    operation: str
    column: Optional[str]
    value: Optional[float] = None
    groups: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
