import os
from typing import List, Dict
from src.logger import console


class FileManager:
    """Manages file operations for groups, prompts, keywords, and blacklists."""

    @staticmethod
    def _read_file(file: str, min_length: int = 0) -> List[str]:
        """
        Reads a file and returns non-empty lines.

        Args:
            file: Path to the file.
            min_length: Minimum line length to include.

        Returns:
            List of non-empty lines.
        """
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                if min_length > 0:
                    lines = [line for line in lines if len(line) >= min_length]
                return lines
        except FileNotFoundError:
            console.log(f"Файл {file} не найден", style="bold red")
            raise
        except IOError as e:
            console.log(f"Ошибка при чтении файла {file}: {e}", style="bold red")
            raise

    @staticmethod
    def read_groups(file: str = 'groups.txt') -> List[str]:
        """
        Reads groups from a file.

        Returns:
            List of groups.
        """
        try:
            groups = [
                line.replace(" ", "").replace("https://", "")
                for line in FileManager._read_file(file, min_length=5)
            ]
            if not groups:
                console.log("Нет групп для обработки", style="red")
            return groups
        except Exception:
            console.log("Ошибка при чтении групп", style="bold red")
            return []

    @staticmethod
    def read_prompts(file: str = 'prompts.txt') -> List[str]:
        """
        Reads prompts from a file.

        Returns:
            List of prompts.
        """
        try:
            prompts = [
                line for line in FileManager._read_file(file)
                if not line.startswith("#")
            ]
            if not prompts:
                console.log("Промпт не найден", style="red")
            return prompts
        except Exception:
            console.log("Ошибка при чтении промптов", style="bold red")
            return []

    @staticmethod
    def read_keywords(file: str = 'key.txt') -> List[str]:
        """
        Reads keywords from a file.

        Returns:
            List of keywords.
        """
        try:
            keywords = [
                line for line in FileManager._read_file(file)
                if not line.startswith("#")
            ]
            if not keywords:
                console.log("Ключевые слова не найдены", style="red")
            return keywords
        except Exception:
            console.log("Ошибка при чтении ключевых слов", style="bold red")
            return []

    @staticmethod
    def read_blacklist(file: str = 'blacklist.txt') -> Dict[str, List[str]]:
        """
        Reads the blacklist from a file.

        Returns:
            Dictionary of account phones and their blacklisted groups.
        """
        blacklist = {}
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                console.log(f"Файл {file} создан, так как он отсутствовал.", style="bold yellow")
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
                        console.log(f"Ошибка формата строки в файле {file}: {line}", style="bold red")
        except IOError as e:
            console.log(f"Ошибка при чтении файла {file}: {e}", style="bold red")
        return blacklist

    @staticmethod
    def add_to_blacklist(account_phone: str, group: str, file: str = 'blacklist.txt') -> bool:
        """
        Adds a group to the blacklist for a specific account.

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(file, 'a', encoding='utf-8') as f:
                f.write(f"{account_phone}:{group}\n")
            console.log(f"Группа {group} добавлена в черный список для аккаунта {account_phone}.", style="yellow")
            return True
        except IOError as e:
            console.log(f"Ошибка при добавлении в черный список: {e}", style="red")
            return False

