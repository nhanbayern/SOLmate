import argparse
import json
import re
from pathlib import Path

from app.ingestion.csv_to_enterprise_json import METRIC_COLUMNS


SECTION_HEADER_PATTERN = re.compile(r"^###\s+\d+\.\s+(.+?)\s*$")
PRIMARY_VALUE_PREFIXES = (
    "Formula:",
    "Main formula:",
    "Weighted formula:",
    "Rules:",
    "Probabilities:",
)


def parse_markdown_sections(markdown_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_name: str | None = None

    for raw_line in markdown_text.splitlines():
        match = SECTION_HEADER_PATTERN.match(raw_line.strip())
        if match:
            current_name = match.group(1).strip()
            sections[current_name] = []
            continue

        if current_name is None:
            continue

        stripped = raw_line.strip()
        if stripped == "---":
            continue
        sections[current_name].append(raw_line.rstrip())

    return sections


def normalize_section_lines(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if text.startswith("- "):
            text = text[2:].strip()
        normalized.append(text)
    return normalized


def extract_primary_value(lines: list[str]) -> str:
    for line in lines:
        for prefix in PRIMARY_VALUE_PREFIXES:
            if line.startswith(prefix):
                return line.removeprefix(prefix).strip()
    return ""


def build_cic_metric_specs(markdown_text: str) -> list[dict[str, str]]:
    sections = parse_markdown_sections(markdown_text)
    specs: list[dict[str, str]] = []

    for metric_name in METRIC_COLUMNS:
        if metric_name not in sections:
            raise ValueError(f"Metric '{metric_name}' was not found in description.txt.")

        normalized_lines = normalize_section_lines(sections[metric_name])
        specs.append(
            {
                "metrics": metric_name,
                "value": extract_primary_value(normalized_lines),
                "note": " ".join(normalized_lines),
            }
        )

    return specs


def convert_description_to_cic_specs(
    input_path: str | Path,
    output_path: str | Path,
) -> tuple[int, Path]:
    source_file = Path(input_path)
    target_file = Path(output_path)

    specs = build_cic_metric_specs(source_file.read_text(encoding="utf-8"))
    target_file.write_text(
        json.dumps(specs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(specs), target_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert dataset description.txt into cic_metrics_spec.json.",
    )
    parser.add_argument(
        "--input",
        default="dataset/description.txt",
        help="Path to the markdown/text description source.",
    )
    parser.add_argument(
        "--output",
        default="dataset/cic_metrics_spec.json",
        help="Path to the JSON output file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    total_specs, output_file = convert_description_to_cic_specs(args.input, args.output)
    print(f"Converted {total_specs} metric specs to {output_file.as_posix()}.")


if __name__ == "__main__":
    main()
