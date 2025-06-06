import re
from typing import Dict, List, Any, Optional


class ValidationError(Exception):
    """Исключение для ошибок валидации."""

    pass


class InputValidator:
    """Класс для валидации входных данных."""

    @staticmethod
    def validate_positive_number(
        value: Any,
        field_name: str,
        min_value: float = 0.01
    ) -> float:
        """Валидация положительного числа."""
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
    def validate_positive_integer(
        value: Any,
        field_name: str,
        min_value: int = 1
    ) -> int:
        """Валидация положительного целого числа."""
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
        if area > 10000:  # Максимум 10000 м²
            raise ValidationError("Площадь не может превышать 10000 м²")
        return area

    @staticmethod
    def validate_height_range(height: float) -> float:
        """Валидация диапазона высоты здания."""
        if height > 100:  # Максимум 100 м
            raise ValidationError("Высота здания не может превышать 100 м")
        return height
