"""Hybrid Memory Agent (Bonus Challenge).

Combines Episodic Memory (Qdrant Vector Store) with User Profile & Activity
(Feast Feature Store) to assemble personalized, context-aware prompts for AI assistants.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from feast import FeatureStore
import numpy as np
from qdrant_client import QdrantClient, models

from app.embeddings import Embedder

MEMORY_COLLECTION = "user_episodic_memory"


@dataclass
class MemoryChunk:
    chunk_id: str
    user_id: str
    text: str
    timestamp: float = field(default_factory=time.time)


class HybridMemoryAgent:
    """Agent that integrates episodic vector recall with Feast feature store personalization."""

    def __init__(
        self,
        repo_path: str | Path | None = None,
        client: QdrantClient | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.feast_dir = Path(repo_path) if repo_path else self.repo_root / "app" / "feast_repo"
        self.client = client or QdrantClient(":memory:")
        self.embedder = embedder or Embedder()
        self.fs = FeatureStore(repo_path=str(self.feast_dir))
        self.memories: list[MemoryChunk] = []
        self._next_id = 1
        self._init_collection()

    def _init_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if MEMORY_COLLECTION in collections:
            self.client.delete_collection(MEMORY_COLLECTION)
        self.client.create_collection(
            collection_name=MEMORY_COLLECTION,
            vectors_config=models.VectorParams(size=self.embedder.dim, distance=models.Distance.COSINE),
        )

    def _chunk_text(self, text: str, chunk_size: int = 250, overlap: int = 50) -> list[str]:
        """Simple sliding window chunker respecting sentence boundaries."""
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        chunks: list[str] = []
        cur_chunk: list[str] = []
        cur_len = 0
        for sent in sentences:
            sent_len = len(sent.split())
            if cur_len + sent_len > chunk_size and cur_chunk:
                chunks.append(". ".join(cur_chunk) + ".")
                cur_chunk = cur_chunk[-1:]
                cur_len = len(cur_chunk[0].split())
            cur_chunk.append(sent)
            cur_len += sent_len
        if cur_chunk:
            chunks.append(". ".join(cur_chunk) + ("." if not cur_chunk[-1].endswith(".") else ""))
        return chunks if chunks else [text]

    def remember(self, text: str, user_id: str = "u_001") -> list[str]:
        """Add new episodic memories for this user into Qdrant."""
        chunks = self._chunk_text(text)
        chunk_ids: list[str] = []
        points: list[models.PointStruct] = []

        embeddings = list(self.embedder.embed(chunks))
        now = time.time()

        for chunk_str, vec in zip(chunks, embeddings):
            c_id = f"mem_{self._next_id:05d}"
            self._next_id += 1
            chunk_ids.append(c_id)
            chunk_obj = MemoryChunk(chunk_id=c_id, user_id=user_id, text=chunk_str, timestamp=now)
            self.memories.append(chunk_obj)

            points.append(
                models.PointStruct(
                    id=self._next_id - 1,
                    vector=vec.tolist(),
                    payload={"chunk_id": c_id, "user_id": user_id, "text": chunk_str, "ts": now},
                )
            )

        self.client.upsert(collection_name=MEMORY_COLLECTION, points=points)
        return chunk_ids

    def recall(self, query: str, user_id: str = "u_001", top_k: int = 3) -> dict[str, Any]:
        """Retrieve relevant episodic memories + user profile features and assemble context."""
        # 1. Online Feature Store Lookup (Feast)
        features: dict[str, Any] = {}
        try:
            feat_dict = self.fs.get_online_features(
                features=[
                    "user_profile_features:reading_speed_wpm",
                    "user_profile_features:preferred_language",
                    "user_profile_features:topic_affinity",
                    "query_velocity_features:queries_last_hour",
                    "query_velocity_features:distinct_topics_24h",
                ],
                entity_rows=[{"user_id": user_id}],
            ).to_dict()
            features = {k: v[0] for k, v in feat_dict.items()}
        except Exception:
            features = {
                "user_profile_features:reading_speed_wpm": 220,
                "user_profile_features:preferred_language": "vi",
                "user_profile_features:topic_affinity": "cloud",
                "query_velocity_features:queries_last_hour": 5,
                "query_velocity_features:distinct_topics_24h": 3,
            }

        # 2. Filtered Vector Retrieval from Qdrant
        q_vec = list(self.embedder.embed([query]))[0].tolist()
        user_filter = models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        )
        res = self.client.query_points(
            collection_name=MEMORY_COLLECTION,
            query=q_vec,
            query_filter=user_filter,
            limit=top_k,
        )

        top_memories = [p.payload["text"] for p in res.points]

        # 3. Context Assembly
        pref_lang = features.get("user_profile_features:preferred_language", "vi")
        speed = features.get("user_profile_features:reading_speed_wpm", 200)
        affinity = features.get("user_profile_features:topic_affinity", "general")
        q_1h = features.get("query_velocity_features:queries_last_hour", 0)

        context_lines = [
            "=== USER PROFILE & STATE ===",
            f"User ID: {user_id} | Language: {pref_lang} | Reading Speed: {speed} wpm",
            f"Topic Affinity: {affinity} | Recent Query Velocity (1h): {q_1h} queries",
            "",
            "=== RELEVANT EPISODIC MEMORIES ===",
        ]
        if top_memories:
            for idx, mem in enumerate(top_memories, 1):
                context_lines.append(f"[{idx}] {mem}")
        else:
            context_lines.append("(No relevant personal memory found)")

        context_lines.extend(["", "=== CURRENT QUERY ===", query])
        assembled_prompt = "\n".join(context_lines)

        return {
            "user_id": user_id,
            "query": query,
            "profile_features": features,
            "retrieved_memories": top_memories,
            "assembled_prompt": assembled_prompt,
        }
