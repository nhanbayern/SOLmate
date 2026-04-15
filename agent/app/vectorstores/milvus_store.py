from app.config import MilvusConfig


class MilvusVectorStore:
    def __init__(self, config: MilvusConfig) -> None:
        self.config = config
        self.client = None

    def connect(self) -> None:
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise ImportError("pymilvus is required to use MilvusVectorStore.") from exc

        self.client = MilvusClient(
            uri=self.config.uri,
            token=self.config.token,
            db_name=self.config.database,
        )

    def ensure_connection(self) -> None:
        if self.client is None:
            self.connect()

    def search_dense(self, vector: list[float], limit: int = 10):
        self.ensure_connection()
        return self.client.search(
            collection_name=self.config.collection_name,
            anns_field=self.config.vector_field,
            data=[vector],
            limit=limit,
            search_params={"metric_type": self.config.metric_type},
            output_fields=["article_id", self.config.text_field, self.config.metadata_field],
        )
