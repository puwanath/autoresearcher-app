from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # LLM (vLLM, OpenAI-compatible)
    vllm_endpoint: str = "http://192.168.3.238:8000/v1"
    vllm_api_key: str = "EMPTY"
    vllm_model: str = "Qwen3.6-35B-A3B-FP8"
    vllm_temperature: float = 0.3
    vllm_max_tokens: int = 8192
    vllm_top_p: float = 0.9
    vllm_timeout: float = 240
    vllm_enable_thinking: bool = False

    # Infra
    database_url: str = "postgresql+asyncpg://autoresearch:autoresearch@localhost:5433/autoresearch"
    redis_url: str = "redis://localhost:6380/0"

    # Research limits
    search_region: str = "th-th"
    max_search_results: int = 8
    max_pages: int = 12
    max_iterations: int = 2
    scrape_timeout: float = 20
    scrape_concurrency: int = 4
    llm_concurrency: int = 4
    page_text_chars: int = 14000
    use_playwright: bool = True

    data_dir: Path = Path("./data")

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"


@lru_cache
def get_settings() -> Settings:
    return Settings()
