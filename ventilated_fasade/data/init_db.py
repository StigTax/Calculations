import sqlite3
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import INSUL_DB_NAME, DATA_FILE

CREATE_MATERIALS_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL UNIQUE,
    material_type TEXT NOT NULL,
    construction TEXT NOT NULL,
    product_name_en TEXT NOT NULL,
    product_name_ru TEXT NOT NULL,
    volume REAL NOT NULL,
    length INTEGER NOT NULL CHECK(length > 0),
    width INTEGER NOT NULL CHECK(width > 0),
    thickness INTEGER NOT NULL CHECK(thickness BETWEEN 30 AND 200),
    lambda_d REAL NOT NULL,
    lambda_a REAL NOT NULL,
    lambda_b REAL NOT NULL
);
'''


def transform_item(item):
    """Трансформирует элемент из JSON в формат для базы данных."""
    return {
        "product_code": item["product_code"],
        "material_type": item["material_type"],
        "construction": item["construction"],
        "product_name_en": item["product_name (EN)"],
        "product_name_ru": item["product_name (RU)"],
        "volume": float(item["volume (pcs), m3"]),
        "length": int(item["length (pcs), mm"]),
        "width": int(item["width (pcs), mm"]),
        "thickness": int(item["height/thickness (pcs), mm"]),
        "lambda_d": float(item["λd, W/m*K"]),
        "lambda_a": float(item["λа, W/m*K"]),
        "lambda_b": float(item["λb, W/m*K"]),
    }


def initial_db():
    """Создание таблиц и загрузка данных из JSON, если таблица пуста."""
    try:
        with sqlite3.connect(INSUL_DB_NAME) as con:
            cur = con.cursor()
            cur.execute(CREATE_MATERIALS_TABLE_SQL)

            cur.execute("SELECT COUNT(*) FROM materials;")
            count = cur.fetchone()[0]

            if count == 0:
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r', encoding='utf-8') as file:
                        data = json.load(file)

                    for raw_item in data:
                        item = transform_item(raw_item)
                        cur.execute('''
                            INSERT INTO materials (
                                product_code, material_type, construction,
                                product_name_en, product_name_ru,
                                volume, length, width, thickness,
                                lambda_d, lambda_a, lambda_b
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            item["product_code"],
                            item["material_type"],
                            item["construction"],
                            item["product_name_en"],
                            item["product_name_ru"],
                            item["volume"],
                            item["length"],
                            item["width"],
                            item["thickness"],
                            item["lambda_d"],
                            item["lambda_a"],
                            item["lambda_b"],
                        ))
                    print(f"Загружено {len(data)} записей из фикстуры.")
                else:
                    print(f"Файл фикстур {DATA_FILE} не найден.")
            else:
                print("Таблица 'materials' уже содержит данные.")
    except sqlite3.Error as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка при загрузке данных из JSON: {e}")


if __name__ == "__main__":
    initial_db()
