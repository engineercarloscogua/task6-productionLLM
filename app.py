from __future__ import annotations

import os
from uuid import uuid4

import streamlit as st

from src.models import ModelOption, fetch_free_tool_models
from src.agent import AgentResponse, build_agent, run_agent
from src.pdf_knowledge import PDF_DIRECTORY, pdf_knowledge_store


st.set_page_config(
    page_title="Asistente universitario con LLM",
    page_icon="🎓",
    layout="wide",
)


@st.cache_data(ttl=900, show_spinner=False)
def load_models() -> list[ModelOption]:
    """Cache the public OpenRouter catalog to avoid repeated requests."""
    return fetch_free_tool_models()


def read_configured_api_key() -> str:
    """Read the key from Streamlit secrets or the process environment."""
    try:
        secret = st.secrets.get("OPENROUTER_API_KEY", "")
    except (FileNotFoundError, AttributeError):
        secret = ""
    return str(secret or os.getenv("OPENROUTER_API_KEY", "")).strip()


def initialize_session() -> None:
    defaults = {
        "messages": [],
        "metrics": [],
        "thread_id": str(uuid4()),
        "active_model": None,
        "agent": None,
        "temporary_api_key": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.metrics = []
    st.session_state.thread_id = str(uuid4())
    st.session_state.agent = None


def model_label(option: ModelOption) -> str:
    context = f"{option.context_length:,}" if option.context_length else "N/D"
    return f"{option.name} · contexto {context}"


initialize_session()

st.title("Asistente documental universitario")
st.caption("Actividad académica sobre agentes, herramientas, RAG y memoria con LangChain")
st.info(
    "Las respuestas se generan a partir de los documentos PDF cargados en el "
    "proyecto. Verifica siempre la información importante en el archivo original."
)

with st.sidebar:
    st.header("Configuración")
    configured_key = read_configured_api_key()
    if configured_key:
        api_key = configured_key
        st.success("API de OpenRouter configurada en el servidor.")
    else:
        st.caption(
            "Para una prueba local puedes introducir la clave durante esta sesión. "
            "No se guarda en archivos ni se muestra nuevamente."
        )
        st.text_input(
            "OPENROUTER_API_KEY",
            type="password",
            key="temporary_api_key",
            placeholder="sk-or-v1-…",
        )
        api_key = st.session_state.temporary_api_key.strip()

    try:
        model_options = load_models()
    except Exception as error:
        st.error(f"No fue posible consultar el catálogo: {error}")
        model_options = [ModelOption.free_router()]

    selected = st.selectbox(
        "Modelo gratuito con herramientas",
        options=model_options,
        format_func=model_label,
        help=(
            "La lista se obtiene de OpenRouter y se filtra por precio gratuito, "
            "salida de texto y soporte para tools."
        ),
    )
    st.caption(f"ID: `{selected.id}`")

    if st.button("Actualizar modelos", width="stretch"):
        load_models.clear()
        st.rerun()

    if st.button("Nueva conversación", width="stretch"):
        reset_conversation()
        st.rerun()

    st.divider()
    st.subheader("Documentos RAG")
    pdf_status = pdf_knowledge_store.status()
    if pdf_status.files:
        st.success(
            f"{len(pdf_status.files)} PDF · {pdf_status.pages_with_text} páginas "
            f"con texto · {pdf_status.chunks} fragmentos"
        )
        with st.expander("Archivos cargados"):
            for filename in pdf_status.files:
                st.write(f"- `{filename}`")
    else:
        st.warning("No hay PDF cargados en `data/pdfs/`.")
        st.caption(f"Carpeta: `{PDF_DIRECTORY}`")

    if pdf_status.errors:
        with st.expander("Errores de lectura", expanded=True):
            for error in pdf_status.errors:
                st.error(error)

    if st.button("Recargar documentos", width="stretch"):
        pdf_knowledge_store.refresh(force=True)
        reset_conversation()
        st.rerun()

    st.divider()
    st.caption(
        "Los modelos gratuitos tienen límites de solicitudes y disponibilidad variable. "
        "Cambiar de modelo inicia una conversación nueva."
    )

if st.session_state.active_model != selected.id:
    reset_conversation()
    st.session_state.active_model = selected.id

suggested_prompt = None
if pdf_status.files and pdf_status.chunks:
    suggestions = [
        "¿Cuál es el tema principal de los documentos?",
        "¿Qué requisitos se mencionan?",
        "¿Qué fechas o plazos importantes aparecen?",
    ]
    st.subheader("Preguntas sugeridas")
    columns = st.columns(len(suggestions))
    for column, suggestion in zip(columns, suggestions):
        if column.button(suggestion, width="stretch"):
            suggested_prompt = suggestion
else:
    st.warning(
        "Para activar el RAG, copia uno o más PDF con texto seleccionable en "
        "`data/pdfs/` y pulsa **Recargar documentos**."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("metadata"):
            metadata = message["metadata"]
            tools = ", ".join(metadata["tools"]) or "ninguna"
            st.caption(
                f"Modelo: {metadata['model']} · Herramientas: {tools} · "
                f"Latencia: {metadata['latency_seconds']:.2f} s"
            )

typed_prompt = st.chat_input(
    "Escribe una pregunta sobre los documentos cargados",
    disabled=not bool(api_key),
)
prompt = suggested_prompt or typed_prompt

if not api_key:
    st.warning(
        "Configura `OPENROUTER_API_KEY` en `.streamlit/secrets.toml`, como variable "
        "de entorno o temporalmente en la barra lateral para habilitar el chat."
    )

if prompt and api_key:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Consultando {selected.name}…"):
            try:
                if st.session_state.agent is None:
                    st.session_state.agent = build_agent(
                        api_key=api_key,
                        model_id=selected.id,
                    )
                response: AgentResponse = run_agent(
                    agent=st.session_state.agent,
                    message=prompt,
                    thread_id=st.session_state.thread_id,
                    model_id=selected.id,
                )
            except Exception as error:
                st.error(
                    "La consulta no pudo completarse. Revisa la clave, el límite del modelo "
                    f"o selecciona otro modelo. Detalle: {error}"
                )
            else:
                st.markdown(response.text)
                tools_text = ", ".join(response.tools) or "ninguna"
                st.caption(
                    f"Modelo: {response.model_id} · Herramientas: {tools_text} · "
                    f"Latencia: {response.latency_seconds:.2f} s"
                )
                metadata = {
                    "model": response.model_id,
                    "tools": response.tools,
                    "latency_seconds": response.latency_seconds,
                }
                st.session_state.messages.append(
                    {"role": "assistant", "content": response.text, "metadata": metadata}
                )
                st.session_state.metrics.append(
                    {
                        "modelo": response.model_id,
                        "latencia_s": round(response.latency_seconds, 3),
                        "herramientas": tools_text,
                        "estado": "correcto",
                    }
                )

if st.session_state.metrics:
    with st.expander("Métricas de esta sesión"):
        st.dataframe(st.session_state.metrics, width="stretch", hide_index=True)
