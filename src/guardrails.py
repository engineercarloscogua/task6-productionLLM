from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


MAX_QUERY_CHARS = 600
MAX_QUERY_WORDS = 100

SCOPE_MESSAGE = (
    "Solo puedo responder preguntas informativas sobre los programas "
    "socioeconómicos incluidos en los documentos cargados. No redacto PQR, "
    "cartas ni correos; tampoco desarrollo código ni creo imágenes, gráficas, "
    "audio, video u otros contenidos. Formula una pregunta concreta sobre el corpus "
    "documental. Esta respuesta se generó localmente y no consumió tokens."
)


@dataclass(frozen=True, slots=True)
class ScopeDecision:
    allowed: bool
    reason: str


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(
        char
        for char in decomposed
        if not unicodedata.combining(char) and unicodedata.category(char) != "Cf"
    )
    compact = re.sub(r"\s+", " ", plain).strip()
    return re.sub(r"^[^a-z0-9]+", "", compact)


_CREATION_ACTIONS = (
    r"redact(?:a|ar|ame)", r"escrib(?:e|ir|eme)", r"cre(?:a|ar|ame)",
    r"gener(?:a|ar|ame)", r"elabor(?:a|ar|ame)", r"prepar(?:a|ar|ame)",
    r"disen(?:a|ar|ame)", r"haz(?:me)?",
    r"ayudame a (?:hacer|redactar|escribir|crear|generar|elaborar)",
)
_CREATED_ARTIFACTS = (
    r"pqr(?:s)?", r"peticion", r"queja", r"reclamo", r"carta", r"correo",
    r"e-?mail", r"mensaje", r"oficio", r"formulario", r"ensayo", r"informe",
    r"presentacion", r"discurso", r"hoja de vida", r"curriculum", r"poema",
    r"historia", r"guion", r"publicacion", r"post", r"codigo", r"script",
    r"programa informatico", r"imagen(?:es)?", r"grafica(?:s)?", r"grafico(?:s)?",
    r"diagrama(?:s)?", r"audio(?:s)?", r"video(?:s)?", r"animacion(?:es)?",
)
_CREATION_PATTERN = re.compile(
    rf"(?:{'|'.join(_CREATION_ACTIONS)}).{{0,45}}(?:{'|'.join(_CREATED_ARTIFACTS)})"
    rf"|(?:{'|'.join(_CREATED_ARTIFACTS)}).{{0,45}}(?:{'|'.join(_CREATION_ACTIONS)})"
)
_RETRIEVAL_PATTERN = re.compile(
    r"\b(?:que|cual(?:es)?|como|cuando|donde|quien(?:es)?|por que|cuanto|"
    r"informacion|requisito(?:s)?|condicion(?:es)?|beneficio(?:s)?|"
    r"explica(?:me)?|resume(?:me)?|consulta|busca|dime|puedo|podria|aplicar|"
    r"acceder|pertenecer|postular(?:me)?|elegible|compatibles?|simultaneamente|"
    r"ambos)\b"
)
_SOURCE_SCOPE_PATTERN = re.compile(
    r"\b(?:renta joven|bien[- ]?estar(?: universitario| contigo| contgio)?|programa(?:s)?|"
    r"estudiante(?:s)?|joven(?:es)?|beneficiari[oa]s?|matricula|educacion superior|"
    r"permanencia|transporte|computador(?:es)?|prestamo|convocatoria|inscripcion|"
    r"institucion(?:es)?|universidad(?:es)?|pago(?:s)?|ciclo(?:s)?|incentivo(?:s)?|"
    r"corresponsabilidad(?:es)?|prosperidad social|documento(?:s)?|archivo(?:s)?|"
    r"pagina(?:s)?|pdf|corpus|sisben|cuenta bancaria|bancari[oa]s?|dinero|pagar|"
    r"paguen|nota(?:s)?|materia(?:s)?|semestre|carrera|voluntariado|curso(?:s)?|"
    r"capacitacion(?:es)?|alimentacion|victima(?:s)?|conflicto armado|indigena(?:s)?|"
    r"promedio|credito(?:s)?|carne estudiantil|bono(?:s)?|supermercado(?:s)?|"
    r"seleccionad[oa]s?|cupo(?:s)?|reclamacion|oficina|calificacion(?:es)?|"
    r"actividad(?:es)?|apoyo(?:s)?|beneficio(?:s)?)\b"
)
_DIRECT_SOURCE_LOOKUP_PATTERN = re.compile(
    r"^(?:(?:informacion|consulta|pregunto|pregunta) (?:sobre|por|de) )?"
    r"(?:el )?(?:programa )?(?:renta joven|bien[- ]?estar (?:contigo|contgio)|"
    r"politica (?:integral )?de bien[- ]?estar universitario)$"
)
_FORBIDDEN_CAPABILITY_PATTERN = re.compile(
    r"\b(?:codigo|codificar|programacion|programar|desarrollo (?:web|de software)|"
    r"python|javascript|typescript|java|html|css|sql|api|imagen(?:es)?|grafica(?:s)?|"
    r"grafico(?:s)?|diagrama(?:s)?|audio(?:s)?|video(?:s)?|animacion(?:es)?)\b"
)
_CALCULATION_PATTERN = re.compile(
    r"\b(?:calcula(?:r|me)?|multiplica(?:r)?|suma(?:r)?|cuanto gasto|"
    r"viajes? (?:diarios?|por dia))\b"
)
_DOCUMENT_FOLLOW_UP_PATTERN = re.compile(
    r"\b(?:requisito(?:s)?|condicion(?:es)?|beneficio(?:s)?|fecha(?:s)?|plazo(?:s)?|"
    r"pago(?:s)?|incentivo(?:s)?|renov(?:ar|acion)|inscrib(?:ir|irse)|"
    r"convocatoria|cobertura|monto|documento(?:s)?|fuente(?:s)?|pagina(?:s)?)\b"
)
_PROMPT_INJECTION_PATTERN = re.compile(
    r"(?:ignora|omite|desobedece|olvida|anula|reemplaza|bypassea|bypass|ignore|"
    r"disregard|forget|override).{0,60}(?:instruccion(?:es)?|regla(?:s)?|prompt|"
    r"mensaje(?:s)?|restriccion(?:es)?|previous instructions?|system message)|"
    r"(?:prompt (?:del )?sistema|system prompt|developer message|mensaje (?:del )?"
    r"sistema|instrucciones? (?:internas?|ocultas?))|"
    r"(?:ahora eres|actua como|finge ser|simula ser|modo (?:desarrollador|admin|"
    r"administrador)|jailbreak|dan mode)|"
    r"(?:no uses|evita usar|sin usar|no consultes).{0,40}(?:herramienta(?:s)?|"
    r"documento(?:s)?|corpus|fuente(?:s)?)"
)
_SECRET_EXTRACTION_PATTERN = re.compile(
    r"\b(?:api[ _-]?key|secrets?\.toml|variable(?:s)? de entorno|environment "
    r"variables?|credencial(?:es)?|clave secreta|token secreto|password|contrasena)\b"
)
_ENCODING_BYPASS_PATTERN = re.compile(
    r"\b(?:base ?64|rot ?13|hexadecimal|decodifica|decode|codifica|encode|"
    r"unicode|leet(?:speak)?)\b"
)
_FABRICATION_PATTERN = re.compile(
    r"(?:aunque no|si no).{0,35}(?:aparezca|exista|encuentre)|"
    r"\b(?:inventa|fabrica|simula|citas? falsas?|fuentes? falsas?|sin fuentes?|"
    r"sin citar)\b"
)
_MASS_EXTRACTION_PATTERN = re.compile(
    r"(?:copia|muestra|imprime|extrae|devuelve|transcribe|vuelca|dump).{0,60}"
    r"(?:todos? los documentos?|documentos? completos?|corpus completo|pagina por pagina)|"
    r"(?:todos? los documentos?|corpus completo).{0,60}(?:copia|completo|pagina por pagina)"
)


