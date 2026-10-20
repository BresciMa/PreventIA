"""Embedding adapters with a fixed BGE-M3 contract."""

import math
from typing import List, Protocol, Sequence


class EmbeddingProvider(Protocol):
    model_name: str
    dimension: int
    model_version: str

    def embed(self, texts: Sequence[str]) -> List[List[float]]: ...


def validate_vectors(
    vectors: Sequence[Sequence[float]], expected_dimension: int
) -> None:
    for vector in vectors:
        if len(vector) != expected_dimension:
            raise ValueError(
                "Dimensão de embedding incompatível: "
                f"esperado={expected_dimension}, recebido={len(vector)}"
            )
        if not all(math.isfinite(float(value)) for value in vector):
            raise ValueError("Embedding inválido: vetor contém valor não finito")


class BGEEmbeddingProvider:
    """Lazy adapter so API startup does not download a model unexpectedly."""

    model_name = "BAAI/bge-m3"
    dimension = 1024

    def __init__(self, model_version: str = "unresolved") -> None:
        self.model_version = model_version
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "Instale sentence-transformers para habilitar BAAI/bge-m3"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        result = [[float(value) for value in vector] for vector in vectors]
        validate_vectors(result, self.dimension)
        return result
