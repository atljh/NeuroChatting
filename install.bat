@echo off
REM Выход при ошибке
setlocal enabledelayedexpansion

REM Цвета для вывода
set GREEN=^[[32m
set NC=^[[0m

echo !GREEN!🔹 Создание виртуального окружения...!NC!
python -m venv venv

echo !GREEN!🔹 Активация виртуального окружения...!NC!
call venv\Scripts\activate.bat

echo !GREEN!🔹 Установка Poetry...!NC!
python -m pip install --upgrade pip
python -m pip install poetry

echo !GREEN!🔹 Установка зависимостей через Poetry...!NC!
poetry install --no-root --all-extras --with=dev

echo !GREEN!✅ Установка завершена! Запустите бота командой:!NC!
echo !GREEN!venv\Scripts\activate.bat && poetry run python main.py!NC!

pause
