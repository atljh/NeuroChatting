import os
import logging
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console


class LoggerManager:
    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        log_file: str = "bot.log",
        max_bytes: int = 5 * 1024 * 1024,  # 5 MB
        backup_count: int = 3,
        file_level: int = logging.INFO,
        console_level: int = logging.INFO,
    ):
        """
        :param name: logger name.
        :param log_dir: directory for logs file.
        :param log_file: logs file name.
        :param max_bytes: Max size of logs file in bytes.
        :param backup_count: Amount of backups files.
        :param file_level: Logging level for file.
        :param console_level: Logging level for console.
        """
        self.name = name
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.file_level = file_level
        self.console_level = console_level

        self._create_log_dir()

        self.console = Console(log_path=False)
        self.logger = self._setup_logger()

    def _create_log_dir(self) -> None:
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Could not create directory for logs: {e}")

    def _setup_logger(self) -> logging.Logger:
        """
        Setup and return logger.

        :return: logger.
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(min(self.file_level, self.console_level))

        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8',
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(self.file_level)

        rich_handler = RichHandler(rich_tracebacks=True)
        rich_handler.setLevel(self.console_level)

        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(rich_handler)

        return logger

    def get_logger(self) -> logging.Logger:
        return self.logger

    def get_console(self) -> Console:
        return self.console


logger_manager = LoggerManager(name="bot_logger")
logger = logger_manager.get_logger()
console = logger_manager.get_console()
