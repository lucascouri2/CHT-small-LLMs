from enum import Enum

class LLMs(Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    CODELLAMA = "codellama:7b"
    QWEN = "qwen2.5-coder:7b"
    CODEGEMMA = "codegemma:7b"
    DEEP_SEEK_CODER = "deepseek-coder:6.7b"
    QWEN_MINI = "qwen2.5-coder:1.5b"
    DEEP_SEEK_CODER_MINI = "deepseek-coder:1.3b"
    GEMMA_MINI = "codegemma:2b"
    OPEN_CODER_MINI = "opencoder:1.5b"
    DEEP_CODER_MINI = "deepcoder:1.5b"
    STAR_CODER_MINI = "starcoder:1b"