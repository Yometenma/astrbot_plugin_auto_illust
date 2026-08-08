"""插件全局常量。"""

# 后端类型
BACKEND_NOVELAI = "novelai"
BACKEND_SD_WEBUI = "sd_webui"
BACKEND_COMFYUI = "comfyui"

# 触发模式
TRIGGER_PROBABILITY = "probability"
TRIGGER_INTERVAL = "interval"
TRIGGER_MANUAL = "manual"

# 默认值
DEFAULT_PROBABILITY = 0.3
DEFAULT_INTERVAL = 3
DEFAULT_COOLDOWN = 2

# Prompt LLM 默认系统提示词
PROMPT_LLM_SYSTEM = (
    "你是一个专业的 AI 绘画 prompt 工程师。"
    "根据用户的对话内容，提炼出适合生图的简洁 prompt。"
    "用英文 tag 输出，逗号分隔，不超过 200 字符。"
    "只输出 prompt 本身，不要输出任何解释。"
)
