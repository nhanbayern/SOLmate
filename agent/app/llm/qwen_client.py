class QwenClient:
    def __init__(self, model_name: str = "Qwen/Qwen3-0.6B") -> None:
        self.model_name = model_name
        self._pipeline = None

    def load(self) -> None:
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise ImportError("transformers is required to use QwenClient.") from exc

        self._pipeline = pipeline(
            task="text-generation",
            model=self.model_name,
            trust_remote_code=True,
        )

        model_config = getattr(self._pipeline.model, "config", None)
        if model_config is not None and getattr(model_config, "max_length", None) is not None:
            model_config.max_length = None

        generation_config = getattr(self._pipeline.model, "generation_config", None)
        if generation_config is not None and getattr(generation_config, "max_length", None) is not None:
            generation_config.max_length = None
            self._pipeline.model.generation_config = generation_config

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        if self._pipeline is None:
            self.load()

        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        return outputs[0]["generated_text"]
