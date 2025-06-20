from reports.report_generator import ReportGenerator
from logic.validators import InputValidator, ValidationError
from data.materials import GetInsulationMaterials
from logic.calculator import InsulationCalculator
import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog
import os
import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class InsulationCalculatorApp(tk.Tk):
    """Главное окно приложения для расчета теплоизоляции фасадов НФС."""

    def __init__(self):
        """Инициализация главного окна приложения."""
        super().__init__()
        self.title('Калькулятор теплоизоляции для НФС')
        self.geometry('800x600')
        logger.info("Запуск приложения InsulationCalculatorApp")

        try:
            materials = GetInsulationMaterials()
            self.materials_list = materials.get_all_ru_names()
            self.materials_data = materials.get_all_materials()
            logger.info(f"Загружены материалы: {self.materials_list}")
            logger.info(f"Загружены материалы: {self.materials_data}")
        except Exception as e:
            logger.error(f"Не удалось загрузить материалы: {e}", exc_info=True)
            messagebox.showerror(
                "Ошибка", f"Не удалось загрузить материалы: {e}")
            self.materials_list = []
            self.materials_data = []

        self.result = {}
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты интерфейса приложения."""
        menubar = Menu(self)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить как Excel",
                              command=self.save_excel)
        file_menu.add_command(label="Сохранить как PDF", command=self.save_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.calc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_frame, text="Калькулятор")

        self.materials_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.materials_frame, text="Материалы")

        self.create_calc_tab()
        self.create_materials_tab()

    def create_calc_tab(self):

        material_label = ttk.Label(self.calc_frame, text="Выберите материал:")
        material_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.material_cb = ttk.Combobox(
            self.calc_frame, values=self.materials_list, state="readonly")
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
            label = ttk.Label(self.calc_frame, text=label_text)
            label.grid(row=ind, column=0, padx=10, pady=5, sticky='w')

            entry = ttk.Entry(self.calc_frame)
            entry.grid(row=ind, column=1, padx=10, pady=5, sticky='ew')
            self.entries[attr_name] = entry

        calc_btn = ttk.Button(
            self.calc_frame, text='Рассчитать', command=self.calculate)
        calc_btn.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

        self.result_text = tk.Text(self.calc_frame, height=10, width=50)
        self.result_text.grid(
            row=len(fields) + 2,
            column=0,
            columnspan=2,
            padx=10,
            pady=5,
            sticky='nsew'
        )
        self.result_text.config(state='disabled')

        self.calc_frame.grid_columnconfigure(1, weight=1)
        self.calc_frame.grid_rowconfigure(len(fields) + 2, weight=1)

    def create_materials_tab(self):
        filter_frame = ttk.Frame(self.materials_frame)
        filter_frame.pack(fill='x', padx=10, pady=5)
        self.filters = {}
        filter_labels = {
            "product_name_ru": "Название",
            "material_type_type": "Тип материала",
            "size_length_mm": "Длина (мм)",
            "size_width_mm": "Ширина (мм)",
            "thickness_mm": "Толщина (мм)"
        }
        col = 0
        for key, label_text in filter_labels.items():
            lbl = ttk.Label(filter_frame, text=label_text)
            lbl.grid(row=0, column=col, padx=5, pady=5)
            ent = ttk.Entry(filter_frame, width=15)
            ent.grid(row=1, column=col, padx=5, pady=2)
            ent.bind("<Return>", self.on_filter_change)
            self.filters[key] = ent
            col += 1

        columns = (
            "product_code",
            "product_name_ru",
            "volume_m3",
            "construction_name",
            "material_type_name",
            "size_length_mm",
            "size_width_mm",
            "thickness_mm"
        )
        self.materials_tree = ttk.Treeview(
            self.materials_frame,
            columns=columns,
            show="headings"
        )

        # Заголовки колонок
        self.materials_tree.heading(
            "product_code", text="Код продукта", command=lambda: self.sort_tree("product_code", False))
        self.materials_tree.heading("product_name_ru", text="Название (RU)",
                                    command=lambda: self.sort_tree("product_name_ru", False))
        self.materials_tree.heading(
            "volume_m3", text="Объем, м³", command=lambda: self.sort_tree("volume_m3", True))
        self.materials_tree.heading("construction_name", text="Для конструкций",
                                    command=lambda: self.sort_tree("construction_name", False))
        self.materials_tree.heading("material_type_name", text="Тип материала",
                            command=lambda: self.sort_tree("material_type_type", False))
        self.materials_tree.heading(
            "size_length_mm", text="Длина (мм)", command=lambda: self.sort_tree("size_length_mm", True))
        self.materials_tree.heading(
            "size_width_mm", text="Ширина (мм)", command=lambda: self.sort_tree("size_width_mm", True))
        self.materials_tree.heading(
            "thickness_mm", text="Толщина (мм)", command=lambda: self.sort_tree("thickness_mm", True))

        # Можно настроить ширину колонок, например так
        self.materials_tree.column("product_code", width=100, anchor="center")
        self.materials_tree.column("product_name_ru", width=180, anchor="w")
        self.materials_tree.column("volume_m3", width=80, anchor="center")
        self.materials_tree.column(
            "construction_name", width=100, anchor="center")
        self.materials_tree.column(
            "material_type_name", width=100, anchor="center")
        self.materials_tree.column("size_length_mm", width=80, anchor="center")
        self.materials_tree.column("size_width_mm", width=80, anchor="center")
        self.materials_tree.column("thickness_mm", width=80, anchor="center")

        self.materials_tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.load_materials_data(self.materials_data)

        self.sprt_descending = {}

    def load_materials_data(self, data):
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)
        for item in data:
            self.materials_tree.insert(
                "",
                "end",
                values=(
                    item.get("product_code", ""),
                    item.get("product_name_ru", ""),
                    item.get("volume_m3", 0),
                    item.get("construction_name", ""),
                    item.get("material_type_type", ""),
                    item.get("size_length_mm", ""),
                    item.get("size_width_mm", ""),
                    item.get("thickness_mm", ""),
                )
            )

    def on_filter_change(self, event=None):
        filtered = self.materials_data
        for key, entry in self.filters.items():
            value = entry.get().strip().lower()
            if value:
                filtered = [
                    item for item in filtered
                    if value in str(item.get(key, "")).lower()
                ]
        self.filtered_materials = filtered
        self.load_materials_data(self.filtered_materials)

    def sort_tree(self, column, is_numeric):
        descending = self.sprt_descending.get(column, False)
        data = getattr(self, 'filtered_materials', self.materials_data).copy()

        def sort_key(item):
            value = item[column]
            if is_numeric:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return float('-inf') if descending else float('inf')
            return str(value).lower()

        data.sort(key=sort_key, reverse=descending)
        self.filtered_materials = data
        self.load_materials_data(self.filtered_materials)
        self.sprt_descending[column] = not descending

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
            "Версия: 0.1.0 (Альфа-версия)\n"
            "Разработчик: Ефремчев Никита\n"
            "Дата: 2025"
        )


if __name__ == "__main__":
    app = InsulationCalculatorApp()
    app.mainloop()
