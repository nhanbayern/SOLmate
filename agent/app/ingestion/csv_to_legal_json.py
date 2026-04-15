import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ARTICLE_PATTERN = re.compile(r"^(điều\s+\d+[a-z]*)\s*(.*)$", re.IGNORECASE)
CLAUSE_PATTERN = re.compile(r"^(khoản\s+\d+)\s*(.*)$", re.IGNORECASE)
POINT_PATTERN = re.compile(r"^(điểm\s+[a-zđ])\s*(.*)$", re.IGNORECASE)
CLAUSE_CONTENT_PREFIX = re.compile(r"^\d+\.\s*")
POINT_CONTENT_PREFIX = re.compile(r"^[a-zđ]\)\s*", re.IGNORECASE)


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").strip().split())


def parse_date(value: str) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return datetime.strptime(text, "%m/%d/%Y").date().isoformat()


def build_section_path(
    article: str,
    clause: str | None = None,
    point: str | None = None,
) -> list[str]:
    parts = [part for part in (article, clause, point) if part]
    return [", ".join(parts)]


def strip_leading_annotation(value: str) -> str:
    _, remainder = split_leading_annotations(value)
    return remainder


def split_leading_annotations(value: str) -> tuple[str, str]:
    text = value.strip()
    annotations: list[str] = []
    while text.startswith("("):
        depth = 0
        consumed = 0
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    consumed = index + 1
                    break
        if consumed == 0:
            break
        annotations.append(text[:consumed].strip())
        text = text[consumed:].lstrip(" ,:-")
    return " ".join(annotations).strip(), text.strip()

def normalize_label(
    raw_label: str,
    pattern: re.Pattern[str],
    prefix: str,
    keep_leading_annotation: bool = False,
) -> tuple[str | None, str]:
    text = normalize_text(raw_label)
    match = pattern.match(text)
    if not match:
        return None, ""

    identifier = match.group(1)
    annotation_text, suffix = split_leading_annotations(match.group(2))
    normalized = f"{prefix} {identifier.split()[-1]}"
    if keep_leading_annotation and annotation_text:
        normalized = f"{normalized} {annotation_text}"
    return normalized, suffix


def normalize_content(value: str, level: str) -> str:
    text = normalize_text(value)
    if level == "clause":
        return CLAUSE_CONTENT_PREFIX.sub("", text, count=1).strip()
    if level == "point":
        return POINT_CONTENT_PREFIX.sub("", text, count=1).strip()
    return text


def append_text(current: str | None, extra: str) -> str:
    extra_text = normalize_text(extra)
    if not extra_text:
        return current or ""
    if not current:
        return extra_text
    return f"{current}\n{extra_text}"


def create_article_entry(
    article: str,
    article_content: str,
    body_text: str,
) -> dict[str, Any]:
    return {
        "article": article,
        "article_content": article_content,
        "clause": None,
        "clause_content": normalize_content(body_text, level="article"),
        "point": None,
        "point_content": None,
        "section_path": build_section_path(article),
    }


def create_clause_entry(
    article: str,
    article_content: str,
    clause: str,
    clause_content: str,
) -> dict[str, Any]:
    return {
        "article": article,
        "article_content": article_content,
        "clause": clause,
        "clause_content": normalize_content(clause_content, level="clause"),
        "point": None,
        "point_content": None,
        "section_path": build_section_path(article, clause),
    }


def create_point_entry(
    article: str,
    article_content: str,
    clause: str | None,
    clause_content: str | None,
    point: str,
    point_content: str,
) -> dict[str, Any]:
    return {
        "article": article,
        "article_content": article_content,
        "clause": clause,
        "clause_content": clause_content,
        "point": point,
        "point_content": normalize_content(point_content, level="point"),
        "section_path": build_section_path(article, clause, point),
    }


def update_current_entry(entry: dict[str, Any], extra_text: str) -> None:
    if entry["point"] is not None:
        entry["point_content"] = append_text(entry["point_content"], extra_text)
        return
    entry["clause_content"] = append_text(entry["clause_content"], extra_text)


