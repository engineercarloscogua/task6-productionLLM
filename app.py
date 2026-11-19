from __future__ import annotations

import os
from uuid import uuid4

import streamlit as st

from src.models import ModelOption, default_model_index, fetch_free_tool_models
from src.agent import AgentResponse, build_agent, run_agent
from src.pdf_knowledge import PDF_DIRECTORY, pdf_knowledge_store


st.set_page_config(
    page_title="Asistente de Fomento Socioeconómico | UNITRÓPICO",
    page_icon="🌿",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --unitropico-navy: #12324a;
        --unitropico-green: #16745b;
        --unitropico-mint: #e7f5ee;
        --unitropico-gold: #d9a441;
        --unitropico-ink: #18302a;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 92% 4%, rgba(217, 164, 65, 0.14), transparent 24rem),
            linear-gradient(180deg, #f7fbf9 0%, #eef6f2 100%);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f3faf6 0%, #e7f2ed 100%);
        border-right: 1px solid rgba(22, 116, 91, 0.14);
    }

    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .unitropico-hero {
        position: relative;
        overflow: hidden;
        padding: 2.2rem 2.4rem;
        margin-bottom: 1.25rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 24px;
        color: white;
        background: linear-gradient(125deg, #12324a 0%, #17634f 68%, #27806a 100%);
        box-shadow: 0 18px 45px rgba(18, 50, 74, 0.18);
    }

    .unitropico-hero::after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -90px;
        top: -120px;
        border: 42px solid rgba(255, 255, 255, 0.08);
        border-radius: 50%;
    }

    .unitropico-eyebrow {
        margin: 0 0 0.55rem;
        color: #d9f2e5;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .unitropico-hero h1 {
        max-width: 820px;
        margin: 0;
        color: white;
        font-size: clamp(2rem, 4vw, 3.15rem);
        line-height: 1.08;
        letter-spacing: -0.035em;
    }

    .unitropico-hero p:last-child {
        max-width: 850px;
        margin: 1rem 0 0;
        color: rgba(255, 255, 255, 0.88);
        font-size: 1.05rem;
        line-height: 1.7;
    }

    [data-testid="stChatMessage"] {
        padding: 1.05rem 1.2rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(22, 116, 91, 0.12);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 8px 24px rgba(18, 50, 74, 0.06);
    }

    [data-testid="stChatInput"] {
        border: 1px solid rgba(22, 116, 91, 0.22);
        border-radius: 18px;
        box-shadow: 0 12px 32px rgba(18, 50, 74, 0.10);
    }

    .stButton > button {
        min-height: 2.75rem;
        border-color: rgba(22, 116, 91, 0.24);
        border-radius: 14px;
        font-weight: 650;
        transition: transform 120ms ease, box-shadow 120ms ease;
    }

    .stButton > button:hover {
        border-color: var(--unitropico-green);
        color: var(--unitropico-green);
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(22, 116, 91, 0.12);
    }

    div[data-testid="stMetric"], div[data-testid="stExpander"] {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
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

st.markdown(
    """
    <section class="unitropico-hero">
        <p class="unitropico-eyebrow">Bienestar Universitario · UNITRÓPICO</p>
        <h1>Asistente de Fomento Socioeconómico UNITRÓPICO</h1>
        <p>
            Este es tu agente conversacional, al cual puedes preguntar dudas sobre los
            programas de fomento socioeconómico, como Bienestar Contigo y Renta Joven,
            además de las dudas que tengas acerca de la Política de Bienestar Universitario.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)
st.info(
    "Las respuestas se apoyan en los documentos institucionales cargados. "
    "Verifica siempre la información importante en el archivo original citado."
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
        index=default_model_index(model_options),
        format_func=model_label,
        key="model_selector",
        help=(
            "La lista se obtiene de OpenRouter y se filtra por precio gratuito, "
            "salida de texto y soporte para herramientas. Nemotron 3.5 Lightning "
            "se selecciona por defecto cuando está disponible."
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
        "¿Cuáles son los requisitos para acceder a Renta Joven?",
        "¿Qué apoyos ofrece el programa Bienestar Contigo?",
        "Resume los principios de la Política de Bienestar Universitario.",
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
    avatar = "🌿" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("metadata"):
            metadata = message["metadata"]
            tools = ", ".join(metadata["tools"]) or "ninguna"
            st.caption(
                f"Modelo: {metadata['model']} · Herramientas: {tools} · "
                f"Latencia: {metadata['latency_seconds']:.2f} s"
            )

typed_prompt = st.chat_input(
    "Pregunta sobre Renta Joven, Bienestar Contigo o la Política de Bienestar…",
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
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌿"):
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
                if response.model_invoked:
                    st.caption(
                        f"Modelo: {response.model_id} · Herramientas: {tools_text} · "
                        f"Latencia: {response.latency_seconds:.2f} s"
                    )
                else:
                    st.caption(
                        "Filtro local de alcance · Modelo no invocado · "
                        "Tokens consumidos: 0"
                    )
                metadata = {
                    "model": response.model_id,
                    "tools": response.tools,
                    "latency_seconds": response.latency_seconds,
                    "model_invoked": response.model_invoked,
                }
                st.session_state.messages.append(
                    {"role": "assistant", "content": response.text, "metadata": metadata}
                )
                st.session_state.metrics.append(
                    {
                        "modelo": response.model_id if response.model_invoked else "no invocado",
                        "latencia_s": round(response.latency_seconds, 3),
                        "herramientas": tools_text,
                        "estado": "correcto" if response.model_invoked else "filtrado local",
                    }
                )

if st.session_state.metrics:
    with st.expander("Métricas de esta sesión"):
        st.dataframe(st.session_state.metrics, width="stretch", hide_index=True)
