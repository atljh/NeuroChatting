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
            client: TelegramClient,
            join_delay: tuple[int, int] = (5, 10)
    ):
        """
        Initializes the ChannelJoiner.

        Args:
            client: The Telethon client.
            join_delay: A tuple (min_delay, max_delay) for random delay before joining.
        """
        self.client = client
        self.join_delay = join_delay

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
        chat_type = await self.detect_chat(chat)
        if chat_type == ChatType.UNKNOWN:
            return JoinStatus.ERROR

        if chat_type == ChatType.CHANNEL:
            return await self.join_channel(client, account_phone, chat)
        elif chat_type == ChatType.GROUP:
            return await self.join_group(client, account_phone, chat)

    async def _random_delay(self):
        """
        Sleeps for a random duration between min_delay and max_delay.
        """
        min_delay, max_delay = self.join_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед вступлением в чат: {delay} секунд")
        await asyncio.sleep(delay)

    async def detect_chat(
        self,
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
            entity = await self.client.get_entity(chat)
            if isinstance(entity, Channel):
                return ChatType.CHANNEL
            elif isinstance(entity, Chat):
                return ChatType.GROUP
            else:
                logger.error(f"Failed to determine chat type {chat}")
                console.log(f"Ошибка определения типа чата {chat}", style="red")
                return ChatType.UNKNOWN
        except Exception as e:
            logger.error(f"Failed to determine chat type {chat}")
            console.log(f"Ошибка при определении типа чата {chat}: {e}", style="red")
            return ChatType.UNKNOWN

    async def join_channel(
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
            entity = await client.get_entity(channel)
            if await self.is_participant(client, entity):
                return True
        except InviteHashExpiredError:
            self.channels.remove(channel)
            console.log(f"Такого канала не существует или ссылка истекла: {channel}", style="red")
        except Exception:
            try:
                await self.sleep_before_enter_channel()
                await client(ImportChatInviteRequest(channel[6:]))
                console.log(
                    f"Аккаунт {account_phone} присоединился к приватному каналу {channel}"
                )
                return True
            except FloodWaitError as e:
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                    style="yellow"
                )
                return "SKIP"
            except Exception as e:
                if "is not valid anymore" in str(e):
                    console.log(
                        f"Вы забанены в канале {channel}, или такого канала не существует", style="yellow"
                        )
                    return "OK"
                elif "A wait of" in str(e):
                    console.log(
                        f"Слишком много запросов \
                            от аккаунта {account_phone}.\
                            Ожидание {e.seconds} секунд.", style="yellow"
                            )
                    return
                elif "is already" in str(e):
                    return
                else:
                    console.log(f"Ошибка при присоединении к каналу {channel}: {e}")
                    return
        try:
            await self.sleep_before_enter_channel()
            await client(JoinChannelRequest(channel))
            console.log(f"Аккаунт присоединился к каналу {channel}")
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
                console.log(f"Ошибка при подписке на канал {channel}: {e}")
                return

    async def join_group(
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
            entity = await client.get_entity(group)
            is_member = await self.is_participant(client, entity)
            if is_member:
                return "OK"
        except Exception:
            try:
                await self.sleep_before_enter_chat()
                await client(ImportChatInviteRequest(group[6:]))
                console.log(f"Аккаунт {account_phone} присоединился к приватному чату {group}", style="green")
                return "OK"
            except Exception as e:
                if "is not valid anymore" in str(e):
                    console.log(
                        f"Аккаунт {account_phone} забанен в чате {group}. Добавляем в черный список.",
                        style="red"
                    )
                    BlackList.add_to_blacklist(account_phone, group)
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
            await self.sleep_before_enter_chat()
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
                BlackList.add_to_blacklist(account_phone, group)
                return "SKIP"
            else:
                logger.error(f"Error joining group {group}: {e}")
                console.log(f"Ошибка при присоединении к группе {group}: {e}", style="red")
                return "SKIP"

    async def is_member(self, chat: str) -> bool:
        """
        Checks if the user is a member of the channel or group.

        Args:
            chat: The channel username or link.

        Returns:
            bool: True if the user is a member, False otherwise.
        """
        try:
            entity = await self.client.get_entity(chat)
            await self.client.get_permissions(entity, "me")
            return True
        except UserNotParticipantError:
            return False
        except Exception as e:
            logger.error(f"Error processing chat {chat}: {e}")
            console.log(f"Ошибка при обработке чата {chat}: {e}", style="red")
            return False
