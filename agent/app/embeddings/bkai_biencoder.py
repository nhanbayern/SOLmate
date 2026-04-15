from app.core.interfaces import EmbeddingModel


class BKAIBiEncoderEmbedder(EmbeddingModel):
    def __init__(self, model_name: str = "bkai-foundation-models/vietnamese-bi-encoder") -> None:
        self.model_name = model_name
        self._model = None

    def load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required to load the BKAI bi-encoder."
            ) from exc

        self._model = SentenceTransformer(self.model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            self.load()

        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]
