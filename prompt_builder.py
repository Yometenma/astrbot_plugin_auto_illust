"""Prompt 构建器：上下文 + LLM 提炼 + 预设注入。"""

import logging
from typing import Any, Optional

from .config import PluginConfig
from .constants import PROMPT_LLM_SYSTEM

logger = logging.getLogger(__name__)


class PromptBuilder:
    """组装最终生图 prompt。"""

    def __init__(self, cfg: PluginConfig):
        self.cfg = cfg

    def build_full_prompt(self, refined_prompt: str) -> str:
        """将 LLM 提炼的 prompt 与预设拼接。"""
        parts = []
        if self.cfg.positive_prefix:
            parts.append(self.cfg.positive_prefix)
        if self.cfg.artist_tags:
            parts.append(self.cfg.artist_tags)
        parts.append(self.cfg.appearance)
        if self.cfg.costume:
            parts.append(self.cfg.costume)
        parts.append(refined_prompt)
        return ", ".join(p for p in parts if p)

    async def refine_prompt(self, context: str, provider: Any = None) -> str:
        """调用 LLM 从上下文提炼生图 prompt。"""
        if not self.cfg.prompt_llm_enabled:
            return context[:200]

        if provider is not None:
            try:
                system = self.cfg.prompt_llm_system or PROMPT_LLM_SYSTEM
                resp = await provider.text_chat(
                    prompt=context, system_prompt=system,
                )
                if resp and resp.result_chain:
                    plain = resp.result_chain.get_plain_text()
                    if plain:
                        return plain.strip()[:200]
            except Exception as e:
                logger.warning(f"Prompt LLM 调用失败: {e}")

        return context[:200]
