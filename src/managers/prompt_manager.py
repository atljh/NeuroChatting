import openai
from typing import List
from openai import OpenAI

from config import Config
from src.logger import logger, console
from src.managers.file_manager import FileManager


class PromptManager:
    """
    Manages the loading and generation of prompts for interacting with the OpenAI API.

    This class is responsible for loading prompt templates from a configuration and using them
    to generate prompts for the OpenAI API. It also initializes the OpenAI client with the
    provided API key.

    Attributes:
        config (Config): The configuration object containing settings such as the OpenAI API key.
        prompts (list[str]): A list of prompt templates loaded from the configuration.
        openai_client (OpenAI): The OpenAI client instance used to interact with the OpenAI API.

    Methods:
        load_prompts(): Loads prompt templates from the configuration or a default source.
        generate_prompt(post_text: str, prompt_tone: str) -> str: Generates a prompt by substituting
            placeholders in a template with the provided post text and tone.
    """

    def __init__(self, config: Config):
        """
        Initializes the PromptManager with the provided configuration.

        Args:
            config (Config): The configuration object containing settings such as the OpenAI API key.
        """
        self.config = config
        self.prompt_tone = self.config.prompt_tone
        self.prompts = self.load_prompts()
        self.openai_client = OpenAI(api_key=self.config.openai_api_key)

    def load_prompts(self) -> List[str]:
        return FileManager.read_prompts()

    async def generate_prompt(
            self,
            message_text: str,
    ) -> str:
        """
        Generates a prompt by inserting the provided post text and tone into a predefined template.

        This method takes the input `message_text` and `prompt_tone`, and substitutes them into the first available
        prompt template from the `self.prompts` list. If no prompts are available, it returns `None`.

        Args:
            message_text (str): The text of the new message to be included in the prompt.
        Returns:
            str: The generated prompt with `{message_text}` and `{prompt_tone}` placeholders replaced by the provided values.
                Returns `None` if no prompt templates are available in `self.prompts`.

        Example:
            >>> self.prompts = ["Write a {prompt_tone} response to: {message_text}"]
            >>> prompt = await generate_prompt("Hello, how are you?", "friendly")
            >>> print(prompt)
            "Write a friendly response to: Hello, how are you?"
        """
        prompt_tone = self.prompt_tone
        prompt = self.prompts[0] if self.prompts else None
        prompt = prompt.replace("{message_text}", message_text)
        prompt = prompt.replace("{prompt_tone}", prompt_tone)
        console.log(self.prompt_tone, prompt)
        return prompt

    async def generate_answer(
            self,
            message_text: str,
    ) -> str | None:
        """
        Generates a response to a given post using the OpenAI ChatGPT model.

        This method creates a prompt based on the provided post text and tone, then sends it to the
        OpenAI API to generate a response. It handles various exceptions that may occur during the
        API request, such as authentication errors, rate limits, and permission issues.

        Args:
            post_text (str): The text of the post to which a response is being generated.

        Returns:
            str | None: The generated response as a string. Returns `None` if the prompt generation fails,
                    an API error occurs, or the response cannot be generated.

        Raises:
            openai.AuthenticationError: If the OpenAI API key is invalid or missing.
            openai.RateLimitError: If the OpenAI API rate limit is exceeded or the account balance is insufficient.
            openai.PermissionDeniedError: If access to the OpenAI API is denied (e.g., due to regional restrictions).
            Exception: If any other unexpected error occurs during the response generation process.

        Example:
            >>> answer = await generate_answer("Hello, how are you?", "friendly")
            >>> print(answer)
            "Hi! I'm doing great, thanks for asking. How about you?"
        """
        prompt = await self.generate_prompt(
            message_text
        )
        if not prompt:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.config.chat_gpt_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant and interesting chatter."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                n=1,
                temperature=0.7
            )
            answer = response.choices[0].message.content
            return answer
        except openai.AuthenticationError:
            console.log("Ошибка авторизации: неверный API ключ", style="red")
        except openai.RateLimitError:
            console.log("Не хватает денег на балансе ChatGPT", style="red")
        except openai.PermissionDeniedError:
            console.log("В вашей стране не работает ChatGPT, включите VPN", style="red")
        except Exception as e:
            logger.error(f"Error while generatin message with prompt: {e}")
            console.log("Ошибка генерации комментария", style="red")
            return None
