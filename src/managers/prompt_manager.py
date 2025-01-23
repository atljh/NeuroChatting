from typing import List, Optional
from config import Config
from src.logger import console
from src.managers.file_manager import FileManager


class PromptManager:
    """
    Manages prompt templates and generates prompts for OpenAI API.
    """

    def __init__(self, config: Config):
        """
        Initializes the PromptManager.

        Args:
            config (Config): Configuration object with settings like OpenAI API key.
        """
        self.config = config
        self.prompt_tone = self.config.prompt_tone
        self.prompts = self.load_prompts()

    def load_prompts(self) -> List[str]:
        """Loads prompt templates from a file."""
        return FileManager.read_prompts()

    async def generate_prompt(self, message_text: str) -> Optional[str]:
        """
        Generates a prompt by inserting message text and tone into a template.

        Args:
            message_text (str): Text to include in the prompt.

        Returns:
            Optional[str]: Generated prompt or None if no templates are available.
        """
        if not self.prompts:
            console.log("Промпты не найдены", style="red")
            return None

        prompt_tone = self.prompt_tone
        prompt = self.prompts[0]
        prompt = prompt.replace("{message_text}", message_text)
        prompt = prompt.replace("{prompt_tone}", prompt_tone)
        return prompt
