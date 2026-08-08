"""ComfyUI 生图后端。

参考：st-chatu8 SillyTavern 插件、ComfyUI 官方 API 文档。

用户提供工作流 JSON 模板，插件将 [PROMPT] / [NEGATIVE_PROMPT] 替换后提交。
"""

import json
import logging
import uuid
from typing import Optional

import asyncio
import aiohttp

logger = logging.getLogger(__name__)


async def generate_comfyui(
    prompt: str,
    negative_prompt: str,
    comfyui_url: str,
    workflow_json: str,
) -> Optional[bytes]:
    """提交 ComfyUI 工作流并等待生图完成，返回图片字节。"""
    base = comfyui_url.rstrip("/")
    client_id = str(uuid.uuid4())

    # 1. 注入 prompt 到工作流
    try:
        workflow = json.loads(workflow_json)
    except json.JSONDecodeError as e:
        logger.error(f"ComfyUI 工作流 JSON 解析失败: {e}")
        return None

    _inject_prompts(workflow, prompt, negative_prompt)

    # 2. 提交任务
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/prompt",
                json={"prompt": workflow, "client_id": client_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    logger.error(f"ComfyUI 提交失败: {resp.status}")
                    return None
                data = await resp.json()
                prompt_id = data.get("prompt_id")
                if not prompt_id:
                    logger.error("ComfyUI 未返回 prompt_id")
                    return None

            # 3. 轮询等待结果
            for _ in range(60):  # 最多等 120 秒
                await asyncio.sleep(2)
                async with session.get(
                    f"{base}/history/{prompt_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        continue
                    history = await resp.json()
                    entry = history.get(prompt_id)
                    if not entry:
                        continue
                    outputs = entry.get("outputs", {})
                    for node_id, node_output in outputs.items():
                        images = node_output.get("images", [])
                        if images:
                            img_info = images[0]
                            img_url = f"{base}/view?filename={img_info['filename']}&subfolder={img_info.get('subfolder', '')}&type={img_info.get('type', 'output')}"
                            async with session.get(img_url) as img_resp:
                                return await img_resp.read()
            logger.error("ComfyUI 生图超时")
            return None
    except Exception as e:
        logger.error(f"ComfyUI 生成失败: {e}")
        return None


def _inject_prompts(workflow: dict, prompt: str, negative: str) -> None:
    """递归遍历工作流 JSON，将占位符替换为实际 prompt。"""
    if isinstance(workflow, dict):
        for key, value in workflow.items():
            if isinstance(value, str):
                if "[PROMPT]" in value:
                    workflow[key] = value.replace("[PROMPT]", prompt)
                if "[NEGATIVE_PROMPT]" in value:
                    workflow[key] = value.replace("[NEGATIVE_PROMPT]", negative)
            elif isinstance(value, (dict, list)):
                _inject_prompts(value, prompt, negative)
    elif isinstance(workflow, list):
        for item in workflow:
            _inject_prompts(item, prompt, negative)
