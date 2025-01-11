import asyncio
import random
from enum import Enum

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.errors import UserNotParticipantError, FloodWaitError
from telethon.errors.rpcerrorlist import (
    InviteHashExpiredError
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from src.logger import logger, console
from src.managers import BlackList
from config import Config


class ChatType(Enum):
    CHANNEL = "channel"
    GROUP = "group"
    UNKNOWN = "unknown"


class JoinStatus(Enum):
    OK = "OK"
    SKIP = "SKIP"
    BANNED = "BANNED"
    FLOOD = "FLOOD"
    ERROR = "ERROR"
    ALREADY_JOINED = "ALREADY_JOINED"


class ChatJoiner:
    """
    Class to handle joining Telegram channels and groups.
    """
    def __init__(
            self,
            config: Config
    ):
        """
        Initializes the ChannelJoiner.

        Args:
            client: The Telethon client.
            join_delay: A tuple (min_delay, max_delay) for random delay before joining.
        """
        self.blacklist = BlackList()
        self.config = config

    async def join(
        self,
        client: TelegramClient,
        account_phone: str,
        chat: str
    ) -> JoinStatus:
        """
        Joins a chat (channel or group).

        Args:
            client: The Telethon client instance.
            account_phone: The phone number of the account.
            chat: The chat link or username.

        Returns:
            JoinStatus: The result of the operation.
        """
        chat_type = await self.detect_chat(client, chat)
        print(chat, chat_type)
        if chat_type == ChatType.UNKNOWN:
            return JoinStatus.ERROR

        if chat_type == ChatType.CHANNEL:
            return await self._join_channel(client, account_phone, chat)
        elif chat_type == ChatType.GROUP:
            return await self._join_group(client, account_phone, chat)

    async def _random_delay(self):
        """
        Sleeps for a random duration between min_delay and max_delay.
        """
        min_delay, max_delay = self.config.join_group_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед вступлением в чат: {delay} секунд")
        await asyncio.sleep(delay)

    def clean_chat_link(self, chat_link: str) -> str:
        if chat_link.startswith("https://t.me/"):
            chat_link = chat_link[13:]
        chat_link = chat_link.split("?")[0]
        return chat_link

    async def detect_chat(
        self,
        client: TelegramClient,
        chat: str
    ) -> ChatType:
        """
        Detect chat type
        Args:
            chat: chat link or username.

        Returns:
            ChatType: Chat type (CHANNEL, GROUP or UNKNOWN).
        """
        try:
            chat = self.clean_chat_link(chat)

            entity = await client.get_entity(chat)

            if isinstance(entity, Channel):
                if entity.megagroup:
                    return ChatType.GROUP
                else:
                    return ChatType.CHANNEL
            elif isinstance(entity, Chat):
                return ChatType.GROUP
            else:
                return ChatType.UNKNOWN
        except Exception as e:
            logger.error(f"Error trying to determine chat type {chat}: {e}")
            console.log(f"Ошибка при определении типа чата {chat}: {e}", style="red")
            return ChatType.UNKNOWN

    async def _join_channel(
        self,
        client: TelegramClient,
        account_phone: str,
        channel: str
    ) -> str:
        """
        Joins a public channel.

        Args:
            channel: The channel username or link.

        Returns:
            bool: True if joined successfully, False otherwise.
        """
        try:
            is_member = await self.is_member(client, channel, account_phone)
            if is_member:
                return "OK"
        except InviteHashExpiredError:
            self.channels.remove(channel)
            console.log(
                f"Такого канала не существует или ссылка истекла: {channel}",
                style="yellow"
            )
        except Exception:
            try:
                await self._random_delay()
                await client(ImportChatInviteRequest(channel[6:]))
                console.log(
                    f"Аккаунт {account_phone} присоединился к приватному каналу {channel}",
                    style="green"
                )
                return True
            except FloodWaitError as e:
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                    style="yellow"
                )
                return "SKIP"
            except Exception as e:
                console.log(e, style='red')
                if "is not valid anymore" in str(e):
                    console.log(
                        f"Вы забанены в канале {channel}, или такого канала не существует",
                        style="yellow"
                    )
                    return "OK"
                elif "A wait of" in str(e):
                    console.log(
                        f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.",
                        style="yellow"
                    )
                    return
                elif "is already" in str(e):
                    return
                else:
                    logger.error(f"Error while trying to join channel {channel}: {e}")
                    console.log(f"Ошибка при присоединении к каналу {channel}: {e}", style="red")
                    return
        try:
            await self._random_delay()
            await client(JoinChannelRequest(channel))
            console.log(f"Аккаунт присоединился к каналу {channel}", style="green")
        except Exception as e:
            if "A wait of" in str(e):
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.",
                    style="yellow"
                )
                return
            elif "is not valid" in str(e):
                console.log("Ссылка на чат не рабочая или такого чата не существует", style="yellow")
                return
            else:
                logger.error(f"Error while trying to join channel {channel}: {e}")
                console.log(f"Ошибка при подписке на канал {channel}: {e}", style="red")
                return

    async def _join_group(
        self,
        client: TelegramClient,
        account_phone: str,
        group: str
    ) -> str:
        """
        Joins a group with the specified account.

        Args:
            client: The Telethon client.
            account_phone: The phone number of the account.
            group: The group to join.

        Returns:
            str: "OK" on success, "SKIP" on failure.
        """
        try:
            is_member = await self.is_member(client, group, account_phone)
            if is_member:
                return "OK"
        except Exception:
            try:
                await self._random_delay()
                await client(ImportChatInviteRequest(group))
                console.log(
                    f"Аккаунт {account_phone} присоединился к приватному чату {group}",
                    style="green"
                )
                return "OK"
            except Exception as e:
                if "is not valid anymore" in str(e):
                    console.log(
                        f"Аккаунт {account_phone} забанен в чате {group}. Добавляем в черный список.",
                        style="red"
                    )
                    self.blacklist.add_to_blacklist(account_phone, group)
                    return "SKIP"
                elif "successfully requested to join" in str(e):
                    console.log(f"Заявка на подписку в {group} уже отправлена.", style="yellow")
                    return "SKIP"
                elif "A wait of" in str(e):
                    console.log(
                        f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                        style="yellow"
                    )
                    return "SKIP"
                else:
                    logger.error(f"Error joining group {group}: {e}")
                    console.log(f"Ошибка при вступлении в группу {group}: {e}", style="red")
                    return "SKIP"
        try:
            await self._random_delay()
            await client(JoinChannelRequest(group))
            console.log(f"Аккаунт присоединился к группе {group}", style="green")
            return "OK"
        except FloodWaitError as e:
            console.log(
                f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                style="yellow"
            )
            return "SKIP"
        except Exception as e:
            if "successfully requested to join" in str(e):
                console.log(f"Заявка на подписку в {group} уже отправлена.", style="yellow")
                return "SKIP"
            elif "The chat is invalid" in str(e):
                console.log(f"Чата {group} не существует или ссылка истекла.", style="yellow")
                self.blacklist.add_to_blacklist(account_phone, group)
                return "SKIP"
            else:
                logger.error(f"Error joining group {group}: {e}")
                console.log(f"Ошибка при присоединении к группе {group}: {e}", style="red")
                return "SKIP"

    async def is_member(
            self,
            client: TelegramClient,
            chat_link: str,
            account_phone: str) -> bool:
        """
        Checks if the user is a member of the channel or group.

        Args:
            chat: The channel username or link.

        Returns:
            bool: True if the user is a member, False otherwise.
        """
        try:
            chat = await client.get_entity(chat_link)
            await client.get_permissions(chat, "me")
            return True
        except UserNotParticipantError:
            return False
        except Exception as e:
            if "private and you lack permission" in str(e):
                console.log(
                    f"Аккаунт {account_phone} забанен в чате {chat.title} добавляем в черный список",
                    style="red"
                )
                self.blacklist.add_to_blacklist(account_phone, chat_link)
                return "SKIP"
            logger.error(f"Error processing chat {chat}: {e}")
            console.log(f"Ошибка при обработке чата {chat}: {e}", style="red")
            return False
