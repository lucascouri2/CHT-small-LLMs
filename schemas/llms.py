from enum import Enum

class LLMs(Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    CODELLAMA = "codellama:7b"
    QWEN = "qwen2.5-coder:7b"
    CODEGEMMA = "codegemma:7b"
    DEEP_SEEK_CODER = "deepseek-coder:6.7b"
    QWEN_MINI = "qwen2.5-coder:1.3b"
    DEEP_SEEK_CODER_MINI = "deepseek-coder:1.3b"