"""FastAPI application factory for the PreventIA V3 contracts."""

from dataclasses import dataclass
from typing import Callable, Optional

from pydantic import ValidationError

from .catalog import CollectionCatalog
from .csv_analysis import CSVValidationError, analyze_csv, profile_csv
from .models import (
    CSVAnalysisPlan,
    CollectionPage,
    RAGQuery,
    RAGResponse,
    UserContext,
)
from .retrieval import RetrievalService


@dataclass
class AppContainer:
    catalog: CollectionCatalog
    retrieval: RetrievalService


def create_app(
    container: AppContainer,
    user_provider: Optional[Callable[[object], UserContext]] = None,
    allow_dev_identity: bool = False,
):
    try:
        from fastapi import (
            Depends,
            FastAPI,
            File,
            Header,
            HTTPException,
            Query,
            Request,
            UploadFile,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Instale fastapi e python-multipart para habilitar a API"
        ) from exc

    app = FastAPI(title="PreventIA API", version="3.0.0")

    def current_user(
        request: Request,
        x_user_id: Optional[str] = Header(default=None),
        x_tenant_id: Optional[str] = Header(default=None),
    ) -> UserContext:
        if user_provider is not None:
            return user_provider(request)
        if allow_dev_identity and x_user_id and x_tenant_id:
            # Explicitly opt-in local adapter; never enable it in production.
            return UserContext(user_id=x_user_id, tenant_id=x_tenant_id)
        raise HTTPException(status_code=401, detail="Sessão autenticada obrigatória")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "preventia-api"}

    @app.get("/knowledge/collections", response_model=CollectionPage)
    def list_collections(
        limit: int = Query(default=20, ge=1, le=100),
        cursor: Optional[str] = Query(default=None),
        user: UserContext = Depends(current_user),
    ) -> CollectionPage:
        try:
            return container.catalog.list_accessible(user, limit=limit, cursor=cursor)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/knowledge/collections/{collection_id}/query",
        response_model=RAGResponse,
    )
    def query_collection(
        collection_id: str,
        request: RAGQuery,
        user: UserContext = Depends(current_user),
    ) -> RAGResponse:
        if request.collection_id and request.collection_id != collection_id:
            raise HTTPException(status_code=400, detail="collection_id inconsistente")
        request.collection_id = collection_id
        try:
            return container.retrieval.query(user, request)
        except LookupError as exc:
            raise HTTPException(
                status_code=404, detail="Coleção não encontrada"
            ) from exc
        except (RuntimeError, TimeoutError) as exc:
            raise HTTPException(
                status_code=503, detail="Serviço de conhecimento indisponível"
            ) from exc

    @app.post("/datasets/profile")
    async def profile_dataset(
        file: UploadFile = File(...),
        _user: UserContext = Depends(current_user),
    ):
        try:
            content = await file.read()
            return profile_csv(file.filename or "dataset.csv", content)
        except (CSVValidationError, ValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/datasets/analyze")
    async def analyze_dataset(
        file: UploadFile = File(...),
        operation: str = Query(...),
        column: Optional[str] = Query(default=None),
        group_by: Optional[str] = Query(default=None),
        _user: UserContext = Depends(current_user),
    ):
        try:
            plan = CSVAnalysisPlan(
                operation=operation,
                column=column,
                group_by=group_by,
            )
            content = await file.read()
            return analyze_csv(file.filename or "dataset.csv", content, plan)
        except (CSVValidationError, ValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app
