from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI/LLM Configuration
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "anthropic"  # or 'openai'
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"

    # Technical Conversation Detection
    TECHNICAL_CONFIDENCE_THRESHOLD: float = 0.7
    CONVERSATION_CONTEXT_WINDOW_SIZE: int = 50
    CONVERSATION_TIME_WINDOW_MINUTES: int = 10

    # Microsoft Teams Bot
    TEAMS_APP_ID: str = ""
    TEAMS_APP_PASSWORD: str = ""
    TEAMS_TENANT_ID: str = ""

    # Diagram Generation
    PLANTUML_JAR_PATH: str = "/usr/local/bin/plantuml.jar"
    DIAGRAM_STORAGE_PATH: str = "/app/diagrams"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
