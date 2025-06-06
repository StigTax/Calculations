import math
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import materials

logger = logging.getLogger(__name__)


class InsulationCalculator:
    """Класс для расчета теплоизоляции."""

    def __init__(
        self,
        materials_ru_name: str,
        area_m2: float,
        building_height_m: float,
        count_corner: int,
        perimeter_m: int
    ):
        """Инициализация калькулятора теплоизоляции."""
        logger.info("Инициализация InsulationCalculator")

        self.materials_ru_name = materials_ru_name
        self.area_m2 = area_m2
        self.building_height_m = building_height_m
        self.count_corner = count_corner
        self.perimeter_m = perimeter_m

        logger.debug(
            f"Параметры: материал='{materials_ru_name}', "
            f"площадь={area_m2}, высота={building_height_m}, "
            f"углы={count_corner}, периметр={perimeter_m}"
        )

        self.materials_data = (
            materials.get_materials_by_ru_name(materials_ru_name)
        )

        if not self.materials_data:
            logger.error(
                f'Материал "{materials_ru_name}" не найден в базе данных'
            )
            raise ValueError(
                f'Материалы с названием "{materials_ru_name}" '
                'не найдены в базе данных.'
            )

    def get_sheet_area(self) -> float:
        """Расчет площади одного листа материала."""
        material = self.materials_data[0]
        length_m = material['length'] / 1000
        width_m = material['width'] / 1000
        area_per_sheet = length_m * width_m
        logger.debug(f"Площадь одного листа: {area_per_sheet:.3f} м²")
        return area_per_sheet

    def get_total_height_build(self) -> float:
        """Расчет суммарной высоты углов здания."""
        total_height = self.building_height_m * self.count_corner
        logger.debug(f"Суммарная высота углов: {total_height:.2f} м")
        return total_height

    def get_bandaging_the_corner(self) -> float:
        """Расчет площади перевязки углов."""
        material = self.materials_data[0]
        thickness_m = material['thickness'] / 1000
        bandaging_corner_m2 = self.get_total_height_build() * thickness_m
        logger.debug(f"Площадь перевязки углов: {bandaging_corner_m2:.3f} м²")
        return bandaging_corner_m2

    def get_sheets_needed(self) -> int:
        """Расчет необходимого количества листов материала."""
        area_per_sheet = self.get_sheet_area()
        total_area_build = self.area_m2 + self.get_bandaging_the_corner()
        sheets_needed = math.ceil(total_area_build / area_per_sheet)
        logger.debug(
            f"Общая площадь: {total_area_build:.2f} м², "
            f"Необходимое количество листов: {sheets_needed}"
        )
        return sheets_needed

    def get_total_volume(self) -> float:
        """Расчет общего объема материала."""
        sheets_needed = self.get_sheets_needed()
        volume_per_sheet = self.materials_data[0]['volume']
        total_volume = sheets_needed * volume_per_sheet
        logger.debug(f"Общий объем материала: {total_volume:.3f} м³")
        return round(total_volume, 3)

    def get_thickness_fasteners(self) -> str:
        """Расчет длины крепежа для фасадного анкера."""
        material = self.materials_data[0]
        thickness_material_mm = material['thickness']
        thickness_fasteners = thickness_material_mm + 45
        result = (
            f'Фасадный анкер длиной {thickness_fasteners} мм '
            f'для толщины МВП {thickness_material_mm} мм'
        )
        logger.debug(f"Расчет длины крепежа: {result}")
        return result

    def get_count_fasteners(self) -> int:
        """Расчет количества крепежей для фасадного анкера."""
        sheets = self.get_sheets_needed()
        count = sheets * 5
        logger.debug(f"Количество крепежей: {count}")
        return count

    def summary(self) -> dict:
        """Сводная информация по расчету теплоизоляции."""
        logger.info("Формирование сводной информации по расчету")
        material = self.materials_data[0]
        result = {
            "SKU": material["product_code"],
            "Наименование материала": self.materials_ru_name,
            "Площадь фасада": self.area_m2,
            "Высота здания": self.building_height_m,
            "Периметр": self.perimeter_m,
            "Количесто внешних углов здания": self.count_corner,
            "Площадь теплоизоляции": self.area_m2 + self.get_bandaging_the_corner(),
            "Количество МВП (шт)": self.get_sheets_needed(),
            "Объем МВП": self.get_total_volume(),
            "Длина крепежа": self.get_thickness_fasteners(),
            "Количество крепежа": self.get_count_fasteners(),
        }
        logger.debug(f"Результаты расчета: {result}")
        return result
