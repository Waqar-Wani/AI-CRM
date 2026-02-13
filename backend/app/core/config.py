from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./crm.db"
    perplexity_api_key: str | None = None
    perplexity_model: str = "sonar-pro"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"


settings = Settings()
