from __future__ import annotations

import os
from uuid import uuid4

import streamlit as st
from openai import AuthenticationError as OpenAIAuthenticationError
from openai import RateLimitError as OpenAIRateLimitError

from src.models import (
    DEFAULT_OPENAI_MODEL_ID,
    ModelOption,
    default_model_index,
    fetch_free_tool_models,
    openai_tool_models,
)
from src.agent import AgentResponse, build_agent, run_agent
from src.guardrails import SCOPE_MESSAGE, classify_scope
from src.openrouter_model import OpenRouterRateLimitError
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


def read_configured_api_key(key_name: str = "OPENROUTER_API_KEY") -> str:
    """Read the key from Streamlit secrets or the process environment."""
    try:
        secret = st.secrets.get(key_name, "")
    except (FileNotFoundError, AttributeError):
        secret = ""
    return str(secret or os.getenv(key_name, "")).strip()


def initialize_session() -> None:
    defaults = {
        "messages": [],
        "metrics": [],
        "thread_id": str(uuid4()),
        "active_model": None,
        "agent": None,
        "temporary_openrouter_api_key": "",
        "temporary_openai_api_key": "",
        "document_context_active": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.metrics = []
    st.session_state.thread_id = str(uuid4())
    st.session_state.agent = None
    st.session_state.document_context_active = False


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
    provider = st.selectbox(
        "Proveedor de API",
        options=["openrouter", "openai"],
        format_func=lambda value: (
            "OpenRouter · modelos gratuitos"
            if value == "openrouter"
            else "OpenAI · cuenta de pago"
        ),
        key="provider_selector",
        help=(
            "OpenRouter usa la cuota gratuita. OpenAI puede generar cargos y solo "
            "se utiliza cuando lo seleccionas manualmente."
        ),
    )
    key_name = "OPENAI_API_KEY" if provider == "openai" else "OPENROUTER_API_KEY"
    provider_name = "OpenAI" if provider == "openai" else "OpenRouter"
    temporary_key_name = f"temporary_{provider}_api_key"
    configured_key = read_configured_api_key(key_name)
    if configured_key:
        api_key = configured_key
        st.success(f"API de {provider_name} configurada en el servidor.")
    else:
        st.caption(
            "Para una prueba local puedes introducir la clave durante esta sesión. "
            "No se guarda en archivos ni se muestra nuevamente."
        )
        st.text_input(
            key_name,
            type="password",
            key=temporary_key_name,
            placeholder="sk-…",
        )
        api_key = st.session_state[temporary_key_name].strip()

    if provider == "openrouter":
        try:
            model_options = load_models()
        except Exception as error:
            st.error(f"No fue posible consultar el catálogo: {error}")
            model_options = [ModelOption.free_router()]
        model_index = default_model_index(model_options)
        model_help = (
            "La lista se obtiene de OpenRouter y se filtra por precio gratuito, "
            "salida de texto y soporte para herramientas."
        )
    else:
        model_options = openai_tool_models()
        model_index = next(
            (
                index
                for index, option in enumerate(model_options)
                if option.id == DEFAULT_OPENAI_MODEL_ID
            ),
            0,
        )
        model_help = (
            "Estos modelos usan la API de pago de OpenAI. GPT-6 Luna se selecciona "
            "por defecto para reducir costos."
        )

    selected = st.selectbox(
        "Modelo con herramientas",
        options=model_options,
        index=model_index,
        format_func=model_label,
        key=f"model_selector_{provider}",
        help=model_help,
    )
    st.caption(f"ID: `{selected.id}`")
    if provider == "openai":
        st.warning("OpenAI es un servicio de pago. Cada consulta puede generar cargos.")

    if provider == "openrouter" and st.button("Actualizar modelos", width="stretch"):
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
        "OpenRouter tiene límites gratuitos; OpenAI puede generar cargos. Cambiar "
        "de proveedor o modelo inicia una conversación nueva."
    )

active_model = f"{provider}:{selected.id}"
if st.session_state.active_model != active_model:
    reset_conversation()
    st.session_state.active_model = active_model

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
            if metadata.get("model_invoked", True):
                provider_caption = metadata.get("provider")
                provider_text = (
                    f"Proveedor: {provider_caption} · " if provider_caption else ""
                )
                st.caption(
                    f"{provider_text}Modelo: {metadata['model']} · Herramientas: {tools} · "
                    f"Latencia: {metadata['latency_seconds']:.2f} s"
                )
            else:
                st.caption(
                    "Filtro local de alcance · Modelo no invocado · "
                    "Tokens consumidos: 0"
                )

typed_prompt = st.chat_input(
    "Pregunta sobre Renta Joven, Bienestar Contigo o la Política de Bienestar…",
    disabled=not bool(api_key),
)
prompt = suggested_prompt or typed_prompt

if not api_key:
    st.warning(
        f"Configura `{key_name}` en `.streamlit/secrets.toml`, como variable de "
        "entorno o temporalmente en la barra lateral para habilitar el chat."
    )

