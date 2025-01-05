import sys
import yaml
from typing import Tuple
from pydantic import BaseModel, Field, field_validator
from src.logger import logger
from src.console import console


class Config(BaseModel):
    openai_api_key: str
    chat_gpt_model: str
    prompt_tone: str = Field(
        default="Дружелюбный",
        description="Тон сообщения"
    )
    join_chat_delay: Tuple[int, int] = Field(
        default=(10, 20),
        description="Диапазон задержки перед подпиской на чат"
    )
    message_limit: int = Field(
        default=10,
        ge=1,
        description="Лимит сообщений на одного пользователя"
    )
    send_message_delay: Tuple[int, int] = Field(
        default=(10, 20),
        description="Задержка перед отправкой сообщения"
    )
    reaction_mode: str = Field(
        default="keywords",
        description="Режим реакции: keywords или interval"
    )
    reaction_interval: int = Field(
        default=10,
        ge=1,
        description="Интервал сообщений для ответа (если режим inteval)"
    )
    keywords_file: str = Field(
        default="key.txt",
        description="Файл с ключевыми словами (если режим keywords)"
    )

    @field_validator('openai_api_key')
    def validate_openai_api_key(cls, value):
        if not value:
            logger.error("openai_api_key не найден")
            sys.exit(0)
        return value


class ConfigManager:
    @staticmethod
    def load_config(config_file='config.yaml') -> Config:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

                join_delay = config_data['settings'].get('join_chat_delay')
                send_message_delay = config_data['settings'].get(
                    'send_message_delay'
                )

                if (
                    isinstance(join_delay, str)
                    and '-' in join_delay
                ):
                    min_delay, max_delay = map(int, join_delay.split('-'))
                    config_data['settings']['join_chat_delay'] = (min_delay, max_delay)

                if (
                    isinstance(send_message_delay, str)
                    and '-' in send_message_delay
                ):
                    min_delay, max_delay = map(int, send_message_delay.split('-'))
                    config_data['settings']['send_message_delay'] = (min_delay, max_delay)

                return Config(
                    **config_data['api'],
                    **config_data['settings']
                )
        except Exception as e:
            console.log("Ошибка в конфиге", style="red")
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            sys.exit(1)
