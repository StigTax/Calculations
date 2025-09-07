from sqlalchemy import Column, Float, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ConstructionType(Base):
    """Модель типа конструкций"""
    __tablename__ = 'construction_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    products = relationship('Product', back_populates='construction')


class MaterialType(Base):
    """Модель типа материала."""
    __tablename__ = 'material_types'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)

    products = relationship('Product', back_populates='material_type')


class Size(Base):
    """Модель размеров."""
    __tablename__ = 'sizes'

    id = Column(Integer, primary_key=True)
    length_mm = Column(Integer, nullable=False)
    width_mm = Column(Integer, nullable=False)


class Thickness(Base):
    """Модель толщин."""
    __tablename__ = 'thicknesses'

    id = Column(Integer, primary_key=True)
    thickness_mm = Column(Integer, nullable=False)


class Product(Base):
    """Модель продукции."""
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name_ru = Column(String, nullable=False)
    product_name_en = Column(String, nullable=False)
    volume_m3 = Column(Float, nullable=True)

    construction_id = Column(
        Integer, ForeignKey('construction_types.id'), nullable=True
    )
    material_type_id = Column(
        Integer, ForeignKey('material_types.id'), nullable=True
    )
    size_id = Column(
        Integer, ForeignKey('sizes.id'), nullable=True)
    thickness_id = Column(
        Integer, ForeignKey('thicknesses.id'), nullable=True
    )

    construction = relationship('ConstructionType', back_populates='products')
    material_type = relationship('MaterialType', back_populates='products')
    size = relationship('Size')
    thickness = relationship('Thickness')

    def to_dict(self):
        return {
            'product_name_ru': self.product_name_ru,
            'product_name_en': self.product_name_en,
            'volume_m3': self.volume_m3,
            'construction_id': self.construction_id,
            'material_type_id': self.material_type_id,
            'size_id': self.size_id,
            'thickness_id': self.thickness_id,
        }
