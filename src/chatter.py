import os
from pathlib import Path

from config import Config
from src.thon import BaseThon
from src.managers import (
    ChatJoiner, FileManager,
    JoinStatus, BlackList
)
from src.managers.chat_manager import ChatManager
from src.logger import logger, console


class Chatter(BaseThon):
    """
    A class responsible for managing the joining and monitoring of Telegram groups for a specific account.

    Attributes:
        item (Path): The path to the session file for the account.
        config (Config): Configuration settings for the application.
        json_file (Path): The path to the JSON file containing account data.
        blacklist (BlackList): An instance of the BlackList class to manage blacklisted groups.
        file_manager (FileManager): An instance of the FileManager class to handle file operations.
        chat_joiner (ChatJoiner): An instance of the ChatJoiner class to manage joining groups.
        chat_manager (ChatManager): An instance of the ChatManager class to monitor groups.
        account_phone (str): The phone number of the account derived from the session file name.
        groups (list): A list of groups the account has joined or is monitoring.
    """

    def __init__(
        self,
        item: Path,
        json_file: Path,
        json_data: dict,
        config: Config,
    ):
        """
        Initializes the Chatter class with the necessary configurations and instances.

        Args:
            item (Path): The path to the session file for the account.
            json_file (Path): The path to the JSON file containing account data.
            json_data (dict): The data loaded from the JSON file.
            config (Config): Configuration settings for the application.
        """
        super().__init__(item=item, json_data=json_data)
        self.item = item
        self.config = config
        self.json_file = json_file
        self.blacklist = BlackList()
        self.file_manager = FileManager()
        self.chat_joiner = ChatJoiner(config)
        self.chat_manager = ChatManager(config)
        self.account_phone = os.path.basename(self.item).split('.')[0]
        self.groups = []

    async def _start(self):
        """
        Starts the process of joining and monitoring groups for the account.

        Returns:
            bool: The status of the chat handler after starting.
        """
        console.log(
            f"Аккаунт {self.account_phone} начал работу",
        )
        await self._join_groups()
        handler_status = await self._start_chat_handler()
        return handler_status

    async def _join_groups(self) -> None:
        """
        Joins the groups listed in the groups file, skipping blacklisted groups.
        """
        for group in self.file_manager.read_groups():
            if self.blacklist.is_group_blacklisted(
                self.account_phone, group
            ):
                console.log(f"Группа {group} в черном списке, пропускаем")
                continue
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
        Handles the status after attempting to join a group.

        Args:
            status (JoinStatus): The status of the join attempt.
            account_phone (str): The phone number of the account.
            chat (str): The name or identifier of the group.
        """
        match status:
            case JoinStatus.OK:
                console.log(
                    f"Аккаунт {account_phone} успешно вступил в {chat}",
                    style="green"
                )
                self.groups.append(chat)
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
                self.blacklist.add_to_blacklist(account_phone, chat)
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
                self.groups.append(chat)
            case JoinStatus.REQUEST_SEND:
                console.log(
                    f"Заявка на подписку в чат {chat} уже отправлена",
                    style="yellow"
                )
            case JoinStatus.ERROR:
                console.log(
                    f"Произошла ошибка при вступлении в чат {chat}, {account_phone}",
                    style="red"
                )
            case _:
                logger.error(f"Unknown JoinStatus: {status}")
                console.log(f"Неизвестный статус: {status}")

    async def _start_chat_handler(self) -> bool:
        """
        Starts monitoring the groups the account has joined.

        Returns:
            bool: True if monitoring started successfully, False otherwise.
        """
        if not len(self.groups):
            console.log("Нет групп для обработки", style="red")
            return False
        console.log(
            f"Мониторинг групп начат для аккаунта {self.account_phone}",
            style="green"
        )
        try:
            status = await self.chat_manager.monitor_groups(
                self.client, self.account_phone, self.groups
            )
            return status
        except Exception as e:
            logger.error(f"Error on monitor groups: {e}")
            console.log('Ошибка при обработке групп', style='yellow')

    async def _main(self) -> str:
        """
        Main method to check the account status and start the group joining and monitoring process.

        Returns:
            str: The result of the account status check.
        """
        r = await self.check()
        if "OK" not in r:
            return r
        await self._start()
        return r

    async def main(self) -> str:
        """
        Public method to execute the main functionality of the Chatter class.

        Returns:
            str: The result of the account status check.
        """
        r = await self._main()
        return r
