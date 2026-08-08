"""Stable Diffusion WebUI 生图后端。"""

import base64
import json
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def generate_sd_webui(
    prompt: str,
    negative_prompt: str,
    sd_url: str,
    width: int = 768,
    height: int = 512,
    steps: int = 20,
    cfg_scale: float = 7.0,
    sampler: str = "DPM++ 2M Karras",
    seed: int = -1,
) -> Optional[bytes]:
    """调用 Stable Diffusion WebUI 生成图片，返回 PNG 字节。"""
    url = f"{sd_url.rstrip('/')}/sdapi/v1/txt2img"
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "sampler_index": sampler,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "seed": seed,
        "batch_size": 1,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    b64 = data.get("images", [None])[0]
                    if b64:
                        return base64.b64decode(b64)
                text = await resp.text()
                logger.error(f"SD API {resp.status}: {text[:200]}")
                return None
    except Exception as e:
        logger.error(f"SD 生成失败: {e}")
        return None
