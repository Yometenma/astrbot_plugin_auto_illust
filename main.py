"""
astrbot_plugin_auto_illust
聊天自动配图插件

在聊天过程中自动为 Bot 回复配图。
LLM 读取上下文 → 判断触发 → 提炼 prompt → 注入预设 → 生图 → 插入回复。

支持后端: NovelAI / Stable Diffusion WebUI
触发模式: 概率 / 间隔 / 手动

作者：yometenma
版本：1.0.0
"""

import asyncio
from io import BytesIO

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, register

from .config import PluginConfig
from .trigger import TriggerManager
from .prompt_builder import PromptBuilder
from .constants import BACKEND_NOVELAI, BACKEND_SD_WEBUI, BACKEND_COMFYUI

__version__ = "1.0.0"


@register(
    "astrbot_plugin_auto_illust",
    "yometenma",
    "聊天自动配图",
    __version__,
)
class AutoIllustPlugin(Star):
    """聊天自动配图插件。"""

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.cfg = PluginConfig(config)
        self.trigger_mgr = TriggerManager(self.cfg)
        self.prompt_builder = PromptBuilder(self.cfg)
        self._msg_count = 0
        self._context_cache: list[dict] = []

    async def initialize(self) -> None:
        self.logger.info(
            f"自动配图插件已就绪 | "
            f"后端: {self.cfg.backend} | "
            f"触发: {self.cfg.trigger_mode} | "
            f"Prompt LLM: {'开' if self.cfg.prompt_llm_enabled else '关'}"
        )

    # ==================== 消息钩子 ====================

    @filter.after_message_sent()
    async def on_bot_reply(self, event: AstrMessageEvent):
        """Bot 回复后触发插图。"""
        self._msg_count += 1

        if not self.trigger_mgr.should_trigger(self._msg_count):
            return

        # 收集最近上下文
        context = self._build_context(event)

        try:
            # 1. LLM 提炼 prompt
            provider = self.context.get_using_provider()
            refined = await self.prompt_builder.refine_prompt(context, provider)

            # 2. 拼接预设
            full_prompt = self.prompt_builder.build_full_prompt(refined)
            self.logger.info(f"生图 prompt: {full_prompt[:150]}...")

            # 3. 生图
            image_bytes = await self._generate(full_prompt)
            if not image_bytes:
                return

            # 4. 发送图片
            await self._send_image(event, image_bytes)

        except Exception as e:
            self.logger.error(f"配图失败: {e}", exc_info=True)

    # ==================== 手动触发 ====================

    @filter.command("illustrate")
    async def cmd_illustrate(self, event: AstrMessageEvent):
        """手动触发配图。"""
        self.trigger_mgr.mark_triggered(self._msg_count)
        context = self._build_context(event)
        try:
            provider = self.context.get_using_provider()
            refined = await self.prompt_builder.refine_prompt(context, provider)
            full_prompt = self.prompt_builder.build_full_prompt(refined)
            self.logger.info(f"[手动] 生图 prompt: {full_prompt[:150]}...")

            image_bytes = await self._generate(full_prompt)
            if not image_bytes:
                yield event.plain_result("生图失败，请查看日志")
                return
            await self._send_image(event, image_bytes)
        except Exception as e:
            yield event.plain_result(f"生图失败: {e}")

    # ==================== 内部方法 ====================

    def _build_context(self, event: AstrMessageEvent) -> str:
        """构建最近对话上下文文本。"""
        msg = event.message_str or ""
        self._context_cache.append({"role": "user", "content": msg})
        if len(self._context_cache) > 10:
            self._context_cache = self._context_cache[-10:]
        return "\n".join(
            f"{'用户' if m['role'] == 'user' else 'Bot'}: {m['content']}"
            for m in self._context_cache[-6:]
        )

    async def _generate(self, prompt: str) -> bytes | None:
        """根据配置调用后端生成图片。"""
        if self.cfg.backend == BACKEND_NOVELAI:
            if not self.cfg.nai_key:
                self.logger.error("未配置 NovelAI API Key")
                return None
            from .backends.novelai import generate_novelai
            return await generate_novelai(
                prompt=prompt,
                negative_prompt=self.cfg.negative_prompt,
                api_key=self.cfg.nai_key,
                width=self.cfg.width,
                height=self.cfg.height,
                steps=self.cfg.steps,
                scale=self.cfg.scale,
                sampler=self.cfg.sampler,
                seed=self.cfg.seed,
            )

        if self.cfg.backend == BACKEND_SD_WEBUI:
            from .backends.sd_webui import generate_sd_webui
            return await generate_sd_webui(
                prompt=prompt,
                negative_prompt=self.cfg.negative_prompt,
                sd_url=self.cfg.sd_url,
                width=self.cfg.width,
                height=self.cfg.height,
                steps=self.cfg.steps,
                cfg_scale=self.cfg.scale,
                sampler=self.cfg.sampler,
                seed=self.cfg.seed,
            )

        if self.cfg.backend == BACKEND_COMFYUI:
            if not self.cfg.comfyui_workflow:
                self.logger.error("未配置 ComfyUI 工作流")
                return None
            from .backends.comfyui import generate_comfyui
            return await generate_comfyui(
                prompt=prompt,
                negative_prompt=self.cfg.negative_prompt,
                comfyui_url=self.cfg.comfyui_url,
                workflow_json=self.cfg.comfyui_workflow,
            )

        self.logger.error(f"不支持的后端: {self.cfg.backend}")
        return None

    async def _send_image(self, event: AstrMessageEvent, image_bytes: bytes):
        """用 AstrBot 发送图片。"""
        try:
            # 尝试用 fromBytes + 平台发送
            img = Image.fromBytes(
                image_bytes,
                format="png",
            )
            # 通过 event 回复
            await event.send(img)
        except Exception as e:
            self.logger.error(f"发送图片失败: {e}")
