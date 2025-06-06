import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.calc_app import InsulationCalculatorApp
from data.init_db import initial_db

REQUIRED_DEPENDENCIES = [
    'openpyxl',
    'reportlab'
]

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
    missing_deps = []
    for dep in REQUIRED_DEPENDENCIES:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)

    if missing_deps:
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

    return True


def initialize_database():
    """Инициализирует базу данных."""
    try:
        from data.init_db import initial_db
        initial_db()
        return True
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'Ошибка инициализации БД',
            f'Не удалось инициализировать базу данных:\n{e}'
        )
        return False


def initialize_database():
    """Инициализирует базу данных."""
    try:
        initial_db()
        return True
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'Ошибка инициализации БД',
            f'Не удалось инициализировать базу данных:\n{e}'
        )
        return False


def main():
    """Главная функция запуска приложения."""
    print('Запуск калькулятора теплоизоляции НФС v2.0...')

    if not check_dependencies():
        return

    if not initialize_database():
        return

    try:
        app = InsulationCalculatorApp()
        app.mainloop()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'Ошибка запуска',
            f'Не удалось запустить приложение:\n{e}'
        )


if __name__ == '__main__':
    main()