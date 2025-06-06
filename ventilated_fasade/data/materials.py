import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import INSUL_DB_NAME


__all__ = [
    "get_all_materials",
    "get_material_by_code",
    "get_materials_by_ru_name",
    "get_all_ru_names"
]


def get_all_materials():
    """Возвращает все записи из БД."""
    with sqlite3.connect(INSUL_DB_NAME) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM materials;")
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_material_by_code(product_code):
    """Возвращает запись из БД по product_code."""
    with sqlite3.connect(INSUL_DB_NAME) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM materials WHERE product_code = ?;",
            (product_code,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_materials_by_ru_name(product_name_ru):
    """Возвращает все записи из БД по названию материала."""
    with sqlite3.connect(INSUL_DB_NAME) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM materials WHERE product_name_ru = ?;",
            (product_name_ru,)
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_all_ru_names():
    """Возвращает все уникальные русские названия материалов."""
    with sqlite3.connect(INSUL_DB_NAME) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT DISTINCT product_name_ru FROM materials;")
        rows = cur.fetchall()
        return [row["product_name_ru"] for row in rows]
