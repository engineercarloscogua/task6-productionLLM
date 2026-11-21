from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from langchain_core.documents import Document


_SPANISH_STOPWORDS = {
    "a", "al", "como", "con", "cual", "cuales", "cuando", "de", "del",
    "donde", "e", "el", "en", "es", "la", "las", "lo", "los", "o",
    "para", "por", "que", "quien", "quienes", "se", "sin", "son", "su",
    "sus", "u", "un", "una", "unas", "unos", "y",
}
_COMMON_QUERY_TYPOS = {
    "beinestar": "bienestar",
    "bienstar": "bienestar",
    "contgio": "contigo",
}


@dataclass(frozen=True, slots=True)
class SearchResult:
    document: Document
    score: float


class KnowledgeBase:
    """Small deterministic TF-IDF knowledge base for the academic RAG demo."""

    def __init__(self, documents: list[Document] | None = None) -> None:
        self.documents = list(documents or [])
        tokenized = [self._terms(document.page_content) for document in self.documents]
        document_frequency = Counter(
            term for terms in tokenized for term in set(terms)
        )
        total_documents = len(self.documents)
        self.idf = {
            term: math.log((1 + total_documents) / (1 + frequency)) + 1
            for term, frequency in document_frequency.items()
        }
        self.document_vectors = [self._vector(terms) for terms in tokenized]

    @staticmethod
    def _terms(text: str) -> list[str]:
        normalized = unicodedata.normalize("NFKD", text.casefold())
        ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
        ascii_text = re.sub(r"\bbien[-\s]*estar\b", "bienestar", ascii_text)
        words = [
            _COMMON_QUERY_TYPOS.get(word, word)
            for word in re.findall(r"[a-z0-9]+", ascii_text)
            if word not in _SPANISH_STOPWORDS
        ]
        bigrams = [f"{left}_{right}" for left, right in zip(words, words[1:])]
        return [*words, *bigrams]

    def _vector(self, terms: list[str]) -> dict[str, float]:
        counts = Counter(terms)
        total = max(len(terms), 1)
        return {
            term: (count / total) * self.idf.get(term, 0.0)
            for term, count in counts.items()
            if term in self.idf
        }

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        common = set(left).intersection(right)
        numerator = sum(left[term] * right[term] for term in common)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)

    def search(self, query: str, k: int = 2) -> list[SearchResult]:
        if not query.strip():
            return []
        query_vector = self._vector(self._terms(query))
        scores = [
            self._cosine(query_vector, document_vector)
            for document_vector in self.document_vectors
        ]
        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )
        return [
            SearchResult(document=self.documents[index], score=float(scores[index]))
            for index in ranked_indexes[:k]
            if scores[index] > 0
        ]

    def context(self, query: str, k: int = 2, max_chars: int = 6000) -> str:
        results = self.search(query, k=k)
        if not results:
            return "No se encontraron documentos relacionados con la pregunta."
        contexts = []
        for result in results:
            page = result.document.metadata.get("pagina")
            location = f", página {page}" if page else ""
            contexts.append(
                f"Fuente: {result.document.metadata['fuente']}{location}\n"
                f"Contenido: {result.document.page_content}\n"
                f"Similitud TF-IDF: {result.score:.3f}"
            )
        return "\n\n".join(contexts)[:max_chars]
