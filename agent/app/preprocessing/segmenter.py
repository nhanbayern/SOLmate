from app.core.interfaces import WordSegmenter


class WhitespaceFallbackSegmenter(WordSegmenter):
    def segment(self, text: str) -> str:
        return " ".join(text.split())


class RDRSegmenterAdapter(WordSegmenter):
    """Adapter placeholder for an external RDR word segmenter."""

    def __init__(self, segmenter=None) -> None:
        self.segmenter = segmenter

    def segment(self, text: str) -> str:
        if self.segmenter is None:
            return " ".join(text.split())

        if hasattr(self.segmenter, "word_segment"):
            segmented = self.segmenter.word_segment(text)
            if isinstance(segmented, list):
                return " ".join(segmented)
            return str(segmented)

        raise ValueError("Unsupported RDR segmenter instance.")
