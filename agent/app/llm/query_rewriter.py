from app.core.interfaces import QueryRewriter
from app.core.prompts import QUERY_REWRITE_PROMPT_TEMPLATE


class MockQueryRewriter(QueryRewriter):
    def rewrite(self, query: str) -> str:
        return " ".join(query.strip().split())


class QwenQueryRewriter(QueryRewriter):
    def __init__(self, llm_client) -> None:
        self.llm_client = llm_client

    def rewrite(self, query: str) -> str:
        prompt = QUERY_REWRITE_PROMPT_TEMPLATE.format(question=query)
        return self.llm_client.generate(prompt, max_new_tokens=64).strip()
