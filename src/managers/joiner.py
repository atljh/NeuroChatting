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

from src.logger import logger
from src.console import console


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
        console.log(f"Delay before joining chat: {delay} seconds")
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

    async def join_group(self, client, account_phone: str, group: str) -> str:
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
                console.log(f"Account {account_phone} joined private group {group}", style="green")
                return "OK"
            except Exception as e:
                if "is not valid anymore" in str(e):
                    console.log(f"Account {account_phone} is banned in chat {group}. Adding to blacklist.", style="red")
                    FileManager.add_to_blacklist(account_phone, group)
                    return "SKIP"
                elif "successfully requested to join" in str(e):
                    console.log(f"Join request for group {group} is already sent and pending.", style="yellow")
                    return "SKIP"
                elif "A wait of" in str(e):
                    console.log(f"Too many requests from account {account_phone}. Waiting {e.seconds} seconds.", style="yellow")
                    return "SKIP"
                else:
                    console.log(f"Error joining group {group}: {e}", style="red")
                    return "SKIP"
        try:
            await self.sleep_before_enter_chat()
            await client(JoinChannelRequest(group))
            console.log(f"Account joined group {group}", style="green")
            return "OK"
        except Exception as e:
            if "successfully requested to join" in str(e):
                console.log(f"Join request for group {group} is already sent and pending.", style="yellow")
                return "SKIP"
            elif "The chat is invalid" in str(e):
                console.log(f"Chat link {group} is invalid.", style="yellow")
                FileManager.add_to_blacklist(account_phone, group)
                return "SKIP"
            else:
                console.log(f"Error joining group {group}: {e}", style="red")
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
            console.log(f"Error processing chat {chat}: {e}", style="red")
            return False
