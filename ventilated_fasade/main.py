from gui.calc_app import InsulationCalculatorApp
from data.sync import sync_db_with_fixture
import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


REQUIRED_DEPENDENCIES = [
    'openpyxl',
    'reportlab',
    'sqlalchemy'
]
FIXTURE_PATH = 'assets/material.json'  # путь к JSON с данными фикстуры
DB_URL = 'sqlite:///insulation.db'
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

log_filename = os.path.join(LOG_DIR, 'insulation_calculator.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(funcName)s]: %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Проверка наличия необходимых библиотек."""
    logger.info('Начата проверка наличия необходимых библиотек...')
    missing_deps = []
    for dep in REQUIRED_DEPENDENCIES:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)

    if missing_deps:
        logger.error(f'Отсутствуют необходимые библиотеки: {missing_deps}')
        root = tk.Tk()
        root.withdraw()
        message = (
            'Отсутствуют необходимые библиотеки:\n' +
            '\n'.join(f'• {dep}' for dep in missing_deps) +
            '\n\nУстановите их командой:\n' +
            f'pip install {" ".join(missing_deps)}\n\n' +
            'Или запустите install_dependencies.py'
        )
        messagebox.showerror('Недостающие зависимости', message)
        return False
    logger.info('Все необходимые библиотеки присутствуют.')
    return True


def initialize_database():
    """Инициализирует базу данных."""
    logger.info('Начата инициализация базы данных...')
    try:
        sync_db_with_fixture(FIXTURE_PATH, DB_URL)
        logger.info('База данных успешно инициализирована.')
        return True
    except Exception as e:
        logger.error(f'Ошибка инициализации БД: {e}', exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'Ошибка инициализации БД',
            f'Не удалось инициализировать базу данных:\n{e}'
        )
        return False


def main():
    """Главная функция запуска приложения."""
    logger.info('Запуск калькулятора теплоизоляции НФС v0.1...')
    print('Запуск калькулятора теплоизоляции НФС v0.1...')

    if not check_dependencies():
        logger.warning('Завершение работы из-за отсутствия зависимостей.')
        return

    if not initialize_database():
        logger.warning('Завершение работы из-за ошибки инициализации БД.')
        return

    try:
        app = InsulationCalculatorApp()
        logger.info('Запуск GUI приложения.')
        app.mainloop()
    except Exception as e:
        logger.error(f'Ошибка запуска приложения: {e}', exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'Ошибка запуска',
            f'Не удалось запустить приложение:\n{e}'
        )


if __name__ == '__main__':
    main()
