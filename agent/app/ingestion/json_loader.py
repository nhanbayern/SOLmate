import json
from pathlib import Path

from app.schemas.loan_models import (
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
)
from app.schemas.models import LegalArticle


class JSONDataLoader:
    def load_json(self, path: str | Path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _coerce_records(self, payload, model_class):
        if isinstance(payload, list):
            return [model_class(**item) for item in payload]
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [model_class(**item) for item in payload["records"]]
        return [model_class(**payload)]

    def _select_record(self, records, customer_id: str | None = None):
        if not records:
            raise ValueError("No records found in JSON payload.")
        if customer_id is None:
            return records[0]
        for record in records:
            if getattr(record, "customer_id", None) == customer_id:
                return record
        raise ValueError(f"Customer ID '{customer_id}' not found in JSON payload.")

    def load_enterprise_profiles(self, path: str | Path) -> list[EnterpriseProfile]:
        return self._coerce_records(self.load_json(path), EnterpriseProfile)

    def load_enterprise_profile(
        self,
        path: str | Path,
        customer_id: str | None = None,
    ) -> EnterpriseProfile:
        return self._select_record(self.load_enterprise_profiles(path), customer_id)

    def load_credit_score_rules(self, path: str | Path) -> list[CreditScoreRule]:
        payload = self.load_json(path)
        if isinstance(payload, list):
            return [CreditScoreRule(**item) for item in payload]
        return [CreditScoreRule(**payload)]

    def load_cic_metric_specs(self, path: str | Path) -> list[CICMetricSpec]:
        payload = self.load_json(path)
        if isinstance(payload, list):
            return [CICMetricSpec(**item) for item in payload]
        if "metrics" in payload:
            return [CICMetricSpec(**payload)]
        raise ValueError("Unsupported cic_metrics_spec.json format.")

    def load_enterprise_cic_metrics_records(self, path: str | Path) -> list[EnterpriseCICMetrics]:
        return self._coerce_records(self.load_json(path), EnterpriseCICMetrics)

    def load_enterprise_cic_metrics(
        self,
        path: str | Path,
        customer_id: str | None = None,
    ) -> EnterpriseCICMetrics:
        return self._select_record(
            self.load_enterprise_cic_metrics_records(path),
            customer_id,
        )

    def load_legal_articles(self, path: str | Path) -> list[LegalArticle]:
        payload = self.load_json(path)
        document_id = str(payload.get("document_id", "legal_document"))
        document_title = str(payload.get("title", "Legal document"))
        document_type = str(payload.get("document_type", "Văn bản pháp luật"))
        is_active = str(payload.get("is_active", ""))
        issue_date = str(payload.get("issue_date", ""))
        effective_date = str(payload.get("effective_date", ""))

        articles: list[LegalArticle] = []
        for index, item in enumerate(payload.get("articles", []), start=1):
            article = str(item.get("article", index))
            clause = item.get("clause")
            point = item.get("point")
            section_path = item.get("section_path", [])

            if "text" in item or "heading" in item:
                heading = str(item.get("heading", ""))
                content = str(item.get("text", ""))
            else:
                article_content = str(item.get("article_content", ""))
                clause_content = str(item.get("clause_content", "") or "")
                point_content = str(item.get("point_content", "") or "")

                heading_parts = [part for part in (article, clause, point) if part]
                heading = " | ".join(str(part) for part in heading_parts)

                content_parts = []
                if article_content:
                    content_parts.append(article_content)
                if clause and clause_content:
                    content_parts.append(f"{clause}: {clause_content}")
                elif clause_content:
                    content_parts.append(clause_content)
                if point and point_content:
                    content_parts.append(f"{point}: {point_content}")
                content = "\n".join(part for part in content_parts if part)

            article_id = f"{document_id}:article_{article}"
            if clause:
                article_id = f"{article_id}:clause_{clause}"
            if point:
                article_id = f"{article_id}:point_{point}"

            title_parts = [document_type, document_title]
            if heading:
                title_parts.append(heading)

            articles.append(
                LegalArticle(
                    article_id=article_id,
                    title=" | ".join(title_parts),
                    content=content,
                    metadata={
                        "document_id": document_id,
                        "document_type": document_type,
                        "is_active": is_active,
                        "issue_date": issue_date,
                        "effective_date": effective_date,
                        "article": article,
                        "clause": "" if clause is None else str(clause),
                        "point": "" if point is None else str(point),
                        "section_path": " > ".join(section_path),
                    },
                )
            )

        return articles
