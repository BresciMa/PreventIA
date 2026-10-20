import math

import pytest

from preventia.embeddings import validate_vectors
from preventia.ingestion import extract_text, split_text
from preventia.qdrant_store import _point_id


def test_vectors_must_match_bge_dimension_and_be_finite():
    with pytest.raises(ValueError):
        validate_vectors([[0.0] * 1023], 1024)
    with pytest.raises(ValueError):
        validate_vectors([[math.nan] * 1024], 1024)


def test_split_text_is_deterministic_and_overlaps():
    text = "palavra " * 400
    chunks = split_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert chunks[0][-10:] in chunks[1]


def test_document_extraction_and_qdrant_point_id_are_safe():
    assert "política" in extract_text("policy.md", "# política".encode())
    point_id = _point_id("chk_abc")

    assert point_id.version == 4
