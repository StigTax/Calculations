from data import materials

class InsulationCalculator:
    """Класс для расчета теплоизоляции."""

    def __init__(self, materials_ru_name: str, area_m2: float):
        """
        Инициализация калькулятора теплоизоляции.
        Args:
            materials_ru_name (str): Название материала на русском языке.
            area_m2 (float): Площадь в квадратных метрах.
        """
        self.materials_ru_name = materials_ru_name
        self.area_m2 = area_m2
        self.materials = materials.get_materials_by_ru_name(materials_ru_name)

        if not self.materials:
            raise ValueError(
                f'Материалы с названием "{materials_ru_name}"'
                'не найдены в базе данных.')

    def get_sheet_area(self) -> float:
        """
        Возвращвет площадь одного листа материала в м2
        """
        material = self.materials[0]
        length_m = material['length'] / 1000
        width_m = material['width'] / 1000
        area_per_sheet = length_m * width_m
        return area_per_sheet

    def get_sheets_needed(self) -> int:
        """
        Возвращает количество листов материала,
        необходимых для покрытия заданной площади.
        """
        area_per_sheet = self.get_sheet_area()
        sheets_needed = self.area_m2 / area_per_sheet
        return int(sheets_needed) + (sheets_needed % 1 > 0)

    def get_total_volume(self) -> float:
        """
        Возвращает общий объем материала в м3,
        необходимый для покрытия заданной площади.
        """
        sheets_needed = self.get_sheets_needed()
        volume_per_sheet = self.materials[0]['volume']
        total_volume = sheets_needed * volume_per_sheet
        return total_volume

    def summary(self) -> dict:
        """Возвращает словарь с итогами расчета."""
        material = self.materials[0]
        return {
            "product_code": material["product_code"],
            "product_name": self.materials_ru_name,
            "area_m2": self.area_m2,
            "sheets_needed": self.get_sheets_needed(),
            "total_volume_m3": round(self.get_total_volume(), 3),
        }


if __name__ == "__main__":
    calc = InsulationCalculator(
        materials_ru_name='Vetonit ВентФасад-Низ-100/610x1170/E /T',
        area_m2=100
    )
    print(calc.summary())
