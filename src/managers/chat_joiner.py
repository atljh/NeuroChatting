import random
import asyncio
from enum import Enum

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.errors import (
    UserNotParticipantError,
    FloodWaitError,
    ChatAdminRequiredError
)
from telethon.errors.rpcerrorlist import (
    InviteHashInvalidError,
    InviteHashExpiredError
)
from telethon.tl.functions.channels import (
    JoinChannelRequest,
)
from telethon.tl.functions.messages import ImportChatInviteRequest

from config import Config
from src.managers import BlackList
from src.logger import logger, console


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
        is_private_chat = await self.is_private_chat(client, chat, account_phone)
        console.log(chat, is_private_chat)
        user_in_chat = await self.is_member(client, chat, account_phone)
        if user_in_chat:
            return JoinStatus.ALREADY_JOINED
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
        min_delay, max_delay = self.config.join_delay
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
            if "you are not part of" in str(e):
                return ChatType.GROUP
            logger.error(f"Error trying to determine chat type {chat}: {e}")
            console.log(f"Ошибка при определении типа чата {chat}: {e}", style="red")
            return ChatType.UNKNOWN

    async def _join_channel(
        self,
        client: TelegramClient,
        account_phone: str,
        channel: str
    ) -> JoinStatus:
        """
        Joins a public channel.

        Args:
            channel: The channel username or link.

        Returns:
            JoinStatus: The result of the operation.
        """
        is_private = await self.is_private_chat(
            client, channel, account_phone
        )
        if is_private:
            return await self._join_private_channel(
                client, account_phone, channel
            )
        return await self._join_public_channel(
            client, account_phone, channel
        )

    async def _join_private_channel(
        self,
        client: TelegramClient,
        account_phone: str,
        channel: str
    ) -> JoinStatus:
        if "+" in channel:
            channel = channel.split('+')[1]
        try:
            await self._random_delay()
            await client(ImportChatInviteRequest(channel))
            console.log(
                f"Аккаунт {account_phone} присоединился к приватному каналу {channel}",
                style="green"
            )
            return JoinStatus.OK
        except FloodWaitError as e:
            console.log(
                f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                style="yellow"
            )
            return JoinStatus.FLOOD
        except Exception as e:
            console.log(e, style='red')
            if "is not valid anymore" in str(e):
                console.log(
                    f"Вы забанены в канале {channel}, или такого канала не существует",
                    style="yellow"
                )
                return JoinStatus.BANNED
            elif "A wait of" in str(e):
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.",
                    style="yellow"
                )
                return JoinStatus.FLOOD
            elif "is already" in str(e):
                return JoinStatus.OK
            else:
                logger.error(f"Error while trying to join channel {channel}: {e}")
                console.log(f"Ошибка при присоединении к каналу {channel}: {e}", style="red")
                return JoinStatus.ERROR

    async def _join_public_channel(
            self,
            client: TelegramClient,
            account_phone: str,
            channel: str
    ) -> JoinStatus:
        try:
            await self._random_delay()
            await client(JoinChannelRequest(channel))
            console.log(f"Аккаунт присоединился к каналу {channel}", style="green")
            return JoinStatus.OK
        except Exception as e:
            if "A wait of" in str(e):
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.",
                    style="yellow"
                )
                return JoinStatus.FLOOD
            elif "is not valid" in str(e):
                console.log("Ссылка на чат не рабочая или такого чата не существует", style="yellow")
                return JoinStatus.SKIP
            else:
                logger.error(f"Error while trying to join channel {channel}: {e}")
                console.log(f"Ошибка при подписке на канал {channel}: {e}", style="red")
                return JoinStatus.ERROR

    async def _join_group(
        self,
        client: TelegramClient,
        account_phone: str,
        group: str
    ) -> JoinStatus:
        """
        Joins a group with the specified account.

        Args:
            client: The Telethon client.
            account_phone: The phone number of the account.
            group: The group to join.

        Returns:
            JoinStatus: The result of the operation.
        """
        is_private = await self.is_private_chat(
            client, group, account_phone
        )
        if is_private:
            return await self._join_private_group(
                client, account_phone, group
            )
        return await self._join_public_group(
            client, account_phone, group
        )

    async def _join_private_group(
            self,
            client: TelegramClient,
            account_phone: str,
            group: str
    ) -> JoinStatus:
        if "+" in group:
            group = group.split('+')[1]
        try:
            await self._random_delay()
            await client(ImportChatInviteRequest(group))
            console.log(
                f"Аккаунт {account_phone} присоединился к приватному чату {group}",
                style="green"
            )
            return JoinStatus.OK
        except Exception as e:
            if "is not valid anymore" in str(e):
                console.log(
                    f"Аккаунт {account_phone} забанен в чате {group}, или ссылка не действительная. "
                    "Добавляем в черный список.",
                    style="red"
                )
                return JoinStatus.BANNED
            elif "successfully requested to join" in str(e):
                console.log(f"Заявка на подписку в {group} отправлена.", style="yellow")
                return JoinStatus.SKIP
            elif "A wait of" in str(e):
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                    style="yellow"
                )
                return JoinStatus.FLOOD

    async def _join_public_group(
            self,
            client: TelegramClient,
            account_phone: str,
            group: str
    ) -> JoinStatus:
        try:
            await self._random_delay()
            await client(JoinChannelRequest(group))
            console.log(f"Аккаунт присоединился к группе {group}", style="green")
            return JoinStatus.OK
        except FloodWaitError as e:
            console.log(
                f"Слишком много запросов от аккаунта {account_phone}. Флуд {e.seconds} секунд.",
                style="yellow"
            )
            return JoinStatus.FLOOD
        except Exception as e:
            if "successfully requested to join" in str(e):
                console.log(f"Заявка на подписку в {group} уже отправлена.", style="yellow")
                return JoinStatus.SKIP
            elif "The chat is invalid" in str(e):
                console.log(f"Чата {group} не существует или ссылка истекла.", style="yellow")
                return JoinStatus.SKIP
            else:
                logger.error(f"Ошибка при присоединении к группе {group}: {e}")
                console.log(f"Ошибка при присоединении к группе {group}: {e}", style="red")
                return JoinStatus.ERROR

    async def is_member(
        self,
        client: TelegramClient,
        chat: str,
        account_phone: str
    ) -> bool:
        """
        Checks if the user is a member of the channel or group.

        Args:
            chat: The channel username or link.

        Returns:
            bool: True if the user is a member, False otherwise.
        """
        try:
            chat_entity = await client.get_entity(chat)
            await client.get_permissions(chat_entity, "me")
            return True
        except UserNotParticipantError:
            return False
        except InviteHashExpiredError:
            console.log(
                f"Такого канала не существует или ссылка истекла: {chat}",
                style="yellow"
            )
            return False
        except Exception as e:
            if "private and you lack permission" in str(e):
                console.log(
                    f"Аккаунт {account_phone} забанен в чате {chat_entity.title} добавляем в черный список",
                    style="red"
                )
                self.blacklist.add_to_blacklist(account_phone, chat)
                return "SKIP"
            elif "that you are not" in str(e):
                return False
            logger.error(f"Error processing chat {chat}: {e}")
            console.log(f"Ошибка при обработке чата {chat}: {e}", style="red")
            return False

    async def is_private_chat(
        self,
        client: TelegramClient,
        chat: str,
        account_phone: str
    ) -> bool:
        """
        Checks if group or chat is private

        Args:
            client: TelegramClient.
            group: Channel/group link, or username.

        Returns:
            bool: True, if group/channel is private, else False.
        """
        try:
            entity = await client.get_entity(chat)
            if isinstance(entity, Channel):
                try:
                    if entity.join_request:
                        return True
                    return not entity.username
                except UserNotParticipantError:
                    return True
                except ChatAdminRequiredError:
                    return True
            return False
        except InviteHashInvalidError:
            return True
        except ChatAdminRequiredError:
            return True
        except Exception as e:
            if "you are not part of" in str(e):
                return True
            if "A wait of" in str(e):
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}, ожидание {e.seconds} секунд",
                    style="yellow"
                )
                return
            logger.error(f"Ошибка при определении типа группы/канала {chat}: {e}")
            console.log(f"Ошибка при определении типа группы/канала {chat}: {e}", style="red")
            return False
