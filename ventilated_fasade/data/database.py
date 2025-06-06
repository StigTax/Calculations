import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import INSUL_DB_NAME


def get_db_connection():
    """Создание подключения к базе данных."""
    return sqlite3.connect(INSUL_DB_NAME)
