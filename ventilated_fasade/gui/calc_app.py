import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog
import os
import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.calculator import InsulationCalculator
from data import materials
from logic.validators import InputValidator, ValidationError
from reports.report_generator import ReportGenerator


class InsulationCalculatorApp(tk.Tk):
    """Главное окно приложения для расчета теплоизоляции фасадов НФС."""

    def __init__(self):
        """Инициализация главного окна приложения."""
        super().__init__()
        self.title('Калькулятор теплоизоляции для НФС')
        self.geometry('600x500')
        logger.info("Запуск приложения InsulationCalculatorApp")

        try:
            self.materials_list = materials.get_all_ru_names()
            logger.info(f"Загружены материалы: {self.materials_list}")
        except Exception as e:
            logger.error(f"Не удалось загрузить материалы: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось загрузить материалы: {e}")
            self.materials_list = []

        self.result = {}
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты интерфейса приложения."""
        menubar = Menu(self)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить как Excel", command=self.save_excel)
        file_menu.add_command(label="Сохранить как PDF", command=self.save_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

        material_label = ttk.Label(self, text="Выберите материал:")
        material_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.material_cb = ttk.Combobox(self, values=self.materials_list, state="readonly")
        self.material_cb.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        if self.materials_list:
            self.material_cb.set(self.materials_list[0])

        self.entries = {}
        fields = [
            ("Площадь, м²", "area_m2"),
            ("Высота здания, м", "building_height_m"),
            ("Количество углов", "count_corner"),
            ("Периметр, м", "perimeter_m"),
        ]

        for ind, (label_text, attr_name) in enumerate(fields, start=1):
            label = ttk.Label(self, text=label_text)
            label.grid(row=ind, column=0, padx=10, pady=5, sticky='w')

            entry = ttk.Entry(self)
            entry.grid(row=ind, column=1, padx=10, pady=5, sticky='ew')
            self.entries[attr_name] = entry

        calc_btn = ttk.Button(self, text='Рассчитать', command=self.calculate)
        calc_btn.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

        self.result_text = tk.Text(self, height=10, width=50)
        self.result_text.grid(
            row=len(fields) + 2,
            column=0,
            columnspan=2,
            padx=10,
            pady=5,
            sticky='nsew'
        )
        self.result_text.config(state='disabled')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(len(fields) + 2, weight=1)

    def calculate(self):
        """Выполняет расчет теплоизоляции на основе введенных данных."""
        try:
            selected_material = self.material_cb.get()
            if not selected_material:
                logger.warning("Не выбран материал для расчета")
                messagebox.showerror("Ошибка", "Выберите материал")
                return

            values = {}
            for key, entry in self.entries.items():
                value = entry.get().strip()
                if not value:
                    logger.warning(f"Пустое поле ввода: {key}")
                    messagebox.showerror("Ошибка", f"Заполните поле '{key}'")
                    return
                values[key] = value

            area = InputValidator.validate_positive_number(
                values["area_m2"], "Площадь"
            )
            area = InputValidator.validate_area_range(area)

            height = InputValidator.validate_positive_number(
                values["building_height_m"], "Высота здания"
            )
            height = InputValidator.validate_height_range(height)

            corners = InputValidator.validate_positive_integer(
                values["count_corner"], "Количество углов"
            )
            perimeter = InputValidator.validate_positive_integer(
                values["perimeter_m"], "Периметр"
            )

            self.calc = InsulationCalculator(
                materials_ru_name=selected_material,
                area_m2=area,
                building_height_m=height,
                count_corner=corners,
                perimeter_m=perimeter,
            )

            self.result = self.calc.summary()
            logger.info(
                f"Выполнен расчет: материал={selected_material},"
                f" результат={self.result}"
            )

            report_text = '\n'.join(
                f"{key}: {val}" for key, val in self.result.items()
            )
            self.display_result(report_text)

        except ValidationError as e:
            logger.warning(f"Ошибка валидации: {e}")
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            logger.error(f"Ошибка при расчёте: {e}", exc_info=True)
            messagebox.showerror("Ошибка", str(e))

    def display_result(self, text):
        """Отображает результаты расчета в текстовом поле."""
        self.result_text.config(state='normal')
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state='disabled')

    def save_excel(self):
        """Сохраняет результаты расчета в Excel файл."""
        if not hasattr(self, 'result') or not self.result:
            logger.warning("Попытка сохранения отчета без данных")
            messagebox.showerror(
                "Ошибка", "Нет данных для сохранения. "
                "Сначала выполните расчет."
            )
            return
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if filename:
                rg = ReportGenerator(self.calc)
                rg.generate_excel_report(filename)
                logger.info(f"Отчет успешно сохранен в Excel: {filename}")
                messagebox.showinfo(
                    "Успех", f"Отчет успешно сохранен: {filename}"
                )
        except Exception as e:
            logger.error(
                f"Ошибка при сохранении Excel отчета: {e}", exc_info=True
            )
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчет: {e}")

    def save_pdf(self):
        """Сохраняет отчет в формате PDF."""
        if not hasattr(self, 'result') or not self.result:
            logger.warning("Попытка сохранения PDF отчета без данных")
            messagebox.showerror(
                "Ошибка", "Нет данных для сохранения. "
                "Сначала выполните расчет."
            )
            return
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if filename:
                rg = ReportGenerator(self.calc)
                rg.generate_pdf_report(filename)
                logger.info(f"Отчет успешно сохранен в PDF: {filename}")
                messagebox.showinfo(
                    "Успех", f"Отчет успешно сохранен: {filename}"
                )
        except Exception as e:
            logger.error(
                f"Ошибка при сохранении PDF отчета: {e}", exc_info=True
            )
            messagebox.showerror(
                "Ошибка", f"Не удалось сохранить отчет: {e}"
            )

    def show_about(self):
        """Показывает информацию о программе."""
        messagebox.showinfo(
            "О программе",
            "Программа расчета теплоизоляции фасадов НФС\n"
            "Версия: 1.0\n"
            "Разработчик: Ефремчев Никита\n"
            "Дата: 2025"
        )


if __name__ == "__main__":
    app = InsulationCalculatorApp()
    app.mainloop()
