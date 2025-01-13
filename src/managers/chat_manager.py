import random
import asyncio
import logging

from openai import OpenAI
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

    async def sleep_before_send_message(self) -> None:
        """Random delay before sending a message."""
        min_delay, max_delay = self.send_message_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед отправкой сообщения: {delay} секунд")
        await asyncio.sleep(delay)

    async def send_answer(self, client, account_phone, group):
        try:
            group_entity = await self.get_channel_entity(client, group)
            if not group_entity:
                console.log(f"Группа {group} не найдена или недоступна.", style="red")
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            await client.send_message(
                group, self.post_text,
                parse_mode='HTML'
            )
            console.log(f"Сообщение отправлено от аккаунта {account_phone} в группу {group_entity.title}", style="green")
        except FloodWaitError as e:
            console.log(f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.", style="yellow")
            return "MUTE"
        except PeerFloodError:
            console.log(f"Аккаунт {account_phone} временно заблокирован за спам. Перемещаем аккаунт в папку мут.", style="yellow")
            return "MUTE"
        except UserBannedInChannelError:
            console.log(f"Аккаунт {account_phone} заблокирован в группе {group_entity.title}", style="red")
            self.file_manager.add_to_blacklist(account_phone, group)
            return "OK"
        except MsgIdInvalidError:
            console.log("Канал не связан с чатом", style="red")
            self.file_manager.add_to_blacklist(account_phone, group)
            return "OK"
        except UserDeactivatedBanError:
            console.log(f"Аккаунт {account_phone} забанен", style="red")
            return "ERROR_AUTH"
        except ChatWriteForbiddenError:
            console.log(f"У аккаунта {account_phone} нет прав на отправку сообщений в чат.", style="yellow")
            self.file_manager.add_to_blacklist(account_phone, group)
            return "OK"
        except ChatSendMediaForbiddenError:
            console.log(f"Ошибка: запрещено отправлять фото в этом чате. Повторная отправка без картинки.", style="yellow")
            return "OK"
        except Exception as e:
            if "private and you lack permission" in str(e):
                console.log(f"Группа {group_entity.title} недоступна для аккаунта {account_phone}. Пропускаем.", style="yellow")
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            elif "You can't write" in str(e):
                console.log(f"Группа {group_entity.title} недоступна для аккаунта {account_phone}. Пропускаем.", style="yellow")
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            elif "CHAT_SEND_PHOTOS_FORBIDDEN" in str(e):
                console.log(f"Ошибка: запрещено отправлять фото в этом чате. Повторная отправка без картинки.", style="yellow")
                return "OK"
            elif "A wait of" in str(e):
                console.log(f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.", style="yellow")
                return "MUTE"
            elif "TOPIC_CLOSED" in str(e):
                console.log("Чат с топиками. Пропускаем", style="yellow")
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            elif "invalid permissions" in str(e):
                console.log("Отправка сообщений запрещена. Добавляем в черный список", style='yellow')
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            elif "The chat is restricted" in str(e):
                console.log("Отправка сообщений запрещена. Добавляем в черный список", style='yellow')
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            elif "CHAT_SEND_PLAIN_FORBIDDEN" in str(e):
                console.log("Отправка сообщений запрещена. Добавляем в черный список", style='yellow')
                self.file_manager.add_to_blacklist(account_phone, group)
                return "OK"
            else:
                console.log(f"Ошибка при отправке сообщения в группе {group_entity.title}, {account_phone}: {e}", style="red")
            self.file_manager.add_to_blacklist(account_phone, group)
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
            if "привет" in message_text.lower():
                await event.reply("Привет! Как дела?")
                console.log(f"Аккаунт {account_phone} ответил на сообщение в группе {chat_title}.", style="green")

        except Exception as e:
            console.log("Ошибка при обработке нового сообщения", style="red")
            logger.error(f"Error process new message: {e}")
