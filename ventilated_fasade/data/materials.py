from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import create_engine

from .models import Product, ConstructionType, MaterialType, Size, Thickness

DB_URL = 'sqlite:///insulation.db'


class GetInsulationMaterials:
    """Класс для получения материалов из базы данных."""

    def __init__(self):
        self.engine = create_engine(DB_URL)
        self.Session = sessionmaker(bind=self.engine)

    def get_all_materials(self):
        """Возвращает все записи из БД."""
        with self.Session() as session:
            query = session.query(
                Product.product_code,
                Product.product_name_ru,
                Product.volume_m3,
                ConstructionType.name.label("construction_name"),
                MaterialType.type.label("material_type_type"),
                Size.length_mm.label("size_length_mm"),
                Size.width_mm.label("size_width_mm"),
                Thickness.thickness_mm.label("thickness_mm"),
            ).join(
                ConstructionType, Product.construction_id == ConstructionType.id
            ).join(
                MaterialType, Product.material_type_id == MaterialType.id
            ).join(
                Size, Product.size_id == Size.id
            ).join(
                Thickness, Product.thickness_id == Thickness.id)

            results = [{
                "product_code": row.product_code,
                "product_name_ru": row.product_name_ru,
                "volume_m3": row.volume_m3,
                "construction_name": row.construction_name,
                "material_type_type": row.material_type_type,
                "size_length_mm": row.size_length_mm,
                "size_width_mm": row.size_width_mm,
                "thickness_mm": row.thickness_mm,
            } for row in query.all()]
            return results

    def get_materials_by_ru_name(self, product_name_ru):
        """Возвращает все записи из БД по названию материала."""
        with self.Session() as session:
            products = session.query(Product).options(
                joinedload(Product.size),
                joinedload(Product.thickness),
                joinedload(Product.construction),
                joinedload(Product.material_type),
            ).filter_by(
                product_name_ru=product_name_ru
            ).all()
            return products

    def get_all_ru_names(self):
        """Возвращает все уникальные русские названия материалов."""
        with self.Session() as session:
            ru_names = session.query(Product.product_name_ru).distinct().all()
            return [name[0] for name in ru_names]
