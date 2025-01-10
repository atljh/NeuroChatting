import os
import sys
from typing import List, Dict

from src.logger import console


class FileManager:
    """Class for file managment"""

    @staticmethod
    def read_groups(
        file: str = 'groups.txt'
    ) -> List[str]:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                return [
                    line.strip().replace(" ", "").replace("https://", "")
                    for line in f.readlines()
                    if len(line.strip()) > 5
                ]
        except FileNotFoundError:
            console.log("Файл groups.txt не найден", style="bold red")
            sys.exit(1)

    @staticmethod
    def read_prompts(
        file: str = 'prompts.txt'
    ) -> List[str]:
        prompts = []
        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        prompts.append(line)
            return prompts
        except FileNotFoundError:
            console.log("Файл prompts.txt не найден", style="bold red")
            sys.exit(1)

    @staticmethod
    def read_blacklist(
        file: str = 'blacklist.txt'
    ) -> Dict[str, List[str]]:
        """
        return
            {account_phone: [groups]}
        """
        blacklist = {}
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                console.log(
                    f"Файл {file} создан, так как он отсутствовал.",
                    style="bold yellow"
                )
            return blacklist

        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        phone, group = line.strip().split(':', 1)
                        if phone not in blacklist:
                            blacklist[phone] = []
                        blacklist[phone].append(group)
                    except ValueError:
                        console.log(
                            f"Ошибка формата строки в файле {file}: {line}",
                            style="bold red"
                        )
        except IOError as e:
            console.log(
                f"Ошибка при чтении файла {file}: {e}",
                style="bold red"
            )
        return blacklist

    @staticmethod
    def add_to_blacklist(
        account_phone: str,
        group: str,
        file: str = 'blacklist.txt'
    ) -> bool:
        try:
            with open(file, 'a', encoding='utf-8') as f:
                f.write(f"{account_phone}:{group}\n")
            console.log(
                f"Группа {group} добавлена в черный список для аккаунта {account_phone}.",
                style="yellow"
            )
            return True
        except IOError as e:
            console.log(
                f"Ошибка при добавлении в черный список: {e}",
                style="red"
            )
            return False
