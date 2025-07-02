import re
from typing import Dict, List, Any, Optional


class ValidationError(Exception):
    """Исключение для ошибок валидации."""

    pass


class InputValidator:
    """Класс для валидации входных данных."""

    @staticmethod
    def validate_inputs(raw_data: Dict[str, str]) -> Dict[str, float]:
        """
        Основной метод валидации всех входных данных.

        Args:
            raw_data: Словарь с сырыми данными из полей ввода

        Returns:
            Словарь с валидированными числовыми значениями

        Raises:
            ValidationError: Если какое-либо поле не прошло валидацию
        """
        validated = {}

        try:
            # Валидация площади
            validated['area_m2'] = InputValidator.validate_positive_number(
                raw_data.get('area_m2'),
                "Площадь"
            )
            validated['area_m2'] = InputValidator.validate_area_range(
                validated['area_m2']
            )

            # Валидация высоты здания
            validated['building_height_m'] = InputValidator.validate_positive_number(
                raw_data.get('building_height_m'),
                "Высота здания"
            )
            validated['building_height_m'] = InputValidator.validate_height_range(
                validated['building_height_m']
            )

            # Валидация количества углов
            validated['count_corner'] = InputValidator.validate_positive_integer(
                raw_data.get('count_corner'),
                "Количество углов",
                min_value=0
            )

            # Валидация периметра
            validated['perimeter_m'] = InputValidator.validate_positive_number(
                raw_data.get('perimeter_m'),
                "Периметр"
            )

            return validated

        except KeyError as e:
            raise ValidationError(f"Отсутствует обязательное поле: {e}")

    # Остальные методы остаются без изменений
    @staticmethod
    def validate_positive_number(value: Any, field_name: str, min_value: float = 0.01) -> float:
        """Валидация положительного числа."""
        if value is None or str(value).strip() == "":
            raise ValidationError(f"{field_name} не может быть пустым")

        try:
            num_value = float(value)
            if num_value < min_value:
                raise ValidationError(
                    f"{field_name} должно быть больше {min_value}"
                )
            return num_value
        except ValueError:
            raise ValidationError(f"{field_name} должно быть числом")

    @staticmethod
    def validate_positive_integer(value: Any, field_name: str, min_value: int = 1) -> int:
        """Валидация положительного целого числа."""
        if value is None or str(value).strip() == "":
            raise ValidationError(f"{field_name} не может быть пустым")

        try:
            int_value = int(value)
            if int_value < min_value:
                raise ValidationError(
                    f"{field_name} должно быть больше или равно {min_value}"
                )
            return int_value
        except ValueError:
            raise ValidationError(f"{field_name} должно быть целым числом")

    @staticmethod
    def validate_area_range(area: float) -> float:
        """Валидация диапазона площади."""
        if area > 10000:
            raise ValidationError("Площадь не может превышать 10000 м²")
        return area

    @staticmethod
    def validate_height_range(height: float) -> float:
        """Валидация диапазона высоты здания."""
        if height > 100:
            raise ValidationError("Высота здания не может превышать 100 м")
        return height
