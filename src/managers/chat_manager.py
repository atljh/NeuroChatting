import random
import asyncio
from enum import Enum

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.errors import (
    FloodWaitError, UserBannedInChannelError, UserNotParticipantError, ChatWriteForbiddenError,
    ChatAdminRequiredError, UserIsBlockedError, InputUserDeactivatedError,
    PeerFloodError, ChannelPrivateError, UsernameNotOccupiedError,
    InviteRequestSentError, InviteHashExpiredError, ChatSendMediaForbiddenError,
    UserDeactivatedBanError, MsgIdInvalidError
)

from src.logger import console, logger
from src.managers.prompt_manager import PromptManager


class SendMessageStatus(Enum):
    OK = "OK"
    SKIP = "SKIP"
    FLOOD = "FLOOD"
    BANNED = "BANNED"
    USER_BANNED = "USER_BANNED"
    ERROR = "ERROR"


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
    def answer_manager(self) -> PromptManager:
        if self._answer_manager is None:
            self._answer_manager = PromptManager(self.config)
        return self._answer_manager

    async def sleep_before_send_message(self) -> None:
        """Random delay before sending a message."""
        min_delay, max_delay = self.send_message_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед отправкой сообщения: {delay} секунд")
        await asyncio.sleep(delay)

    async def send_answer(
            self,
            event: events.NewMessage.Event,
            account_phone: str,
            group: str
    ) -> SendMessageStatus:
        try:
            await event.reply("Привет! Как дела?")
        except FloodWaitError:
            return SendMessageStatus.FLOOD
        except PeerFloodError:
            return SendMessageStatus.FLOOD
        except UserBannedInChannelError:
            return SendMessageStatus.BANNED
        except MsgIdInvalidError:
            return SendMessageStatus.BANNED
        except UserDeactivatedBanError:
            return SendMessageStatus.USER_BANNED
        except ChatWriteForbiddenError:
            return SendMessageStatus.BANNED
        except ChatSendMediaForbiddenError:
            return SendMessageStatus.SKIP
        except Exception as e:
            if "private and you lack permission" in str(e):
                return SendMessageStatus.BANNED
            elif "You can't write" in str(e):
                return SendMessageStatus.BANNED
            elif "CHAT_SEND_PHOTOS_FORBIDDEN" in str(e):
                return SendMessageStatus.SKIP
            elif "A wait of" in str(e):
                return SendMessageStatus.FLOOD
            elif "TOPIC_CLOSED" in str(e):
                return SendMessageStatus.SKIP
            elif "invalid permissions" in str(e):
                return SendMessageStatus.BANNED
            elif "The chat is restricted" in str(e):
                return SendMessageStatus.BANNED
            elif "CHAT_SEND_PLAIN_FORBIDDEN" in str(e):
                return SendMessageStatus.BANNED
            else:
                console.log(f"Ошибка при отправке сообщения в группу {group}, {account_phone}: {e}", style="red")
            return "SKIP"
        return "OK"

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
                    lambda event: self.handle_new_message(event, group, account_phone),
                    events.NewMessage(chats=group)
                )
        except Exception as e:
            console.log("Ошибка при запуске мониторинга групп", style="red")
            logger.error(f"Error running group monitoring: {e}")

    async def handle_new_message(
            self,
            event: events.NewMessage.Event,
            group_link: str,
            account_phone: str
    ) -> None:
        """
        Process new message in group

        Args:
            event: new message event object.
            account_phone: User phone number (for logs).
        """
        try:
            chat = await event.get_chat()
            chat_title = chat.title if hasattr(chat, "title") else "Unknown Chat"

            message_text = event.message.message

            console.log(
                f"Новое сообщение в группе {chat_title} ({group_link})",
                style="blue"
            )
            await self.sleep_before_send_message()
            result = await self.send_answer(event, account_phone, group_link)
            console.log(f"Аккаунт {account_phone} ответил на сообщение в группе {chat_title}.", style="green")

        except Exception as e:
            console.log("Ошибка при обработке нового сообщения", style="red")
            logger.error(f"Error process new message: {e}")
