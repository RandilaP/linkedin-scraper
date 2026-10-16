from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    LINKEDIN_CLIENT_ID: str
    LINKEDIN_CLIENT_SECRET: str
    JWT_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()