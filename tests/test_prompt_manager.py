import pytest
from src.managers.prompt_manager import PromptManager
from config import Config


@pytest.fixture
def config():
    return Config(prompt_tone="friendly", openai_api_key='test', chat_gpt_model='3.5')


@pytest.mark.asyncio
async def test_generate_prompt(config):
    prompt_manager = PromptManager(config)

    prompt = await prompt_manager.generate_prompt("Hello, how are you?")
    assert "{message_text}" not in prompt
    assert "{prompt_tone}" not in prompt
    assert "Hello, how are you?" in prompt
    assert "friendly" in prompt
