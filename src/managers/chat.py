import random
import asyncio
import logging

from openai import OpenAI
from telethon import events
from telethon.errors import UserNotParticipantError, FloodWaitError
from telethon.errors.rpcerrorlist import (
    UserBannedInChannelError,
    MsgIdInvalidError,
    InviteHashExpiredError
)
from telethon.tl.functions.channels import (
    JoinChannelRequest
)
from telethon.tl.functions.messages import (
    ImportChatInviteRequest)

from src.logger import logger
from src.console import console
from src.managers.file import FileManager
from src.managers.prompt import PromptManager


class ChatManager:
    MAX_SEND_ATTEMPTS = 3

    def __init__(self, config):
        self.config = config
        self.prompt_tone = self.config.prompt_tone
        self.sleep_duration = self.config.sleep_duration
        self.comment_limit = self.config.comment_limit
        self.join_channel_delay = self.config.join_channel_delay
        self.send_comment_delay = self.config.send_message_delay
        self.channels = FileManager.read_channels()
        self.openai_client = OpenAI(api_key=config.openai_api_key)
        self.comment_manager = PromptManager(config, self.openai_client)

        self.stop_event = asyncio.Event()

    async def is_participant(self, client, channel):
        try:
            await client.get_permissions(channel, 'me')
            return True
        except UserNotParticipantError:
            return False
        except Exception as e:
            logger.error(f"Ошибка при обработке чата {channel}: {e}")
            console.log(f"Ошибка при обработке чата {channel}: {e}", style="red")
            return False

    async def sleep_before_send_message(self):
        min_delay, max_delay = self.send_comment_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед отправкой сообщения {delay} сек")
        await asyncio.sleep(delay)

    async def sleep_before_enter_chat(self):
        min_delay, max_delay = self.join_channel_delay
        delay = random.randint(min_delay, max_delay)
        console.log(f"Задержка перед вступлением в чат {delay} сек")
        await asyncio.sleep(delay)

    async def join_group(self, client, account_phone, group):
        try:
            entity = await client.get_entity(group)
            is_member = await self.is_participant(client, entity, group, account_phone)
            if is_member:
                return is_member
        except Exception:
            try:
                await self.sleep_before_enter_group()
                await client(ImportChatInviteRequest(group[6:]))
                console.log(f"Аккаунт {account_phone} присоединился к приватной группе {group}", style="green")
                return "OK"
            except Exception as e:
                if "is not valid anymore" in str(e):
                    console.log(f"Аккаунт {account_phone} забанен в чате {group}, добавляем в черный список.", style="red")
                    self.file_manager.add_to_blacklist(account_phone, group)
                    return "SKIP"
                elif "successfully requested to join" in str(e):
                    console.log(f"Запрос на подписку в группу {group} уже отправлен и еще не подтвержден.", style="yellow")
                    return "SKIP"
                elif "A wait of" in str(e):
                    console.log(f"Слишком много запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.", style="yellow")
                    return "SKIP"
                else:
                    console.log(f"Ошибка при присоединении к группе {group}: {e}", style="red")
                    return "SKIP"
        try:
            await self.sleep_before_enter_group()
            await client(JoinChannelRequest(group))
            console.log(f"Аккаунт присоединился к группе {group}", style="green")
        except Exception as e:
            if "successfully requested to join" in str(e):
                console.log(f"Запрос на подписку в группу {group} уже отправлен и еще не подтвержден.", style="yellow")
                return "SKIP"
            elif "The chat is invalid" in str(e):
                console.log("Ссылка на чат {group} не рабочая", style="yellow")
                self.file_manager.add_to_blacklist(account_phone, group)
                return "SKIP"
            else:
                console.log(f"Ошибка при подписке на группу {group}: {e}", style="red")
                return "SKIP"
        return "OK"

    async def monitor_groups(self, client, account_phone):
        if not self.groups:
            console.log("Группы не найдены", style="yellow")
            return
        for group in self.groups:
            try:
                client.add_event_handler(
                    lambda event: self.new_post_handler(client, event, self.prompt_tone, account_phone),
                    events.NewMessage(chats=group)
                )
            except Exception as e:
                console.log(f'Ошибка, {e}', style="red")
        console.log(f"Мониторинг каналов начался для аккаунта {account_phone}...")
        await self.stop_event.wait()

    async def get_channel_entity(self, client, channel):
        try:
            return await client.get_entity(channel)
        except Exception as e:
            console.log(f"Ошибка получения объекта канала: {e}", style="red")
            return None

    async def send_comment(self, client, account_phone, channel, comment, message_id, attempts=0):
        try:
            channel_entity = await self.get_channel_entity(client, channel)
            if not channel_entity:
                console.log("Канал не найден или недоступен.", style="red")
                return
            await client.send_message(
                entity=channel_entity,
                message=comment,
                comment_to=message_id
            )
            console.log(f"Комментарий отправлен от аккаунта {account_phone} в канал {channel.title}", style="green")
            self.account_comment_count[account_phone] = self.account_comment_count.get(account_phone, 0) + 1
            if self.account_comment_count[account_phone] >= self.comment_limit:
                await self.switch_to_next_account()
                await self.sleep_account(account_phone)
        except FloodWaitError as e:
            logging.warning(
                f"Превышен лимит запросов от аккаунта {account_phone}. Ожидание {e.seconds} секунд.", style="yellow"
                )
            await asyncio.sleep(e.seconds)
            await self.switch_to_next_account()
        except UserBannedInChannelError:
            console.log(f"Аккаунт {account_phone}\
                         заблокирован в канале {channel.title}", style="red")
            await self.switch_to_next_account()
        except MsgIdInvalidError:
            console.log("Канал не связан с чатом", style="red")
            await self.switch_to_next_account()
        except Exception as e:
            if "private and you lack permission" in str(e):
                console.log(f"Канал {channel.title} недоступен для аккаунта {account_phone}. Пропускаем.", style="yellow")
            elif "You can't write" in str(e):
                console.log(f"Канал {channel.title} недоступен для аккаунта {account_phone}. Пропускаем.", style="yellow")
            elif "You join the discussion group before commenting" in str(e):
                console.log("Для комментирование необходимо вступить в группу.")
                join_result = await self.join_discussion_group(client, channel_entity)
                if join_result:
                    await self.send_comment(client, account_phone, channel, comment, message_id)
                    return
                else:
                    return
            else:
                console.log(f"Ошибка при отправке комментария: {e}", style="red")

            if attempts < self.MAX_SEND_ATTEMPTS:
                console.log(f"Попытка {attempts + 1}/{self.MAX_SEND_ATTEMPTS} отправить сообщение c другого аккаунта...")
                await self.switch_to_next_account()
                next_client = self.accounts.get(self.active_account)
                if next_client:
                    await self.sleep_before_send_message()
                    await self.send_comment(next_client, account_phone, channel, comment, message_id, attempts + 1)
                else:
                    console.log("Нет доступных аккаунтов для отправки.", style="red")
            else:
                console.log(f"Не удалось отправить сообщение после {self.MAX_SEND_ATTEMPTS} попыток.", style="red")

    async def new_post_handler(self, client, event, prompt_tone, account_phone):
        if account_phone != self.active_account:
            return

        post_text = event.message.message
        message_id = event.message.id
        channel = event.chat

        console.log(f"Новый пост в канале {channel.title} для аккаунта {account_phone}", style="green")

        if self.account_comment_count.get(account_phone, 0) >= self.comment_limit:
            await self.switch_to_next_account()
            await self.sleep_account(account_phone)
            return
        
        comment = await self.comment_manager.generate_comment(post_text, prompt_tone)
        if not comment:
            return

        await self.sleep_before_send_message()
        await self.send_comment(client, account_phone, channel, comment, message_id)
