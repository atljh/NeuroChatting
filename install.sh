#!/bin/bash

# Выход при ошибке
set -e

# Цвета для вывода
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔹 Создание виртуального окружения...${NC}"
python3 -m venv venv

echo -e "${GREEN}🔹 Активация виртуального окружения...${NC}"
source venv/bin/activate

echo -e "${GREEN}🔹 Установка Poetry...${NC}"
pip install --upgrade pip
pip install poetry

echo -e "${GREEN}🔹 Установка зависимостей через Poetry...${NC}"
poetry install --no-root --all-extras --with=dev

echo -e "${GREEN}✅ Установка завершена! Запустите бота командой:${NC}"
echo -e "${GREEN}source venv/bin/activate && poetry run python main.py${NC}"
