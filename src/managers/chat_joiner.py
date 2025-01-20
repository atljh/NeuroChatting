import random
import asyncio
from enum import Enum

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, ChatInviteAlready
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
    JoinChannelRequest
)
from telethon.tl.functions.messages import (
    ImportChatInviteRequest,
    CheckChatInviteRequest
)

from config import Config
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
    ALREADY_JOINED = "ALREADY_JOINED"
    REQUEST_SEND = "REQUEST_SEND"
    ERROR = "ERROR"


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
        self.config = config

    async def join(
        self,
        client: TelegramClient,
        account_phone: str,
        chat_link: str
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
        chat = self.clean_chat_link(chat_link)
        chat_type = await self.detect_chat(client, chat)
        if chat_type == ChatType.UNKNOWN:
            return JoinStatus.ERROR
        elif isinstance(chat_type, JoinStatus):
            return chat_type
        user_in_chat = await self.is_member(client, chat)
        if isinstance(user_in_chat, JoinStatus):
            return user_in_chat
        if user_in_chat:
            return JoinStatus.ALREADY_JOINED

        if chat_type == ChatType.CHANNEL:
            return await self._join_channel(client, account_phone, chat)
        elif chat_type == ChatType.GROUP:
            return await self._join_group(client, account_phone, chat)

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
            client, channel
        )
        if isinstance(is_private, JoinStatus):
            return is_private
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
        if "joinchat" in channel:
            channel = channel.split("/")[2]
        try:
            await self._random_delay()
            await client(ImportChatInviteRequest(channel))
            return JoinStatus.OK
        except FloodWaitError:
            return JoinStatus.FLOOD
        except Exception as e:
            if "is not valid anymore" in str(e):
                return JoinStatus.BANNED
            elif "A wait of" in str(e):
                return JoinStatus.FLOOD
            elif "is already" in str(e):
                return JoinStatus.OK
            else:
                logger.error(f"Error while trying to join channel {account_phone}, {channel}: {e}")
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
            return JoinStatus.OK
        except Exception as e:
            if "A wait of" in str(e):
                return JoinStatus.FLOOD
            elif "is not valid" in str(e):
                return JoinStatus.SKIP
            else:
                logger.error(f"Error while trying to join channel {account_phone}, {channel}: {e}")
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
            client, group
        )
        if isinstance(is_private, JoinStatus):
            return is_private
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
            return JoinStatus.OK
        except Exception as e:
            if "is not valid anymore" in str(e):
                return JoinStatus.SKIP
            elif "successfully requested to join" in str(e):
                return JoinStatus.REQUEST_SEND
            elif "A wait of" in str(e):
                return JoinStatus.FLOOD
            else:
                logger.error(f"Error trying to join group {account_phone}, {group}: {e}")
                return JoinStatus.ERROR

    async def _join_public_group(
            self,
            client: TelegramClient,
            account_phone: str,
            group: str
    ) -> JoinStatus:
        try:
            await self._random_delay()
            await client(JoinChannelRequest(group))
            return JoinStatus.OK
        except FloodWaitError:
            return JoinStatus.FLOOD
        except Exception as e:
            if "successfully requested to join" in str(e):
                return JoinStatus.REQUEST_SEND
            elif "The chat is invalid" in str(e):
                return JoinStatus.SKIP
            else:
                logger.error(f"Error trying to join group {account_phone}, {group}: {e}")
                return JoinStatus.ERROR

    async def is_member(
        self,
        client: TelegramClient,
        chat: str,
    ) -> bool | JoinStatus:
        """
        Checks if the user is a member of the channel or group.

        Args:
            chat: The channel username or link.

        Returns:
            bool: True if the user is a member else False, or JoinStatus in case of error.
        """
        try:
            chat_entity = await client.get_entity(chat)
            await client.get_permissions(chat_entity, "me")
            return True
        except UserNotParticipantError:
            return False
        except InviteHashExpiredError:
            return JoinStatus.SKIP
        except Exception as e:
            if "private and you lack permission" in str(e):
                return JoinStatus.BANNED
            elif "that you are not" in str(e):
                return False
            elif "A wait of" in str(e):
                return JoinStatus.FLOOD
            logger.error(f"Error processing chat {chat}: {e}")
            console.log(f"Ошибка при обработке чата {chat}: {e}", style="red")
            return False

    async def is_private_chat(
        self,
        client: TelegramClient,
        chat: str,
    ) -> bool | JoinStatus:
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
                return JoinStatus.FLOOD
            logger.error(f"Error while trying to detect type of group/channel {chat}: {e}")
            console.log(f"Ошибка при определении типа группы/канала {chat}: {e}", style="red")
            return False

    async def _random_delay(self):
        """
        Sleeps for a random duration between min_delay and max_delay.
        """
        min_delay, max_delay = self.config.join_delay
        delay = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def detect_chat(
        self,
        client: TelegramClient,
        chat_link: str
    ) -> ChatType | JoinStatus:
        """
        Detect chat type
        Args:
            chat: chat link or username.

        Returns:
            ChatType: Chat type (CHANNEL, GROUP or UNKNOWN) or JoinStatus
        """
        try:
            if "joinchat" in chat_link:
                hash = chat_link.split("/")[-1]
                res = await client(CheckChatInviteRequest(hash=hash))

                if isinstance(res, ChatInviteAlready):
                    entity = await client.get_entity(res.chat)
                    if isinstance(entity, Channel):
                        return ChatType.CHANNEL if not entity.megagroup else ChatType.GROUP
                    elif isinstance(entity, Chat):
                        return ChatType.GROUP
                    else:
                        return ChatType.UNKNOWN

                if hasattr(res, 'channel') and res.channel:
                    return ChatType.CHANNEL

            entity = await client.get_entity(chat_link)
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
            elif "A wait of" in str(e):
                return JoinStatus.FLOOD
            logger.error(f"Error trying to determine chat type {chat_link}: {e}")
            console.log(f"Ошибка при определении типа чата {chat_link}", style="red")
            return ChatType.UNKNOWN

    def clean_chat_link(self, chat_link: str) -> str:
        if chat_link.startswith("https://t.me/"):
            chat_link = chat_link[13:]
        chat_link = chat_link.split("?")[0]
        return chat_link
