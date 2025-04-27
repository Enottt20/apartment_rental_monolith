from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field, Extra, SecretStr, FilePath

class Config(BaseSettings):
    POSTGRES_DSN: PostgresDsn = Field(
        default='postgresql://uuuuu12345:ppppp11111@postgresql:5432/postgres',
        env='POSTGRES_DSN',
        alias='POSTGRES_DSN'
    )

    POSTGRES_DSN_ASYNC: PostgresDsn = Field(
        default='postgresql+asyncpg://uuuuu12345:ppppp11111@postgresql:5432/postgres',
        env='POSTGRES_DSN_ASYNC',
        alias='POSTGRES_DSN_ASYNC'
    )

    FRONT: str = Field(
        default='http://localhost:3000',
        env='FRONT',
        alias='FRONT'
    )

    jwt_secret: str = Field(
        default='JWT_SECRET',
        env='JWT_SECRET',
        alias='JWT_SECRET'
    )

    reset_password_token_secret: SecretStr = Field(
        default='RESET_PASSWORD_TOKEN_SECRET',
        env='RESET_PASSWORD_TOKEN_SECRET',
        alias='RESET_PASSWORD_TOKEN_SECRET'
    )

    verification_token_secret: SecretStr = Field(
        default='VERIFICATION_TOKEN_SECRET',
        env='VERIFICATION_TOKEN_SECRET',
        alias='VERIFICATION_TOKEN_SECRET'
    )

    class Config:
        env_file = "example.env"  # Указываем имя файла example.env
        extra = Extra.allow  # Разрешаем дополнительные входные данные


# Создаем экземпляр конфигурации
def load_config() -> Config:
    return Config()