def extract_metadata(rows: list[list[str]]) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    for row in rows[:7]:
        first = normalize_text(row[0]) if row else ""
        second = normalize_text(row[1]) if len(row) > 1 else ""
        if not first and second:
            metadata["status"] = second
            continue
        if first:
            metadata[first] = second

    document_id = metadata.get("Số Thông tư", "").removeprefix("Thông tư số").strip()
    status_text = metadata.get("status", "").lower()
    return {
        "document_id": document_id,
        "document_type": "Thông tư",
        "is_active": "còn hiệu lực" in status_text,
        "title": metadata.get("Tiêu đề Thông tư", ""),
        "issue_date": parse_date(metadata.get("Ngày ban hành", "")),
        "effective_date": parse_date(metadata.get("Ngày hiệu lực", "")),
    }


def build_legal_document(rows: list[list[str]]) -> dict[str, Any]:
    payload = extract_metadata(rows)
    articles: list[dict[str, Any]] = []

    current_article: str | None = None
    current_article_content = ""
    current_clause: str | None = None
    current_clause_content: str | None = None
    current_entry: dict[str, Any] | None = None

    for row in rows[7:]:
        first = normalize_text(row[0]) if row else ""
        second = normalize_text(row[1]) if len(row) > 1 else ""

        if not first and not second:
            continue

        article_label, article_suffix = normalize_label(
            first,
            ARTICLE_PATTERN,
            "Điều",
            keep_leading_annotation=True,
        )
        if article_label:
            current_article = article_label
            current_clause = None
            current_clause_content = None
            current_entry = None

            if article_suffix and second and re.match(r"^\d+\.\s*", second):
                current_article_content = article_suffix
                current_entry = create_article_entry(
                    article=current_article,
                    article_content=current_article_content,
                    body_text=second,
                )
                articles.append(current_entry)
                continue

            current_article_content = second or article_suffix or current_article
            continue

        clause_label, _ = normalize_label(first, CLAUSE_PATTERN, "Khoản")
        if clause_label and current_article:
            current_clause = clause_label
            current_clause_content = normalize_content(second, level="clause")
            current_entry = create_clause_entry(
                article=current_article,
                article_content=current_article_content,
                clause=current_clause,
                clause_content=current_clause_content,
            )
            articles.append(current_entry)
            continue

        point_label, _ = normalize_label(first, POINT_PATTERN, "Điểm")
        if point_label and current_article:
            current_entry = create_point_entry(
                article=current_article,
                article_content=current_article_content,
                clause=current_clause,
                clause_content=current_clause_content,
                point=point_label,
                point_content=second,
            )
            articles.append(current_entry)
            continue

        if second and current_article:
            if current_entry is None:
                current_entry = create_article_entry(
                    article=current_article,
                    article_content=current_article_content,
                    body_text=second,
                )
                articles.append(current_entry)
            else:
                update_current_entry(current_entry, second)

    payload["articles"] = articles
    return payload


def convert_csv_to_legal_json(
    csv_path: str | Path,
    output_path: str | Path,
) -> tuple[int, Path]:
    csv_file = Path(csv_path)
    output_file = Path(output_path)

    with csv_file.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    document = build_legal_document(rows)
    output_file.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(document["articles"]), output_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Vietnamese banking-law CSV data into legal JSON.",
    )
    parser.add_argument(
        "--csv",
        default="dataset/vietnamese-laws-bank.csv",
        help="Path to the source legal CSV file.",
    )
    parser.add_argument(
        "--output",
        default="dataset/vietnamese-bank-legal.json",
        help="Path to the legal JSON output file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    total_articles, output_file = convert_csv_to_legal_json(args.csv, args.output)
    print(f"Converted {total_articles} legal sections to {output_file.as_posix()}.")


if __name__ == "__main__":
    main()
