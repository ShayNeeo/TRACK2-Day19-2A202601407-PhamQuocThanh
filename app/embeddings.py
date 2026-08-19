"""Pluggable embedding backends, selected by the EMBEDDING_BACKEND env var.

Why this exists: `.env.example` has always advertised
`EMBEDDING_BACKEND=fastembed | bge-m3 | openai`, setup-docker.sh flips it to
`bge-m3` and prints "bge-m3 embeddings", and the README sells bge-m3 as the
reason to take the Docker path -- but nothing ever read the variable. Every
path silently used BAAI/bge-small-en-v1.5, an ENGLISH model, which is exactly
why NB2 shows weak recall on Vietnamese paraphrases. Students were promised an
upgrade that never happened.

The default is unchanged (fastembed / bge-small / 384-dim), so the lite path
and every rubric threshold behave exactly as before. The other backends are
opt-in via the environment.

    EMBEDDING_BACKEND=fastembed     BAAI/bge-small-en-v1.5     384   (default, lite)
    EMBEDDING_BACKEND=multilingual  intfloat/multilingual-e5-large 1024 (fastembed)
    EMBEDDING_BACKEND=bge-m3        BAAI/bge-m3                1024  (sentence-transformers)
    EMBEDDING_BACKEND=openai        text-embedding-3-small     1536  (needs OPENAI_API_KEY)
"""
from __future__ import annotations

import os
import itertools
import time
from dataclasses import dataclass
from typing import Iterable, Iterator

import httpx
import numpy as np
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BACKEND = "fastembed"


@dataclass(frozen=True)
class BackendSpec:
    model: str
    dim: int
    provider: str       # fastembed | sentence-transformers | openai | gemini
    note: str = ""


BACKENDS: dict[str, BackendSpec] = {
    "fastembed": BackendSpec("BAAI/bge-small-en-v1.5", 384, "fastembed",
                             "English-focused; weak on Vietnamese paraphrase (that is the NB2 lesson)"),
    "multilingual": BackendSpec("intfloat/multilingual-e5-large", 1024, "fastembed",
                                "Multilingual, no extra dependency, ~2.2 GB download"),
    "bge-m3": BackendSpec("BAAI/bge-m3", 1024, "sentence-transformers",
                          "Multilingual; needs sentence-transformers (requirements-full.txt)"),
    "openai": BackendSpec("text-embedding-3-small", 1536, "openai",
                          "Needs OPENAI_API_KEY; costs money"),
    "gemini": BackendSpec("models/gemini-embedding-2", 3072, "gemini",
                          "Google Gemini Embedding 2 via AI Studio / Gemini API"),
    "gemini-embedding-2": BackendSpec("models/gemini-embedding-2", 3072, "gemini",
                                      "Google Gemini Embedding 2 via AI Studio"),
    "aistudio": BackendSpec("models/gemini-embedding-2", 3072, "gemini",
                            "Google Gemini Embedding 2 via AI Studio"),
}


import hashlib
import sqlite3
from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / ".cache_embeddings"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _CACHE_DIR / "gemini_cache.db"


