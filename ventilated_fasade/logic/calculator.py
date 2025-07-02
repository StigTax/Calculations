from data.models import Product
from data.materials import GetInsulationMaterials

import math
import os
import sys
import logging
from typing import Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logger = logging.getLogger(__name__)


class InsulationCalculator:
    """Калькулятор расчета фасадной теплоизоляции."""

    def __init__(
        self,
        outer_material_ru_name: str,
        inner_material_ru_name: Optional[str] = None,
        area_m2: float = 0,
        building_height_m: float = 0,
        count_corner: int = 0,
        perimeter_m: int = 0,
        repo: Optional[GetInsulationMaterials] = None
    ):
        logger.info("Инициализация InsulationCalculator")

        self.outer_material_ru_name = outer_material_ru_name
        self.inner_material_ru_name = inner_material_ru_name
        self.area_m2 = area_m2
        self.building_height_m = building_height_m
        self.count_corner = count_corner
        self.perimeter_m = perimeter_m
        self.is_double_layer = inner_material_ru_name is not None

        logger.debug(
            f"Параметры: внешний материал='{outer_material_ru_name}', "
            f"внутренний материал='{inner_material_ru_name}', "
            f"площадь={area_m2}, высота={building_height_m}, "
            f"углы={count_corner}, периметр={perimeter_m}"
        )

        repo = repo or GetInsulationMaterials()

        # Основной слой (внешний) обязателен
        self.outer_product = repo.get_materials_by_ru_name(
            outer_material_ru_name
        )
        if not self.outer_product:
            logger.error(f'Материал "{outer_material_ru_name}" не найден')
            raise ValueError(f'Материал "{outer_material_ru_name}" не найден')
        self.outer_product = self.outer_product[0]

        # Внутренний слой (второй) опционален
        if self.is_double_layer:
            self.inner_product = repo.get_materials_by_ru_name(
                inner_material_ru_name
            )
            if not self.inner_product:
                logger.error(f'Материал "{inner_material_ru_name}" не найден')
                raise ValueError(f'Материал "{inner_material_ru_name}" не найден')
            self.inner_product = self.inner_product[0]

    def get_sheet_area(self, product: Product) -> float:
        if product.size is None:
            raise ValueError('Размер материала не задан')
        return (product.size.length_mm / 1000) * (product.size.width_mm / 1000)

    def get_total_height_build(self) -> float:
        return self.building_height_m * self.count_corner

    def get_bandaging_the_corner(self, product: Product) -> float:
        if product.thickness is None:
            raise ValueError('Толщина материала не задана')
        return self.get_total_height_build() * (product.thickness.thickness_mm / 1000)

    def calculate_layer(self, product: Product, area: float) -> Tuple[int, float]:
        area_per_sheet = self.get_sheet_area(product)
        sheets_needed = math.ceil(area / area_per_sheet)
        if product.volume_m3 is None:
            raise ValueError('Отсутствует объем материала')
        total_volume = sheets_needed * product.volume_m3
        return sheets_needed, round(total_volume, 3)

    def get_fastener_length(self, product: Product) -> int:
        return product.thickness.thickness_mm + 45

    def get_count_fasteners(self, sheets_needed: int, count_per_sheet: int = 1) -> int:
        return sheets_needed * count_per_sheet

    def summary(self) -> dict:
        logger.info("Формирование отчета по расчету")

        # Всегда рассчитываем внешний слой (основной)
        outer_area = self.area_m2 + self.get_bandaging_the_corner(
            self.outer_product
        )
        outer_sheets, outer_volume = self.calculate_layer(
            self.outer_product, outer_area
        )
        outer_fasteners_count = self.get_count_fasteners(
            outer_sheets, count_per_sheet=5
        )
        outer_fasteners_length = self.get_fastener_length(
            self.outer_product
        )

        result = {
            "system_type": "double" if self.is_double_layer else "single",
            "outer_layer": {
                "material": self.outer_material_ru_name,
                "sheets": outer_sheets,
                "volume": outer_volume,
                "fasteners": {
                    "count": outer_fasteners_count,
                    "length": outer_fasteners_length
                }
            }
        }

        # Добавляем внутренний слой только если он есть
        if self.is_double_layer:
            inner_area = self.area_m2 + self.get_bandaging_the_corner(
                self.inner_product
            )
            inner_sheets, inner_volume = self.calculate_layer(
                self.inner_product, inner_area
            )
            inner_fasteners_count = self.get_count_fasteners(
                inner_sheets, count_per_sheet=1
            )
            inner_fasteners_length = self.get_fastener_length(
                self.inner_product
            )

            result["inner_layer"] = {
                "material": self.inner_material_ru_name,
                "sheets": inner_sheets,
                "volume": inner_volume,
                "fasteners": {
                    "count": inner_fasteners_count,
                    "length": inner_fasteners_length
                }
            }

        return result