if prompt and api_key:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    decision = classify_scope(
        prompt,
        has_document_context=st.session_state.document_context_active,
    )

    with st.chat_message("assistant", avatar="🌿"):
        if not decision.allowed:
            st.markdown(SCOPE_MESSAGE)
            st.caption(
                "Filtro local de alcance · Modelo no invocado · "
                "Tokens consumidos: 0"
            )
            metadata = {
                "provider": provider_name,
                "model": "no invocado",
                "tools": [],
                "latency_seconds": 0.0,
                "model_invoked": False,
                "filter_reason": decision.reason,
            }
            st.session_state.messages.append(
                {"role": "assistant", "content": SCOPE_MESSAGE, "metadata": metadata}
            )
            st.session_state.metrics.append(
                {
                    "modelo": "no invocado",
                    "latencia_s": 0.0,
                    "herramientas": "ninguna",
                    "estado": f"filtrado local: {decision.reason}",
                }
            )
        else:
            st.session_state.document_context_active = True
            with st.spinner(f"Consultando {selected.name}…"):
                try:
                    if st.session_state.agent is None:
                        st.session_state.agent = build_agent(
                            api_key=api_key,
                            model_id=selected.id,
                            provider=provider,
                        )
                    response: AgentResponse = run_agent(
                        agent=st.session_state.agent,
                        message=prompt,
                        thread_id=st.session_state.thread_id,
                        model_id=selected.id,
                    )
                except OpenRouterRateLimitError as error:
                    limit_message = (
                        f"**Cuota diaria de OpenRouter agotada**\n\n{error}\n\n"
                        "Puedes seleccionar OpenAI en la barra lateral; recuerda que "
                        "esa API es de pago."
                    )
                    st.warning(limit_message)
                    metadata = {
                        "provider": "OpenRouter",
                        "model": selected.id,
                        "tools": ["consultar_documentos"],
                        "latency_seconds": 0.0,
                        "model_invoked": True,
                        "provider_status": "rate_limit",
                    }
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": limit_message,
                            "metadata": metadata,
                        }
                    )
                    st.session_state.metrics.append(
                        {
                            "modelo": selected.id,
                            "latencia_s": 0.0,
                            "herramientas": "consultar_documentos",
                            "estado": "cuota diaria agotada",
                        }
                    )
                except OpenAIRateLimitError:
                    limit_message = (
                        "**OpenAI rechazó la solicitud por límite o saldo**\n\n"
                        "Revisa el uso, presupuesto y facturación de tu proyecto en "
                        "OpenAI. No se realizó ningún reintento automático."
                    )
                    st.warning(limit_message)
                    metadata = {
                        "provider": "OpenAI",
                        "model": selected.id,
                        "tools": ["consultar_documentos"],
                        "latency_seconds": 0.0,
                        "model_invoked": True,
                        "provider_status": "rate_limit",
                    }
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": limit_message,
                            "metadata": metadata,
                        }
                    )
                    st.session_state.metrics.append(
                        {
                            "modelo": selected.id,
                            "latencia_s": 0.0,
                            "herramientas": "consultar_documentos",
                            "estado": "límite o saldo de OpenAI",
                        }
                    )
                except OpenAIAuthenticationError:
                    st.error(
                        "OpenAI rechazó la clave. Verifica `OPENAI_API_KEY` en los "
                        "secretos del servidor."
                    )
                except Exception as error:
                    st.error(
                        "La consulta no pudo completarse. Revisa la clave, el límite del modelo "
                        f"o selecciona otro modelo. Detalle: {error}"
                    )
                else:
                    model_invoked = getattr(response, "model_invoked", True)
                    st.markdown(response.text)
                    tools_text = ", ".join(response.tools) or "ninguna"
                    if model_invoked:
                        st.caption(
                            f"Proveedor: {provider_name} · Modelo: {response.model_id} · "
                            f"Herramientas: {tools_text} · Latencia: "
                            f"{response.latency_seconds:.2f} s"
                        )
                    else:
                        st.caption(
                            "Filtro local de alcance · Modelo no invocado · "
                            "Tokens consumidos: 0"
                        )
                    metadata = {
                        "provider": provider_name,
                        "model": response.model_id,
                        "tools": response.tools,
                        "latency_seconds": response.latency_seconds,
                        "model_invoked": model_invoked,
                    }
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response.text, "metadata": metadata}
                    )
                    st.session_state.metrics.append(
                        {
                            "modelo": response.model_id if model_invoked else "no invocado",
                            "latencia_s": round(response.latency_seconds, 3),
                            "herramientas": tools_text,
                            "estado": "correcto" if model_invoked else "filtrado local",
                        }
                    )

if st.session_state.metrics:
    with st.expander("Métricas de esta sesión"):
        st.dataframe(st.session_state.metrics, width="stretch", hide_index=True)
