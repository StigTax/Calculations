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
    """Класс для расчета теплоизоляции."""

    def __init__(
        self,
        inner_material_ru_name: str,
        outer_material_ru_name: Optional[str] = None,
        area_m2: float = 0,
        building_height_m: float = 0,
        count_corner: int = 0,
        perimeter_m: int = 0,
        repo: Optional[GetInsulationMaterials] = None
    ):
        """Инициализация калькулятора теплоизоляции."""
        logger.info("Инициализация InsulationCalculator")

        self.inner_material_ru_name = inner_material_ru_name
        self.outer_material_ru_name = outer_material_ru_name
        self.area_m2 = area_m2
        self.building_height_m = building_height_m
        self.count_corner = count_corner
        self.perimeter_m = perimeter_m
        self.is_double_layer = outer_material_ru_name is not None

        logger.debug(
            f"Параметры: внутренний материал='{inner_material_ru_name}', "
            f'внешний материал="{outer_material_ru_name}", '
            f"площадь={area_m2}, высота={building_height_m}, "
            f"углы={count_corner}, периметр={perimeter_m}"
        )

        repo = repo or GetInsulationMaterials()
        # Получаем внутренний материал
        self.inner_product = repo.get_materials_by_ru_name(
            inner_material_ru_name)
        if not self.inner_product:
            logger.error(f'Материал "{inner_material_ru_name}" не найден')
            raise ValueError(f'Материал "{inner_material_ru_name}" не найден')
        self.inner_product = self.inner_product[0]

        # Если двойной слой, получаем внешний материал
        if self.is_double_layer:
            self.outer_product = repo.get_materials_by_ru_name(
                outer_material_ru_name)
            if not self.outer_product:
                logger.error(f'Материал "{outer_material_ru_name}" не найден')
                raise ValueError(
                    f'Материал "{outer_material_ru_name}" не найден')
            self.outer_product = self.outer_product[0]

    def get_sheet_area(self, product: Product) -> float:
        """Расчет площади одного листа материала."""
        if product.size is None:
            logger.error('Отсутствуют данные о размере материала')
            raise ValueError('Размер материала не задан')

        length_m = product.size.length_mm / 1000
        width_m = product.size.width_mm / 1000
        area_per_sheet = length_m * width_m
        logger.debug(f"Площадь одного листа: {area_per_sheet:.3f} м²")
        return area_per_sheet

    def get_total_height_build(self) -> float:
        """Расчет суммарной высоты углов здания."""
        total_height = self.building_height_m * self.count_corner
        logger.debug(f"Суммарная высота углов: {total_height:.2f} м")
        return total_height

    def get_bandaging_the_corner(self, product: Product) -> float:
        """Расчет площади перевязки углов."""
        if product.thickness is None:
            logger.error('Отсутствуют данные о толщине материала')
            raise ValueError('Толщина материала не задана')

        thickness_m = product.thickness.thickness_mm / 1000
        bandaging_corner_m2 = self.get_total_height_build() * thickness_m
        logger.debug(f"Площадь перевязки углов: {bandaging_corner_m2:.3f} м²")
        return bandaging_corner_m2

    def calculate_layer(
        self, product: Product, area: float
    ) -> Tuple[int, float]:
        """Расчет параметров для одного слоя."""
        area_per_sheet = self.get_sheet_area(product)
        sheets_needed = math.ceil(area / area_per_sheet)

        if product.volume_m3 is None:
            logger.error('Объем материала не указан')
            raise ValueError('Отсутствует объем материала')

        total_volume = sheets_needed * product.volume_m3
        return sheets_needed, round(total_volume, 3)

    def get_fastener_length(self, product: Product) -> int:
        """Расчет длины крепежа для слоя."""
        return product.thickness.thickness_mm + 45

    def get_count_fasteners(
        self, sheets_needed: int, count_per_sheet: int = 1
    ) -> int:
        """Расчет количества крепежей для фасадного анкера."""
        count = sheets_needed * count_per_sheet
        logger.debug(f"Количество крепежей: {count}")
        return count

    def summary(self) -> dict:
        logger.info("Формирование сводной информации по расчету")

        # Расчет площади с учетом перевязки углов для внутреннего слоя
        inner_area = self.area_m2 + \
            self.get_bandaging_the_corner(self.inner_product)
        inner_sheets, inner_volume = self.calculate_layer(
            self.inner_product, inner_area)
        inner_fasteners_count = self.get_count_fasteners(
            inner_sheets, count_per_sheet=1)
        inner_fasteners_length = self.get_fastener_length(self.inner_product)

        result = {
            "system_type": "double" if self.is_double_layer else "single",
            "inner_layer": {
                "material": self.inner_material_ru_name,
                "sheets": inner_sheets,
                "volume": inner_volume,
                "fasteners": {
                    "count": inner_fasteners_count,
                    "length": inner_fasteners_length
                }
            }
        }

        if self.is_double_layer:
            # Аналогично считаем для внешнего слоя, можно тоже добавить перевязку углов
            outer_area = self.area_m2 + \
                self.get_bandaging_the_corner(self.outer_product)
            outer_sheets, outer_volume = self.calculate_layer(
                self.outer_product, outer_area)
            outer_fasteners_count = self.get_count_fasteners(
                outer_sheets, count_per_sheet=5)
            outer_fasteners_length = self.get_fastener_length(
                self.outer_product)

            result["outer_layer"] = {
                "material": self.outer_material_ru_name,
                "sheets": outer_sheets,
                "volume": outer_volume,
                "fasteners": {
                    "count": outer_fasteners_count,
                    "length": outer_fasteners_length
                }
            }

        return result
