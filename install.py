import os
import platform
import subprocess
import sys


def run_script(script_path):
    """Запускает скрипт в зависимости от операционной системы"""
    try:
        if platform.system() == "Windows":
            subprocess.run([script_path], shell=True, check=True)
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            subprocess.run(["bash", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске скрипта: {e}")
        sys.exit(1)


def main():
    if platform.system() == "Windows":
        script_path = "install/install.bat"
    else:
        script_path = "install/install.sh"

    if os.path.exists(script_path):
        print(f"Запуск скрипта {script_path}...")
        run_script(script_path)
    else:
        print(f"Скрипт {script_path} не найден!")


if __name__ == "__main__":
    main()
