import os
from pathlib import Path

from config import Config
from src.thon import BaseThon
from src.logger import logger
from src.console import console
from src.managers import ChatManager


class Chatter(BaseThon):
    def __init__(
        self,
        item: Path,
        json_file: Path,
        json_data: dict,
        config: Config,
        chat_manager: ChatManager
    ):
        super().__init__(item=item, json_data=json_data)
        self.item = item
        self.config = config
        self.json_file = json_file
        self.account_phone = os.path.basename(self.item).split('.')[0]
        self.chat_manager = chat_manager
        self.chat_manager.add_accounts_to_queue([self.account_phone])
        self.chat_manager.add_account({self.account_phone: self.client})

    async def __main(self):
        await self.chat_manager.join_group(
            self.client, self.account_phone
        )
        console.log(
            f"Аккаунт {self.account_phone} успешно подключен и добавлен в очередь.",
            style="green"
        )
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
        await self.__main()
        return r

    async def main(self) -> str:
        r = await self._main()
        return r
