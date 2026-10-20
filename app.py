"""PreventIA Streamlit shell for collection discovery and RAG queries."""

import os
from typing import Any, Dict

import streamlit as st

from preventia.bootstrap import build_catalog, build_retrieval_service
from preventia.config import Settings
from preventia.csv_analysis import CSVValidationError, profile_csv
from preventia.models import RAGQuery, UserContext


st.set_page_config(
    page_title="PreventIA",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="auto",
)


@st.cache_resource
def settings() -> Settings:
    return Settings.from_env()


@st.cache_resource
def catalog():
    return build_catalog(settings())


def current_user() -> UserContext:
    user_id = os.getenv("PREVENTIA_USER_ID")
    tenant_id = os.getenv("PREVENTIA_TENANT_ID")
    if not user_id or not tenant_id:
        raise RuntimeError(
            "Configure PREVENTIA_USER_ID e PREVENTIA_TENANT_ID para usar o chat"
        )
    return UserContext(
        user_id=user_id,
        tenant_id=tenant_id,
        group_ids=_csv_env("PREVENTIA_GROUP_IDS"),
        unit_ids=_csv_env("PREVENTIA_UNIT_IDS"),
        region_ids=_csv_env("PREVENTIA_REGION_IDS"),
        classifications=_csv_env("PREVENTIA_CLASSIFICATIONS") or ["internal"],
    )


def _csv_env(name: str):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def collection_message(user: UserContext) -> Dict[str, Any]:
    page = catalog().list_accessible(user, limit=settings().qdrant_collection_page_size)
    return {
        "role": "assistant",
        "type": "collections",
        "content": "Coleções de conhecimento disponíveis para seu perfil:",
        "items": [item.model_dump(mode="json") for item in page.items],
    }


def render_message(message: Dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        if message.get("type") == "csv_profile":
            st.markdown(f"**{message['content']}**")
            st.json(message["profile"])
            return
        if message.get("type") != "collections":
            st.write(message["content"])
            return
        st.markdown(f"**{message['content']}**")
        if not message.get("items"):
            st.write("Nenhuma coleção ativa está disponível para o seu escopo.")
            return
        for item in message["items"]:
            st.write(
                f"- **{item['display_name']}** — {item['description']} "
                f"({item['document_count']} documentos, embedding "
                f"{item['embedding_model_name']})"
            )


def render_history() -> None:
    for message in st.session_state.conversa:
        render_message(message)


def handle_prompt(prompt: str, user: UserContext) -> None:
    st.session_state.conversa.append({"role": "user", "content": prompt})
    normalized = prompt.casefold()
    if "coleções" in normalized or "colecoes" in normalized:
        st.session_state.conversa.append(collection_message(user))
        return
    try:
        service = build_retrieval_service(settings())
        response = service.query(user, RAGQuery(question=prompt))
    except LookupError:
        response = None
        answer = "Não há coleções autorizadas para consultar neste escopo."
    except RuntimeError as exc:
        response = None
        answer = str(exc)
    except Exception:
        response = None
        answer = "Não foi possível consultar a base de conhecimento agora."
    else:
        if not response.has_sufficient_evidence:
            answer = response.message or "Não encontrei evidência suficiente."
        else:
            answer = (
                "Encontrei estas evidências. A geração da resposta final deve usar "
                "um LLM Gateway configurado, preservando as citações:\n\n"
                + response.answer_context
            )
    st.session_state.conversa.append({"role": "assistant", "content": answer})


def process_uploaded_csv(uploaded_file: Any) -> None:
    content = uploaded_file.getvalue()
    try:
        profile = profile_csv(uploaded_file.name, content)
    except CSVValidationError as exc:
        st.error(str(exc))
        return
    if st.session_state.get("dataset_id") == profile.dataset_id:
        return
    st.session_state.dataset_id = profile.dataset_id
    st.session_state.conversa.append(
        {
            "role": "assistant",
            "type": "csv_profile",
            "content": f"CSV recebido: {profile.filename}",
            "profile": profile.model_dump(mode="json"),
        }
    )


def main() -> None:
    st.title("PreventIA")
    st.caption("Análise assistida de perdas com conhecimento autorizado")
    if "conversa" not in st.session_state:
        st.session_state.conversa = []
    if "collections_shown" not in st.session_state:
        st.session_state.collections_shown = False
    if "dataset_id" not in st.session_state:
        st.session_state.dataset_id = None

    with st.sidebar:
        st.header("Conhecimento")
        uploaded_file = st.file_uploader("Enviar CSV de perdas", type=["csv"])
        if uploaded_file is not None:
            process_uploaded_csv(uploaded_file)
        if st.button("Ver coleções disponíveis"):
            try:
                st.session_state.conversa.append(collection_message(current_user()))
                st.session_state.collections_shown = True
            except RuntimeError as exc:
                st.error(str(exc))
        if st.button("Novo chat"):
            st.session_state.conversa = []
            st.session_state.collections_shown = False
            st.session_state.dataset_id = None
            st.rerun()

    try:
        user = current_user()
    except RuntimeError as exc:
        st.info(str(exc))
        st.stop()

    render_history()
    prompt = st.chat_input("Pergunte sobre políticas, procedimentos ou perdas")
    if prompt:
        handle_prompt(prompt, user)
        st.rerun()


if __name__ == "__main__":
    main()
