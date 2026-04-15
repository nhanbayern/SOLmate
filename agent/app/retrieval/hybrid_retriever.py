from app.config import RetrievalWeights
from app.retrieval.normalizer import min_max_normalize
from app.schemas.models import QueryVariant, RetrievalResult


class HybridRetriever:
    def __init__(self, bm25_retriever, dense_retriever, weights: RetrievalWeights) -> None:
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.weights = weights

    def retrieve(self, query: QueryVariant, top_k: int) -> list[RetrievalResult]:
        bm25_results = self.bm25_retriever.retrieve(query, top_k=top_k)
        dense_results = self.dense_retriever.retrieve(query, top_k=top_k)

        merged: dict[str, RetrievalResult] = {}
        for item in bm25_results:
            merged[item.chunk_id] = item

        for item in dense_results:
            if item.chunk_id in merged:
                merged[item.chunk_id].dense_score = item.dense_score
            else:
                merged[item.chunk_id] = item

        bm25_scores = [item.bm25_score for item in merged.values()]
        dense_scores = [item.dense_score for item in merged.values()]
        normalized_bm25 = min_max_normalize(bm25_scores)
        normalized_dense = min_max_normalize(dense_scores)

        reranked: list[RetrievalResult] = []
        for item, bm25_score, dense_score in zip(merged.values(), normalized_bm25, normalized_dense):
            combined_score = (self.weights.bm25 * bm25_score) + (self.weights.dense * dense_score)
            reranked.append(
                item.model_copy(
                    update={
                        "bm25_score": bm25_score,
                        "dense_score": dense_score,
                        "combined_score": combined_score,
                    }
                )
            )

        return sorted(reranked, key=lambda result: result.combined_score, reverse=True)[:top_k]
