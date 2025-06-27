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
        """Создает вкладку с интерфейсом калькулятора."""
        # Основной фрейм разделен на 2 колонки: левая (элементы управления) и правая (таблица)
        self.calc_frame.grid_columnconfigure(0, weight=1)  # Левая колонка (элементы)
        self.calc_frame.grid_columnconfigure(2, weight=3)  # Правая колонка (таблица)
        
        # Создаем отдельный фрейм для левой части (элементов управления)
        left_frame = ttk.Frame(self.calc_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Настройка колонок в левом фрейме
        left_frame.grid_columnconfigure(0, weight=1)  # Колонка для labels
        left_frame.grid_columnconfigure(1, weight=1)  # Колонка для полей ввода
        
        # Переносим все элементы управления в left_frame
        # Внутренний слой
        material_label_inner_layers = ttk.Label(
            left_frame,
            text="Выберите материал для внутреннего слоя:"
        )
        material_label_inner_layers.grid(
            row=0,
            column=0,
            padx=10,
            pady=5,
            sticky="w"
        )
        
        self.material_cb = ttk.Combobox(
            left_frame, values=self.materials_list, state="readonly")
        self.material_cb.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
        if self.materials_list:
            self.material_cb.set(self.materials_list[0])
        
        # Внешний слой
        material_label_outer_layer = ttk.Label(
            left_frame,
            text="Выберите материал для внешнего слоя:"
        )
        material_label_outer_layer.grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )

        self.material_cb_outer = ttk.Combobox(
            left_frame, values=self.materials_list, state="readonly"
        )
        self.material_cb_outer.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
        if self.materials_list:
            self.material_cb_outer.set(self.materials_list[0])

        # Поля ввода
        self.entries = {}
        fields = [
            ("Площадь, м²", "area_m2"),
            ("Высота здания, м", "building_height_m"),
            ("Количество углов", "count_corner"),
            ("Периметр, м", "perimeter_m"),
        ]

        for row, (label_text, attr_name) in enumerate(fields, start=4):
            label = ttk.Label(left_frame, text=label_text)
            label.grid(row=row, column=0, padx=10, pady=5, sticky='w')

            entry = ttk.Entry(left_frame)
            entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
            self.entries[attr_name] = entry

        # Кнопки
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(
            row=len(fields)+5,
            column=0, columnspan=2,
            pady=10
        )

        calc_btn = ttk.Button(
            buttons_frame, text='Рассчитать', command=self.calculate)
        calc_btn.pack(side='left', padx=5)

        clear_btn = ttk.Button(
            buttons_frame, text='Очистить', command=self.clear_fields)
        clear_btn.pack(side='left', padx=5)

        # Правая часть - таблица результатов
        self.result_table = ttk.Treeview(
            self.calc_frame,
            columns=("param", "value"),
            show="headings",
            height=20
        )
        self.result_table.heading("param", text='Параметр')
        self.result_table.heading("value", text='Значение')
        self.result_table.column("param", anchor="w", width=200)
        self.result_table.column("value", anchor="center", width=200)
        self.result_table.grid(
            row=0,
            column=2,
            rowspan=20,
            padx=10,
            pady=5,
            sticky='nsew'
        )

        # Настройка весов строк в основном фрейме
        self.calc_frame.grid_rowconfigure(0, weight=1)

    def create_materials_tab(self):
        """Создает вкладку с таблицей материалов и фильтрами."""
        columns = (
            "index",
            "product_code",
            "product_name_ru",
            "volume_m3",
            "construction_name",
            "material_type_name",
            "size_length_mm",
            "size_width_mm",
            "thickness_mm"
        )
        container = ttk.Frame(self.materials_frame)
        container.pack(fill='both', expand=True, padx=10, pady=10)

        self.sort_descending = {col: False for col in columns}

        self.materials_tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings"
        )

        self.materials_tree.heading('index', text='№', anchor='center')
        self.materials_tree.heading(
            'product_code',
            text='Код продукта',
            command=lambda: self.sort_tree('product_code', False)
        )
        self.materials_tree.heading(
            "product_name_ru",
            text="Название (RU)",
            command=lambda: self.sort_tree("product_name_ru", False)
        )
        self.materials_tree.heading(
            "volume_m3",
            text="Объем, м³",
            command=lambda: self.sort_tree("volume_m3", True)
        )
        self.materials_tree.heading(
            "construction_name",
            text="Для конструкций",
            command=lambda: self.sort_tree("construction_name", False)
        )
        self.materials_tree.heading(
            "material_type_name",
            text="Тип материала",
            command=lambda: self.sort_tree(
                "material_type_name", False)  # Fixed typo here
        )
        self.materials_tree.heading(
            "size_length_mm",
            text="Длина (мм)",
            command=lambda: self.sort_tree("size_length_mm", True)
        )
        self.materials_tree.heading(
            "size_width_mm",
            text="Ширина (мм)",
            command=lambda: self.sort_tree("size_width_mm", True)
        )
        self.materials_tree.heading(
            "thickness_mm",
            text="Толщина (мм)",
            command=lambda: self.sort_tree("thickness_mm", True)
        )
        self.materials_tree.column('index', width=40, anchor='center')
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

        y_scrollbar = ttk.Scrollbar(
            container,
            orient='vertical',
            command=self.materials_tree.yview
        )
        self.materials_tree.configure(yscrollcommand=y_scrollbar.set)

        self.materials_tree.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.load_materials_data(self.materials_data)

        self.sprt_descending = {}

    def load_materials_data(self, data):
        """Загружает и отображает список материалов в таблице."""
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)
        for idx, item in enumerate(data, start=1):
            self.materials_tree.insert(
                "",
                "end",
                values=(
                    idx,
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

    def sort_tree(self, column, is_numeric):
        """Сортирует таблицу материалов по выбранному столбцу."""
        descending = self.sprt_descending.get(column, False)
        data = self.materials_data.copy()

        def sort_key(item):
            value = item[column]
            if is_numeric:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return float('-inf') if descending else float('inf')
            return str(value).lower()

        data.sort(key=sort_key, reverse=descending)
        self.load_materials_data(data)
        self.sprt_descending[column] = not descending

    def calculate(self):
        """Выполняет расчет теплоизоляции на основе введенных данных."""
        try:
            # Получаем выбранные материалы
            inner_material = self.material_cb.get()
            outer_material = self.material_cb_outer.get() if hasattr(self, 'material_cb_outer') else None

            if not inner_material:
                logger.warning("Не выбран материал для расчета")
                messagebox.showerror("Ошибка", "Выберите материал внутреннего слоя")
                return

            # Проверяем поля ввода
            values = {}
            for key, entry in self.entries.items():
                value = entry.get().strip()
                if not value:
                    logger.warning(f"Пустое поле ввода: {key}")
                    messagebox.showerror("Ошибка", f"Заполните поле '{key}'")
                    return
                values[key] = value

            # Валидация входных данных
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

            # Создаем калькулятор с правильными параметрами
            self.calc = InsulationCalculator(
                inner_material_ru_name=inner_material,
                outer_material_ru_name=outer_material if outer_material else None,
                area_m2=area,
                building_height_m=height,
                count_corner=corners,
                perimeter_m=perimeter,
            )

            self.result = self.calc.summary()
            logger.info(
                f"Выполнен расчет: внутренний материал={inner_material}, "
                f"внешний материал={outer_material}, результат={self.result}"
            )

            self.display_result(self.result)

        except ValueError as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            logger.error(f"Ошибка при расчете: {str(e)}", exc_info=True)
            messagebox.showerror("Ошибка расчета", f"Произошла ошибка: {str(e)}")

        except ValidationError as e:
            logger.warning(f"Ошибка валидации: {e}")
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            logger.error(f"Ошибка при расчёте: {e}", exc_info=True)
            messagebox.showerror("Ошибка", str(e))

    def clear_fields(self):
        """Очищает все поля ввода и таблицу с результатами."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.result_table.delete(*self.result_table.get_children())

    def display_result(self, result_dict):
        """Отображает результаты расчета в текстовом поле."""
        for item in self.result_table.get_children():
            self.result_table.delete(item)

        for key, val in result_dict.items():
            self.result_table.insert('', 'end', values=(key, val))

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