def contains_prompt_injection(text: str) -> bool:
    """Detecta instrucciones potencialmente hostiles en entradas o documentos."""
    normalized = _normalize(text)
    security_text = normalized.translate(str.maketrans("013457", "oieast"))
    return bool(
        _PROMPT_INJECTION_PATTERN.search(security_text)
        or _SECRET_EXTRACTION_PATTERN.search(security_text)
        or _ENCODING_BYPASS_PATTERN.search(security_text)
    )


def classify_scope(message: str, has_document_context: bool = False) -> ScopeDecision:
    """Decide localmente si una entrada merece invocar al modelo remoto."""
    normalized = _normalize(message)
    security_text = normalized.translate(str.maketrans("013457", "oieast"))
    if not normalized:
        return ScopeDecision(False, "empty")
    if len(message) > MAX_QUERY_CHARS or len(normalized.split()) > MAX_QUERY_WORDS:
        return ScopeDecision(False, "input_too_large")
    if message.count("\n") > 5 or any(ord(char) < 32 and char not in "\n\t\r" for char in message):
        return ScopeDecision(False, "suspicious_format")
    if _PROMPT_INJECTION_PATTERN.search(security_text):
        return ScopeDecision(False, "prompt_injection")
    if _SECRET_EXTRACTION_PATTERN.search(security_text):
        return ScopeDecision(False, "secret_extraction")
    if _ENCODING_BYPASS_PATTERN.search(security_text):
        return ScopeDecision(False, "encoded_bypass")
    if _FABRICATION_PATTERN.search(security_text):
        return ScopeDecision(False, "fabrication_request")
    if _MASS_EXTRACTION_PATTERN.search(security_text):
        return ScopeDecision(False, "mass_extraction")
    if _FORBIDDEN_CAPABILITY_PATTERN.search(normalized):
        return ScopeDecision(False, "forbidden_capability")
    if _CREATION_PATTERN.search(normalized):
        return ScopeDecision(False, "content_creation")
    if _CALCULATION_PATTERN.search(normalized):
        return ScopeDecision(False, "calculation")
    direct_source_lookup = bool(
        _DIRECT_SOURCE_LOOKUP_PATTERN.fullmatch(normalized.strip(" ?.!,;:"))
    )
    if direct_source_lookup:
        return ScopeDecision(True, "document_lookup")
    explicit_question = "?" in normalized or "¿" in message
    if not _RETRIEVAL_PATTERN.search(normalized) and not explicit_question:
        return ScopeDecision(False, "not_a_knowledge_question")
    short_follow_up = (
        has_document_context
        and len(normalized.split()) <= 12
        and re.match(r"^(?:y|tambien|ademas|eso|esa|ese|este|esta|cuando|como|cual)", normalized)
        and _DOCUMENT_FOLLOW_UP_PATTERN.search(normalized)
    )
    if _SOURCE_SCOPE_PATTERN.search(normalized) or short_follow_up:
        return ScopeDecision(True, "document_question")
    return ScopeDecision(False, "outside_source_scope")
