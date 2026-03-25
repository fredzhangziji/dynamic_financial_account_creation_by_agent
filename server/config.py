from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = "sk-placeholder"
    openai_model: str = "gpt-4o"
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
