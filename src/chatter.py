import os
from pathlib import Path

from config import Config
from src.thon import BaseThon
from src.managers import ChatManager, ChatJoiner, FileManager
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
            await self.chat_joiner.join(
                self.client, self.account_phone, group
            )

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
