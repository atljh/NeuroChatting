import random
import asyncio
import logging

from openai import OpenAI
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.errors.rpcerrorlist import (
    UserBannedInChannelError,
    MsgIdInvalidError
)

from src.logger import console, logger
from src.managers.prompt_manager import PromptManager


class ChatManager:
    """
    A class for managing chats, comments, and interactions with Telegram and OpenAI.
    """
    MAX_SEND_ATTEMPTS = 3

    def __init__(
            self,
            config
    ):
        """
        Initializes the ChatManager.

        Args:
            config: Configuration object containing settings.
        """

        self.config = config
        self._openai_client = None
        self._comment_manager = None
        self.event_handlers = {}

    @property
    def prompt_tone(self) -> str:
        return self.config.prompt_tone

    @property
    def message_limit(self) -> int:
        return self.config.message_limit

    @property
    def send_message_delay(self) -> tuple[int, int]:
        return self.config.send_message_delay

    @property
    def openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=self.config.openai_api_key)
        return self._openai_client

    @property
    def comment_manager(self) -> PromptManager:
        if self._comment_manager is None:
            self._comment_manager = PromptManager(self.config, self.openai_client)
        return self._comment_manager

    async def sleep_before_send_message(self):
        """Random delay before sending a message."""
        min_delay, max_delay = self.send_comment_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Delay before sending message: {delay} seconds")
        await asyncio.sleep(delay)

    async def send_comment(self, client, account_phone: str, channel, comment: str, message_id: int, attempts: int = 0) -> None:
        """
        Sends a comment to the specified channel.

        Args:
            client: The Telethon client.
            account_phone: The phone number of the account.
            channel: The channel to send the comment to.
            comment: The comment text.
            message_id: The ID of the message to reply to.
            attempts: The number of send attempts.
        """
        try:
            channel_entity = await self.get_channel_entity(client, channel)
            if not channel_entity:
                console.log("Channel not found or inaccessible.", style="red")
                return
            await client.send_message(entity=channel_entity, message=comment, comment_to=message_id)
            console.log(f"Comment sent from account {account_phone} to channel {channel.title}", style="green")
        except FloodWaitError as e:
            logging.warning(f"Rate limit exceeded for account {account_phone}. Waiting {e.seconds} seconds.", style="yellow")
            await asyncio.sleep(e.seconds)
            await self.switch_to_next_account()
        except UserBannedInChannelError:
            console.log(f"Account {account_phone} is banned in channel {channel.title}", style="red")
            await self.switch_to_next_account()
        except MsgIdInvalidError:
            console.log("Channel is not linked to a chat.", style="red")
            await self.switch_to_next_account()
        except Exception as e:
            if "private and you lack permission" in str(e) or "You can't write" in str(e):
                console.log(f"Channel {channel.title} is inaccessible for account {account_phone}. Skipping.", style="yellow")
            elif "You join the discussion group before commenting" in str(e):
                console.log("You need to join the discussion group before commenting.")
                join_result = await self.join_discussion_group(client, channel_entity)
                if join_result:
                    await self.send_comment(client, account_phone, channel, comment, message_id)
                    return
            else:
                console.log(f"Error sending comment: {e}", style="red")

            if attempts < self.MAX_SEND_ATTEMPTS:
                console.log(f"Attempt {attempts + 1}/{self.MAX_SEND_ATTEMPTS} to send message from another account...")
                await self.switch_to_next_account()
                next_client = self.accounts.get(self.active_account)
                if next_client:
                    await self.sleep_before_send_message()
                    await self.send_comment(next_client, account_phone, channel, comment, message_id, attempts + 1)
                else:
                    console.log("No available accounts for sending.", style="red")
            else:
                console.log(f"Failed to send message after {self.MAX_SEND_ATTEMPTS} attempts.", style="red")

    async def monitor_groups(
            self,
            client: TelegramClient,
            account_phone: str,
            groups: list
    ) -> None:
        """
        Handles new messages in passed groups

        Args:
            client: TelegramClient.
            account_phone: User phone number (for logs).
            groups: List of groups (link or username).
        """
        try:
            for group in groups:
                client.add_event_handler(
                    lambda event: self.handle_new_message(event, account_phone),
                    events.NewMessage(chats=group)
                )
        except Exception as e:
            console.log("Ошибка при запуске мониторинга групп", style="red")
            logger.error(f"Ошибка при запуске мониторинга групп: {e}")

    async def handle_new_message(
            self,
            event: events.NewMessage.Event,
            account_phone: str
    ) -> None:
        """
        Process new message in group

        Args:
            event: new message event object.
            account_phone: User phone number (for logs).
        """
        try:
            chat_id = event.chat_id
            chat = await event.get_chat()
            chat_title = chat.title if hasattr(chat, "title") else "Unknown Chat"

            message_text = event.message.message

            console.log(
                f"Новое сообщение в группе {chat_title} ({chat_id}): {message_text}",
                style="blue"
            )

            if "привет" in message_text.lower():
                await event.reply("Привет! Как дела?")
                console.log(f"Аккаунт {account_phone} ответил на сообщение в группе {chat_title}.", style="green")

        except Exception as e:
            console.log("Ошибка при обработке нового сообщения", style="red")
            logger.error(f"Ошибка при обработке нового сообщения: {e}")
