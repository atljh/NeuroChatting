import asyncio
import random

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    UserNotParticipantError,
    UserBannedInChannelError,
    InviteHashExpiredError,
    InviteHashInvalidError,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest


class ChatJoiner:
    """
    A class to handle joining Telegram channels and groups.
    """
    def __init__(self, client: TelegramClient, join_delay: tuple[int, int] = (5, 10)):
        """
        Initializes the ChannelJoiner.

        Args:
            client: The Telethon client.
            join_delay: A tuple (min_delay, max_delay) for random delay before joining.
        """
        self.client = client
        self.join_delay = join_delay

    async def _random_delay(self):
        """
        Sleeps for a random duration between min_delay and max_delay.
        """
        min_delay, max_delay = self.join_delay
        delay = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def join_channel(self, channel: str) -> bool:
        """
        Joins a public channel.

        Args:
            channel: The channel username or link.

        Returns:
            bool: True if joined successfully, False otherwise.
        """
        try:
            await self._random_delay()
            await self.client(JoinChannelRequest(channel))
            print(f"Successfully joined channel: {channel}")
            return True
        except FloodWaitError as e:
            print(f"FloodWaitError: Need to wait {e.seconds} seconds before joining {channel}.")
            await asyncio.sleep(e.seconds)
            return await self.join_channel(channel)  # Retry after waiting
        except UserBannedInChannelError:
            print(f"User is banned in channel: {channel}.")
            return False
        except Exception as e:
            print(f"Failed to join channel {channel}: {e}")
            return False

    async def join_group(self, invite_link: str) -> bool:
        """
        Joins a private group using an invite link.

        Args:
            invite_link: The invite link (e.g., "https://t.me/joinchat/abc123").

        Returns:
            bool: True if joined successfully, False otherwise.
        """
        try:
            await self._random_delay()
            await self.client(ImportChatInviteRequest(invite_link.split("/")[-1]))
            print(f"Successfully joined group: {invite_link}")
            return True
        except FloodWaitError as e:
            print(f"FloodWaitError: Need to wait {e.seconds} seconds before joining {invite_link}.")
            await asyncio.sleep(e.seconds)
            return await self.join_group(invite_link)  # Retry after waiting
        except (InviteHashExpiredError, InviteHashInvalidError):
            print(f"Invite link is invalid or expired: {invite_link}.")
            return False
        except UserBannedInChannelError:
            print(f"User is banned in group: {invite_link}.")
            return False
        except Exception as e:
            print(f"Failed to join group {invite_link}: {e}")
            return False

    async def is_member(self, channel: str) -> bool:
        """
        Checks if the user is a member of the channel or group.

        Args:
            channel: The channel username or link.

        Returns:
            bool: True if the user is a member, False otherwise.
        """
        try:
            entity = await self.client.get_entity(channel)
            await self.client.get_permissions(entity, "me")
            return True
        except UserNotParticipantError:
            return False
        except Exception as e:
            print(f"Error checking membership for {channel}: {e}")
            return False
