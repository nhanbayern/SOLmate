from pathlib import Path


VI_STOPWORDS = Path(__file__).resolve().parents[2] / "dataset" / "vietnamese-stopwords.txt"


def remove_stopwords(text: str) -> str:
    with open(VI_STOPWORDS, "r", encoding="utf-8") as f:
        stopwords = set(line.strip().lower() for line in f)
    tokens = text.split()
    kept_tokens = [token for token in tokens if token.lower() not in stopwords]
    return " ".join(kept_tokens)
