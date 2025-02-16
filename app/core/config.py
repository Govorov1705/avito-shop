from datetime import timedelta
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str
    DB_ECHO: bool

    TESTING_DB_NAME: str = "tests"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    JWT_LIFESPAN: timedelta = timedelta(days=30)

    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def TESTING_DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.TESTING_DB_NAME}"


settings = Settings()
