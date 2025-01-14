import asyncio
from src.logger import console
from src.starter import Starter
from config import ConfigManager, print_config
from src.thon.json_converter import JsonConverter
from src.managers.file_manager import FileManager, groups
from scripts.authorization import register_user


async def run_starter(sessions_count, config):
    starter = Starter(sessions_count, config)
    await starter.main()


def initialize_keywords(config):
    if config.reaction_mode == 'keywords':
        FileManager.read_keywords(config.keywords_file)


def main():
    config = ConfigManager.load_config()
    initialize_keywords(config)
    print_config(config, len(groups))
    sessions_count = JsonConverter().main()
    asyncio.run(run_starter(sessions_count, config))


if __name__ == "__main__":
    # register_user()
    main()