class GeminiEmbeddingClient:
    """Client for Google AI Studio / Gemini Embedding API with persistent caching & key rotation."""

    def __init__(self, model: str = "models/gemini-embedding-2") -> None:
        self.model = model if model.startswith("models/") else f"models/{model}"
        keys: list[str] = []
        if os.getenv("GOOGLE_AI_API_KEYS"):
            keys.extend([k.strip() for k in os.getenv("GOOGLE_AI_API_KEYS", "").split(",") if k.strip()])
        for env_var in ["AI_STUDIO_API_KEY", "GEMINI_API_KEY", "GOOGLE_AI_API_KEY", "GOOGLE_API_KEY"]:
            val = os.getenv(env_var)
            if val and val.strip() not in keys:
                keys.append(val.strip())
        if not keys:
            raise RuntimeError(
                "Gemini embedding backend requires GEMINI_API_KEY, AI_STUDIO_API_KEY, or GOOGLE_AI_API_KEY in .env"
            )
        self.keys = keys
        self._key_cycle = itertools.cycle(keys)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache (hash TEXT PRIMARY KEY, model TEXT, vector BLOB)"
            )

    def _get_cached(self, hashes: list[str]) -> dict[str, np.ndarray]:
        found: dict[str, np.ndarray] = {}
        if not hashes:
            return found
        with sqlite3.connect(_DB_PATH) as conn:
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in hashes)
            cur.execute(f"SELECT hash, vector FROM cache WHERE model = ? AND hash IN ({placeholders})", [self.model, *hashes])
            for h, v_blob in cur.fetchall():
                found[h] = np.frombuffer(v_blob, dtype=np.float32)
        return found

    def _save_cached(self, items: list[tuple[str, np.ndarray]]) -> None:
        if not items:
            return
        with sqlite3.connect(_DB_PATH) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO cache (hash, model, vector) VALUES (?, ?, ?)",
                [(h, self.model, v.astype(np.float32).tobytes()) for h, v in items]
            )

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        if not texts:
            return []

        hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
        cached_map = self._get_cached(hashes)

        # Identify missing texts
        missing_indices = [i for i, h in enumerate(hashes) if h not in cached_map]
        
        if missing_indices:
            BATCH_SIZE = 25
            for chunk_start in range(0, len(missing_indices), BATCH_SIZE):
                chunk_idx = missing_indices[chunk_start:chunk_start + BATCH_SIZE]
                chunk_texts = [texts[i] for i in chunk_idx]
                chunk_hashes = [hashes[i] for i in chunk_idx]

                max_retries = len(self.keys) * 3
                backoff = 1.0
                last_err = None
                for attempt in range(max_retries):
                    key = next(self._key_cycle)
                    url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:batchEmbedContents?key={key}"
                    payload = {
                        "requests": [{"model": self.model, "content": {"parts": [{"text": t}]}} for t in chunk_texts]
                    }
                    try:
                        with httpx.Client(timeout=60.0) as client:
                            resp = client.post(url, json=payload)
                            if resp.status_code == 200:
                                data = resp.json()
                                items_to_save = []
                                for idx, item in zip(chunk_idx, data.get("embeddings", [])):
                                    vec = np.asarray(item["values"], dtype=np.float32)
                                    cached_map[hashes[idx]] = vec
                                    items_to_save.append((hashes[idx], vec))
                                self._save_cached(items_to_save)
                                break
                            elif resp.status_code == 429:
                                time.sleep(min(backoff, 4.0))
                                backoff = min(backoff * 1.5, 8.0)
                            else:
                                last_err = f"Status {resp.status_code}: {resp.text}"
                                time.sleep(1.0)
                    except Exception as e:
                        last_err = str(e)
                        time.sleep(1.0)
                else:
                    raise RuntimeError(f"Gemini API batch failed after {max_retries} attempts: {last_err}")

        return [cached_map[h] for h in hashes]


class Embedder:
    """Uniform `.embed(list[str]) -> Iterator[np.ndarray]`, matching fastembed."""

    def __init__(self, backend: str | None = None) -> None:
        name = (backend or os.getenv("EMBEDDING_BACKEND") or os.getenv("EMBEDDING_MODEL") or DEFAULT_BACKEND).strip().lower()
        if name in ("gemini-embedding-2", "gemini-embedding-001", "models/gemini-embedding-2", "models/gemini-embedding-001"):
            name = "gemini"
        if name not in BACKENDS:
            raise ValueError(
                f"Unknown EMBEDDING_BACKEND={name!r}. "
                f"Valid: {', '.join(sorted(BACKENDS))}"
            )
        self.backend = name
        self.spec = BACKENDS[name]
        self._impl = None

    # dimension is a property of the chosen model, never a hard-coded constant
    @property
    def dim(self) -> int:
        return self.spec.dim

    @property
    def model_name(self) -> str:
        return self.spec.model

    def _load(self):
        if self._impl is not None:
            return self._impl
        p = self.spec.provider
        if p == "fastembed":
            from fastembed import TextEmbedding
            self._impl = TextEmbedding(model_name=self.spec.model)
        elif p == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:                       # pragma: no cover
                raise ImportError(
                    f"EMBEDDING_BACKEND={self.backend} needs sentence-transformers.\n"
                    "It ships with the Docker path:  pip install -r requirements-full.txt"
                ) from exc
            self._impl = SentenceTransformer(self.spec.model)
        elif p == "openai":
            try:
                from openai import OpenAI
            except ImportError as exc:                       # pragma: no cover
                raise ImportError(
                    "EMBEDDING_BACKEND=openai needs the openai package "
                    "(requirements-full.txt) and OPENAI_API_KEY."
                ) from exc
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("EMBEDDING_BACKEND=openai but OPENAI_API_KEY is unset.")
            self._impl = OpenAI()
        elif p == "gemini":
            self._impl = GeminiEmbeddingClient(model=self.spec.model)
        return self._impl

    def embed(self, texts: Iterable[str]) -> Iterator[np.ndarray]:
        texts = list(texts)
        impl = self._load()
        p = self.spec.provider
        if p == "fastembed":
            yield from impl.embed(texts)
        elif p == "sentence-transformers":
            for v in impl.encode(texts, normalize_embeddings=True):
                yield np.asarray(v, dtype=np.float32)
        elif p == "openai":
            resp = impl.embeddings.create(model=self.spec.model, input=texts)
            for item in resp.data:
                yield np.asarray(item.embedding, dtype=np.float32)
        elif p == "gemini":
            results = impl.embed_batch(texts)
            yield from results


def describe() -> str:
    e = Embedder()
    return f"{e.backend} -> {e.model_name} ({e.dim}d) — {e.spec.note}"
