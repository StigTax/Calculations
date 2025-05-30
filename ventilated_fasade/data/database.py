import sqlite3

from config import INSUL_DB_NAME


def get_db_connection():
    """"Создание подключения к базе данных."""
    return sqlite3.connect(INSUL_DB_NAME)
