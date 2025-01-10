import openai

from src.logger import console
from src.managers.file_manager import FileManager


class PromptManager:
    def __init__(self, config, openai_client):
        self.config = config
        self.client = openai_client
        self.prompts = self.load_prompts()

    def load_prompts(self):
        return FileManager.read_prompts()

    async def generate_prompt(self, post_text, prompt_tone):

        if not len(self.prompts):
            console.log("Промпт не найден")
            return None

        prompt = self.prompts[0] if self.prompts else None
        prompt = prompt.replace("{post_text}", post_text)
        prompt = prompt.replace("{prompt_tone}", prompt_tone)
        return prompt

    async def generate_answer(self, post_text, prompt_tone):
        prompt = await self.generate_prompt(post_text, prompt_tone)
        if not prompt:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.config.chat_gpt_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                n=1,
                temperature=0.7)
            answer = response.choices[0].message.content
            return answer
        except openai.AuthenticationError:
            console.log("Ошибка авторизации: неверный API ключ", style="red")
        except openai.RateLimitError:
            console.log("Не хватает денег на балансе ChatGPT", style="red")
        except openai.PermissionDeniedError:
            console.log("В вашей стране не работает ChatGPT, включите VPN", style="red")
        except Exception as e:
            console.log(f"Ошибка генерации комментария: {e}", style="red")
            return None
