"""NovelAI 生图后端。

参考：
- novelai-api Python 库 (deedlitelf/novelai-api)
- st-chatu8 SillyTavern 插件
"""

import base64
import json
import logging
from io import BytesIO
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

NOVELAI_API = "https://api.novelai.net"


async def generate_novelai(
    prompt: str,
    negative_prompt: str,
    api_key: str,
    width: int = 768,
    height: int = 512,
    steps: int = 28,
    scale: float = 11.0,
    sampler: str = "k_euler_ancestral",
    seed: int = -1,
) -> Optional[bytes]:
    """调用 NovelAI 生成图片，返回 PNG 字节。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": prompt,
        "model": "nai-diffusion-3",
        "parameters": {
            "width": width,
            "height": height,
            "scale": scale,
            "sampler": sampler,
            "steps": steps,
            "seed": seed,
            "n_samples": 1,
            "negative_prompt": negative_prompt,
            "qualityToggle": True,
        },
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{NOVELAI_API}/ai/generate",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
                text = await resp.text()
                logger.error(f"NovelAI API {resp.status}: {text[:200]}")
                return None
    except Exception as e:
        logger.error(f"NovelAI 生成失败: {e}")
        return None
