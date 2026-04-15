from app.config import RetrievalWeights
from app.retrieval.normalizer import min_max_normalize
from app.schemas.models import QueryVariant, RetrievalResult


class MilvusHybridRetriever:
    def __init__(self, vector_store, embedder, weights: RetrievalWeights) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.weights = weights

    def retrieve(self, query: QueryVariant, top_k: int) -> list[RetrievalResult]:
        dense_candidates: dict[str, RetrievalResult] = {}

        for unit in query.retrieval_units:
            dense_vector = self.embedder.encode([unit])[0]
            dense_hits = self.vector_store.search_dense(dense_vector, limit=top_k)
            self._merge_hits(dense_candidates, dense_hits, score_field="dense_score")

        normalized_dense = min_max_normalize(
            [item.dense_score for item in dense_candidates.values()]
        )

        ranked: list[RetrievalResult] = []
        for item, dense_score in zip(dense_candidates.values(), normalized_dense):
            ranked.append(
                item.model_copy(
                    update={
                        "bm25_score": 0.0,
                        "dense_score": dense_score,
                        "combined_score": dense_score,
                    }
                )
            )

        return sorted(ranked, key=lambda item: item.combined_score, reverse=True)[:top_k]

    def _merge_hits(
        self,
        target: dict[str, RetrievalResult],
        raw_hits,
        score_field: str,
    ) -> None:
        for hit in self._flatten_hits(raw_hits):
            chunk_id = str(hit.get("id", ""))
            if not chunk_id:
                continue

            entity = hit.get("entity", {})
            article_id = str(entity.get("article_id", "unknown_article"))
            text = str(entity.get("dense_text") or entity.get("text") or "")
            score = float(hit.get("score", 0.0))

            if chunk_id in target:
                current = getattr(target[chunk_id], score_field)
                if score > current:
                    setattr(target[chunk_id], score_field, score)
                continue

            payload = {
                "chunk_id": chunk_id,
                "article_id": article_id,
                "text": text,
                score_field: score,
            }
            target[chunk_id] = RetrievalResult(**payload)

    def _flatten_hits(self, raw_hits):
        if raw_hits is None:
            return []

        if isinstance(raw_hits, list) and raw_hits and isinstance(raw_hits[0], list):
            return raw_hits[0]

        if isinstance(raw_hits, list):
            return raw_hits

        return []
