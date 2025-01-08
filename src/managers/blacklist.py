from typing import Dict, List

from src.managers import FileManager


class BlackList:
    """Class to add accounts to blacklist."""

    @staticmethod
    def get_blacklist() -> Dict[str, List[str]]:
        """
        return
            {account_phone: [groups]}
        """
        return FileManager.read_blacklist()

    @staticmethod
    def add_to_blacklist(
        account_phone: str,
        group: str
    ) -> None:
        FileManager.add_to_blacklist(
            account_phone,
            group
        )

    @staticmethod
    def is_group_blacklisted(
        account_phone: str,
        group: str
    ) -> bool:
        blacklist = FileManager.read_blacklist()
        return group in blacklist.get(
            account_phone, []
        )
