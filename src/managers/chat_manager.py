import random
import asyncio
from enum import Enum
from typing import List

from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, UserBannedInChannelError, ChatWriteForbiddenError,
    PeerFloodError, ChatSendMediaForbiddenError,
    UserDeactivatedBanError, MsgIdInvalidError
)
from src.logger import console, logger
from src.chatgpt import ChatGPTClient
from src.managers import BlackList, FileManager
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
        self.reaction_mode = config.reaction_mode
        self.keywords_file = config.keywords_file
        self.reaction_interval = config.reaction_interval
        self._messages_count = 0
        self._monitoring_active = True
        self._event_handlers = {}
        self._prompt_manager = PromptManager(self.config)
        self._chatgpt_client = ChatGPTClient(self.config)
        self._blacklist_manager = BlackList()

    @property
    def message_limit(self) -> int:
        return self.config.message_limit

    @property
    def send_message_delay(self) -> tuple[int, int]:
        return self.config.send_message_delay

    async def sleep_before_send_message(self) -> None:
        """Random delay before sending a message."""
        min_delay, max_delay = self.send_message_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед отправкой сообщения: {delay} секунд")
        await asyncio.sleep(delay)

    async def send_answer(
        self,
        event: events.NewMessage.Event,
        answer_text: str,
        account_phone: str,
        group_link: str
    ) -> SendMessageStatus:
        try:
            await event.reply(answer_text)
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
                logger.error(f"Error sending answer to group {group_link}: {account_phone}, {e}")
                console.log(f"Ошибка при отправке сообщения в группу {group_link}, {account_phone}", style="red")
            return SendMessageStatus.ERROR
        return SendMessageStatus.OK

    async def monitor_groups(
        self,
        client: TelegramClient,
        account_phone: str,
        groups: List[str]
    ) -> None:
        """
        Monitors groups for new messages and handles them.

        Args:
            client: The Telegram client instance.
            account_phone: The phone number of the account.
            groups: A list of group links or usernames to monitor.
        """
        try:
            for group in groups:
                def handler(event, group=group):
                    return self.handle_new_message(event, group, account_phone)
                client.add_event_handler(
                    handler,
                    events.NewMessage(chats=group)
                )
                self._event_handlers[group] = handler

            while self._monitoring_active:
                await asyncio.sleep(1)

        except Exception as e:
            console.log("Ошибка при запуске мониторинга групп", style="red")
            logger.error(f"Error running group monitoring: {e}")
        finally:
            await self.stop_monitoring(client)
            return True

    async def stop_monitoring(self, client: TelegramClient) -> None:
        """
        Stops monitoring and removes all event handlers.

        Args:
            client: The Telegram client instance.
        """
        self._monitoring_active = False

        for group, handler in self._event_handlers.items():
            client.remove_event_handler(handler, events.NewMessage(chats=group))

        if client.is_connected():
            await client.disconnect()

    async def handle_new_message(
        self,
        event: events.NewMessage.Event,
        group_link: str,
        account_phone: str
    ) -> None:
        """
        Handles a new message in a group based on the reaction mode.

        Args:
            event: The event containing the new message.
            group_link: The link to the group.
            account_phone: The phone number of the account.
        """
        try:
            if not self._monitoring_active:
                return
            message_text = event.message.message.lower()

            if self.reaction_mode == 'keywords':
                should_react = await self.handle_message_with_keywords(message_text)
            elif self.reaction_mode == 'interval':
                should_react = await self.handle_message_with_interval()
            else:
                should_react = True

            if not should_react:
                return

            chat = await event.get_chat()
            chat_title = getattr(chat, "title", "Unknown Chat")
            console.log(
                f"Новое сообщение в группе {chat_title} ({group_link})",
                style="blue"
            )
            prompt = await self._prompt_manager.generate_prompt(message_text)
            answer_text = await self._chatgpt_client.generate_answer(prompt)

            await self.sleep_before_send_message()

            answer_status = await self.send_answer(
                event, answer_text, account_phone, group_link
            )
            await self.handle_answer_status(answer_status, group_link, account_phone)

            if answer_status == SendMessageStatus.OK:
                await self.check_for_limit(event)

        except Exception as e:
            console.log(f"Ошибка при обработке нового сообщения: {e}", style="red")
            logger.error(f"Error handling new message: {e}")

    async def handle_message_with_keywords(
            self,
            message_text: str,
    ) -> bool:
        """
        Checks if the message contains any of the predefined keywords.

        Args:
            message_text: The text of the message.

        Returns:
            bool: True if the message contains keywords, otherwise False.
        """
        keywords = FileManager.read_keywords(self.keywords_file)
        if not any(keyword in message_text for keyword in keywords):
            console.log("Сообщение не содержит ключевых слов. Пропускаем.", style="yellow")
            return False
        return True

    async def handle_message_with_interval(
            self,
    ) -> bool:
        """
        Checks if the bot should react to the message based on the interval.

        Returns:
            bool: True if the bot should react, otherwise False.
        """
        if not hasattr(self, "_message_counter"):
            self._message_counter = 0

        self._message_counter += 1
        if self._message_counter < self.reaction_interval:
            console.log(
                f"Сообщение #{self._message_counter} проигнорировано (интервал: {self.reaction_interval}).",
                style="yellow"
            )
            return False
        self._message_counter = 0
        return True

    async def handle_answer_status(
            self,
            status: SendMessageStatus,
            group_link: str,
            account_phone: str
    ) -> SendMessageStatus:
        """
        Handles the status of a sent message and performs corresponding actions.

        This method processes the status of a message sent to a group and performs specific actions
        based on the status, such as logging success, handling errors, or adding the group to a blacklist.

        Args:
            status (SendMessageStatus): The status of the sent message (e.g., OK, SKIP, FLOOD, BANNED).
            group_link (str): The link to the group where the message was sent.
            account_phone (str): The phone number of the account used to send the message.

        Returns:
            SendMessageStatus: The same status that was passed to the method.
        """
        match status:
            case SendMessageStatus.OK:
                console.log(
                    f"Сообщение успешно отправлено в группу {group_link} от аккаунта {account_phone}.",
                    style="green"
                )
            case SendMessageStatus.SKIP:
                console.log(
                    f"Сообщение пропущено для группы {group_link} (аккаунт {account_phone}).",
                    style="yellow"
                )
            case SendMessageStatus.FLOOD:
                console.log(
                    f"Аккаунт {account_phone} достиг лимита запросов для группы {group_link}. Необходимо подождать.",
                    style="yellow"
                )
            case SendMessageStatus.BANNED:
                console.log(
                    f"Аккаунт {account_phone} забанен в группе {group_link}. Добавляем группу в чёрный список.",
                    style="red"
                )
                self._blacklist_manager.add_to_blacklist(
                    account_phone, group_link
                )
            case SendMessageStatus.USER_BANNED:
                console.log(
                    f"Пользователь в группе {group_link} забанен. Сообщение не отправлено (аккаунт {account_phone}).",
                    style="red"
                )
            case SendMessageStatus.ERROR:
                console.log(
                    f"Ошибка при отправке сообщения в группу {group_link} от аккаунта {account_phone}.",
                    style="red"
                )
                logger.error(f"Ошибка при отправке сообщения в группу {group_link} от аккаунта {account_phone}.")
            case _:
                console.log(
                    f"Неизвестный статус отправки сообщения: {status} (группа {group_link}, аккаунт {account_phone}).",
                    style="red"
                )

        return status

    async def check_for_limit(
        self,
        event: events.NewMessage.Event
    ) -> None:
        self._messages_count += 1
        console.log(
            f"Отправлено сообщений: {self._messages_count}/{self.message_limit}",
            style="green"
        )
        if self._messages_count >= self.message_limit:
            console.log(
                "Достигнут лимит сообщений. Останавливаем мониторинг.",
                style="yellow"
            )
            await self.stop_monitoring(event.client)
