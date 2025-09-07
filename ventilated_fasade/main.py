from gui.calc_app import InsulationCalculatorApp
from config import DB_URL, LOG_DIR, REQUIRED_DEPENDENCIES
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from data.models import Base as Material
from data.models_calc import Base as Personal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


os.makedirs(LOG_DIR, exist_ok=True)

log_filename = os.path.join(LOG_DIR, 'insulation_calculator.log')

for h in logging.root.handlers[:]:
    logging.root.removeHandler(h)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_fmt = logging.Formatter(
    fmt="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
file_fmt = logging.Formatter(
    fmt=(
        "%(asctime)s %(levelname)s [%(name)s:%(funcName)s] %(message)s"
    ), datefmt="%Y-%m-%d %H:%M:%S"
)

# Консоль: только INFO+
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_fmt)

# Файл: DEBUG+ с ротацией
file_handler = RotatingFileHandler(
    log_filename, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_fmt)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Подкручиваем шумные библиотеки
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

app_logger = logging.getLogger(__name__)


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
        engine = create_engine(DB_URL)
        Material.metadata.create_all(engine)
        Personal.metadata.create_all(engine)
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
