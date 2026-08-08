"""插件配置模型。"""

from .constants import (
    BACKEND_NOVELAI,
    TRIGGER_PROBABILITY,
    DEFAULT_PROBABILITY,
    DEFAULT_INTERVAL,
    DEFAULT_COOLDOWN,
)


class PluginConfig:
    """从 raw dict 解析后的配置对象。"""

    def __init__(self, raw: dict):
        # ---- 触发 ----
        self.trigger_mode: str = str(raw.get("trigger_mode", TRIGGER_PROBABILITY))
        self.probability: float = float(raw.get("probability", DEFAULT_PROBABILITY))
        self.interval: int = int(raw.get("interval", DEFAULT_INTERVAL))
        self.cooldown: int = int(raw.get("cooldown", DEFAULT_COOLDOWN))

        # ---- 后端 ----
        self.backend: str = str(raw.get("backend", BACKEND_NOVELAI))
        self.nai_key: str = str(raw.get("nai_key", ""))
        self.sd_url: str = str(raw.get("sd_url", "http://127.0.0.1:7860"))

        # ---- 生图参数 ----
        self.width: int = int(raw.get("width", 768))
        self.height: int = int(raw.get("height", 512))
        self.steps: int = int(raw.get("steps", 28))
        self.scale: float = float(raw.get("scale", 11.0))
        self.sampler: str = str(raw.get("sampler", "k_euler_ancestral"))
        self.seed: int = int(raw.get("seed", -1))

        # ---- 预设 ----
        self.appearance: str = str(raw.get("appearance", "1girl, silver hair, blue eyes"))
        self.costume: str = str(raw.get("costume", "school uniform"))
        self.artist_tags: str = str(raw.get("artist_tags", ""))
        self.positive_prefix: str = str(raw.get("positive_prefix", "masterpiece, best quality"))
        self.negative_prompt: str = str(
            raw.get("negative_prompt", "lowres, bad anatomy, bad hands, extra fingers, worst quality")
        )

        # ---- Prompt LLM ----
        self.prompt_llm_enabled: bool = bool(raw.get("prompt_llm_enabled", True))
        self.prompt_llm_api: str = str(raw.get("prompt_llm_api", ""))
        self.prompt_llm_key: str = str(raw.get("prompt_llm_key", ""))
        self.prompt_llm_model: str = str(raw.get("prompt_llm_model", ""))
        self.prompt_llm_system: str = str(raw.get("prompt_llm_system", ""))
