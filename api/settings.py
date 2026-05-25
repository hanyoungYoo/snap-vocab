from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    api_secret_key: str

    # LLM
    llm_provider: str = ""
    llm_api_key: str = ""
    extract_model: str = "claude-haiku-4-5-20251001"
    review_model: str = "claude-sonnet-4-6"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_webhook_secret: str = ""
    notification_provider: str = "telegram"

    # Review
    review_time: str = "21:00"
    review_max_cards: int = 5


settings = Settings()  # type: ignore[call-arg]
