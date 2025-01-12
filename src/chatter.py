import os
from pathlib import Path

from config import Config
from src.thon import BaseThon
from src.managers import (
    ChatManager, ChatJoiner, FileManager, JoinStatus
)
from src.logger import logger, console


class Chatter(BaseThon):
    def __init__(
        self,
        item: Path,
        json_file: Path,
        json_data: dict,
        config: Config,
    ):
        super().__init__(item=item, json_data=json_data)
        self.item = item
        self.config = config
        self.json_file = json_file
        self.chat_manager = ChatManager(config)
        self.chat_joiner = ChatJoiner(config)
        self.file_manager = FileManager()
        self.account_phone = os.path.basename(self.item).split('.')[0]

    async def _start(self):
        console.log(
            f"Аккаунт {self.account_phone} начал работу",
            style="green"
        )
        await self._join_groups()
        console.log(
            f"Аккаунт {self.account_phone} начал мониторинг групп"
        )
        await self._start_chat_handler()

    async def _join_groups(self) -> None:
        for group in self.file_manager.read_groups():
            status = await self.chat_joiner.join(
                self.client, self.account_phone, group
            )
            await self._handle_join_status(
                status, self.account_phone, group
            )

    async def _handle_join_status(
        self,
        status: JoinStatus,
        account_phone: str,
        chat: str
    ) -> None:
        """
        Handle join chat status.

        Args:
            status: JoinStatus
            account_phone: str
            chat: str
        """
        match status:
            case JoinStatus.OK:
                console.log(
                    f"Аккаунт {account_phone} успешно вступил в {chat}",
                    style="green"
                )
            case JoinStatus.SKIP:
                console.log(
                    f"Ссылка на чат {chat} не рабочая или такого чата не существует",
                    style="yellow"
                )
            case JoinStatus.BANNED:
                console.log(
                    f"Аккаунт {account_phone} забанен в чате {chat}, или ссылка не действительная",
                    style="yellow"
                )
            case JoinStatus.FLOOD:
                console.log(
                    f"Слишком много запросов от аккаунта {account_phone}",
                    style="yellow"
                )
            case JoinStatus.ALREADY_JOINED:
                console.log(
                    f"Аккаунт {account_phone} уже состоит в чате {chat}",
                    style="green"
                )
            case JoinStatus.REQUEST_SEND:
                console.log(
                    f"Заявка на подписку в чат {chat} уже отправлена",
                    style="yellow"
                )
            case JoinStatus.ERROR:
                console.log(
                    f"Произошла ошибка при вступлении в чат {account_phone}: {chat}",
                    style="red"
                )
            case _:
                logger.error(f"Неизвестный статус: {status}")
                console.log(f"Неизвестный статус: {status}")

    async def _start_chat_handler(self):
        try:
            await self.chat_manager.monitor_groups(
                self.client, self.account_phone
            )
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            console.log(f'Ошибка {e}', style='yellow')

    async def _main(self) -> str:
        r = await self.check()
        if "OK" not in r:
            return r
        await self._start()
        return r

    async def main(self) -> str:
        r = await self._main()
        return r
