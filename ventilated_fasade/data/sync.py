import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .models import (
    Base, ConstructionType, MaterialType, Size, Thickness, Product)


logger = logging.getLogger('insulation.sync')


def load_fixture_data(path):
    logger.info(f'Загрузка даных из фикстуры: {path}')
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.info(f'Загружено {len(data)} записей из фикстуры')
        return data
    except FileNotFoundError:
        logger.error(f'Файл фикстуры не найден: {path}')
        raise
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка чтения JSON: {e}')
        raise
    except Exception as e:
        logger.error(f'Неизвестная ошибка при загрузке фикстуры: {e}')
        raise


def sync_db_with_fixture(fixture_path, db_url):
    try:
        logger.info('Синхронизация базы данных с фикстурой...')
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info('Соединение с базой данных установлено')
        data = load_fixture_data(fixture_path)
    except SQLAlchemyError as e:
        logger.error(f'Ошибка соединения с базой данных: {e}')
        raise
    except Exception as e:
        logger.error(f'Неизвестная ошибка при синхронизации: {e}')
        raise

    def safe_float(value, default=0.0):
        """Преобразует значение в float, возвращает default при ошибке."""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    try:

        def upser(model_class, items, key='id'):
            updated, added = 0, 0
            for item in items:
                obj = session.get(model_class, item[key])
                if obj:
                    changed = False
                    for attr, value in item.items():
                        if getattr(obj, attr) != value:
                            setattr(obj, attr, value)
                            changed = True
                    if changed:
                        logger.debug(
                            f'Обновление: {model_class.__name__} {item[key]}'
                        )
                        updated += 1
                else:
                    logger.debug(
                        f'Добавление: {model_class.__name__} {item[key]}'
                    )
                    session.add(model_class(**item))
                    added += 1
            return updated, added

        total_updated, total_added = 0, 0

        for model_class, key in [
            (ConstructionType, 'id'),
            (MaterialType, 'id'),
            (Size, 'id'),
            (Thickness, 'id'),
        ]:
            logger.info(f'Обработка {model_class.__name__}...')
            added, updated = upser(
                model_class, data[model_class.__name__], key)
            total_added += added
            total_updated += updated
            logger.info(
                f'{model_class.__name__}: +{added}, ~{updated}'
            )

        logger.info('Обработка продуктов...')
        existing_product = {
            p.product_code: p for p in session.query(Product).all()}
        fixture_codes = set()
        product_added, product_updated = 0, 0

        required_keys = [
            'product_code', 'product_name_ru', 'product_name_en',
            'construction_id', 'material_type_id', 'size_id', 'thickness_id'
        ]

        for item in data['products']:
            missing = [key for key in required_keys if key not in item]
            if missing:
                logger.error(
                    f'Пропущены обязательные ключи в продукте: {missing}\n'
                    f'Продукт: {item}'
                )
                continue
            fixture_codes.add(item['product_code'])

            product_data = {
                "product_code": item["product_code"],
                "product_name_ru": item["product_name_ru"],
                "product_name_en": item["product_name_en"],
                "volume_m3": safe_float(item.get("volume_m3", 0)),
                "lambda_d": safe_float(item.get("lambda_d", 0)),
                "lambda_a": safe_float(item.get("lambda_a", 0)),
                "lambda_b": safe_float(item.get("lambda_b", 0)),
                "construction_id": item.get("construction_id"),
                "material_type_id": item.get("material_type_id"),
                "size_id": item.get("size_id"),
                "thickness_id": item.get("thickness_id")
            }

            if item['product_code'] in existing_product:
                product = existing_product[item['product_code']]
                changed = False
                for key, value in product_data.items():
                    if getattr(product, key) != value:
                        setattr(product, key, value)
                        changed = True
                if changed:
                    logger.debug(
                        f'Обновление продукта: {item["product_code"]}'
                    )
                    product_updated += 1
            else:
                logger.debug(
                    f'Добавление продукта: {item["product_code"]}'
                )
                session.add(Product(**product_data))
                product_added += 1

        to_delete = set(existing_product.keys()) - fixture_codes
        for code in to_delete:
            logger.debug(f'Удаление продукта: {code}')
            session.delete(existing_product[code])

        session.commit()

        logger.info(
            f'✓ MaterialTypes, ConstructionTypes, Sizes & Thicknesses: +{total_added}, ~{total_updated}')
        logger.info(
            f'✓ Products: +{product_added}, ~{product_updated}, -{len(to_delete)}')
        logger.info('Синхронизация завершена успешно.')

    except SQLAlchemyError as e:
        logger.error(f'Ошибка при работе с БД: {e}')
        session.rollback()
    except KeyError as e:
        logger.error(f'Ошибка в структуре данных: отсутствует ключ {e}')
        session.rollback()
    except Exception as e:
        logger.exception(f'Неожиданная ошибка при синхронизации: {e}')
        session.rollback()
    finally:
        session.close()
        logger.info('Сессия закрыта.')
