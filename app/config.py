from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_data_dir: Path = ROOT_DIR / "data"

    tutor_db_path: Path = ROOT_DIR / "data" / "tutor.sqlite"

    sql_timeout_seconds: float = 2.0
    sql_max_rows: int = 200
    sql_max_query_chars: int = 20_000

    solution_after_failed_attempts: int = 5

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0

    curriculum_dir: Path = ROOT_DIR / "curriculum"
    datasets_dir: Path = ROOT_DIR / "datasets"
    web_dir: Path = ROOT_DIR / "web"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip())


settings = Settings()
