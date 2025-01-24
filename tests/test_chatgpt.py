import pytest
from unittest.mock import AsyncMock, patch
from src.chatgpt import ChatGPTClient
from config import Config, ConfigManager


@pytest.fixture
def config():
    config = ConfigManager.load_config()
    return Config(openai_api_key=config.openai_api_key, chat_gpt_model="gpt-3.5-turbo")


@pytest.fixture
def chatgpt_client(config):
    return ChatGPTClient(config)


@pytest.mark.asyncio
async def test_generate_answer(chatgpt_client):
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]

    with patch("openai.resources.chat.Completions.create", return_value=mock_response):
        answer = await chatgpt_client.generate_answer("Test prompt")
        assert answer == "Test response"


@pytest.mark.asyncio
async def test_generate_answer_empty_prompt(chatgpt_client):
    answer = await chatgpt_client.generate_answer("")
    assert answer is None


@pytest.mark.asyncio
async def test_generate_answer_api_error(chatgpt_client):
    with patch("openai.resources.chat.Completions.create", side_effect=Exception("API error")):
        answer = await chatgpt_client.generate_answer("Test prompt")
        assert answer is None
