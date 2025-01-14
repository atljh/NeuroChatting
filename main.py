import asyncio

from config import ConfigManager, print_config
from src.starter import Starter
from src.logger import console
from src.thon.json_converter import JsonConverter
from src.managers.file_manager import groups
from scripts.authorization import register_user

# register_user()


def main():
    config = ConfigManager.load_config()
    print_config(config, len(groups))
    sessions_count = JsonConverter().main()
    s = Starter(sessions_count, config)
    asyncio.run(s.main())


if __name__ == "__main__":
    main()
