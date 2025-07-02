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
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        # Create frames for tabs
        self.calc_frame = ttk.Frame(self.notebook)
        self.materials_frame = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.calc_frame, text='Калькулятор')
        self.notebook.add(self.materials_frame, text='Материалы')

        # Create widgets for each tab
        self.create_calc_tab()
        self.create_materials_tab()

        # Create menu
        self.create_menu()

        self.material_columns = (
            "index",
            "product_code",
            "product_name_ru",
            "volume_m3",
            "construction_name",
            "material_type_type",
            "size_length_mm",
            "size_width_mm",
            "thickness_mm"
        )

    def create_calc_tab(self):
        """Создает вкладку с интерфейсом калькулятора."""
        # Основной фрейм разделен на 2 колонки: левая (элементы управления) и правая (таблица)
        self.calc_frame.grid_columnconfigure(
            0, weight=1)  # Левая колонка (элементы)
        self.calc_frame.grid_columnconfigure(
            2, weight=3)  # Правая колонка (таблица)

        # Создаем отдельный фрейм для левой части (элементов управления)
        left_frame = ttk.Frame(self.calc_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # Настройка колонок в левом фрейме
        left_frame.grid_columnconfigure(0, weight=1)  # Колонка для labels
        left_frame.grid_columnconfigure(1, weight=1)  # Колонка для полей ввода

        # Переменная для хранения выбранного типа системы
        self.system_type = tk.StringVar(
            value="mono")  # По умолчанию моносистема

        # Фрейм для радиокнопок
        system_frame = ttk.LabelFrame(left_frame, text="Тип системы")
        system_frame.grid(row=0, column=0, columnspan=2,
                          padx=10, pady=5, sticky="ew")

        mono_radio = ttk.Radiobutton(
            system_frame,
            text="Моносистема (один слой)",
            variable=self.system_type,
            value="mono",
            command=self.toggle_material_fields
        )
        mono_radio.pack(side="left", padx=5, pady=2)

        double_radio = ttk.Radiobutton(
            system_frame,
            text="Двухслойная система",
            variable=self.system_type,
            value="double",
            command=self.toggle_material_fields
        )
        double_radio.pack(side="left", padx=5, pady=2)

        # Внутренний слой
        self.material_label_inner = ttk.Label(
            left_frame,
            text="Выберите материал для внутреннего слоя:"
        )
        self.material_label_inner.grid(
            row=1,
            column=0,
            padx=10,
            pady=5,
            sticky="w"
        )

        self.material_cb_inner = ttk.Combobox(
            left_frame, values=self.materials_list, state="readonly")
        self.material_cb_inner.grid(
            row=2, column=0, columnspan=2,
            padx=10, pady=5, sticky='ew'
        )
        if self.materials_list:
            self.material_cb_inner.set(self.materials_list[0])

        # Внешний слой
        self.material_label_outer = ttk.Label(
            left_frame, text="Выберите материал для внешнего слоя:"
        )
        self.material_label_outer.grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )

        self.material_cb_outer = ttk.Combobox(
            left_frame, values=self.materials_list, state="readonly"
        )
        self.material_cb_outer.grid(
            row=4, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
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

        for row, (label_text, attr_name) in enumerate(fields, start=5):
            label = ttk.Label(left_frame, text=label_text)
            label.grid(row=row, column=0, padx=10, pady=5, sticky='w')

            entry = ttk.Entry(left_frame)
            entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
            self.entries[attr_name] = entry

        # Кнопки
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(
            row=len(fields)+6,
            column=0, columnspan=2,
            pady=10
        )

        calc_btn = tk.Button(
            buttons_frame, text='Рассчитать', command=self.calculate)
        calc_btn.pack(side='left', padx=5)

        clear_btn = tk.Button(
            buttons_frame, text='Очистить', command=self.clear_fields,
            bg='red', fg='white',
            activebackground="#a80000", activeforeground='white'
        )
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

        # Изначально скрываем поля для внешнего слоя
        self.toggle_material_fields()

    def toggle_material_fields(self):
        """Переключает видимость полей для внешнего слоя в зависимости от выбранного типа системы."""
        if self.system_type.get() == "mono":
            # Для моносистемы скрываем внешний слой
            self.material_cb_outer.grid_remove()
            # Переименовываем label для внутреннего слоя
            self.material_label_inner.config(text="Выберите материал:")
        else:
            # Для двухслойной системы показываем оба слоя
            self.material_cb_outer.grid()
            # Возвращаем стандартное название label
            self.material_label_inner.config(
                text="Выберите материал для внутреннего слоя:")

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
        descending = self.sort_descending.get(column, False)
        data = self.materials_data.copy()

        def sort_key(item):
            value = item.get(column)
            if is_numeric:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return float('-inf') if descending else float('inf')
            return str(value).lower() if value else ""

        data.sort(key=sort_key, reverse=descending)

        # После сортировки обновляем таблицу
        self.materials_data = data
        # Здесь заменяем refresh_table на load_materials_data
        self.load_materials_data(data)

        # Переключаем направление сортировки
        self.sort_descending[column] = not descending

    def calculate(self):
        """Выполняет расчет теплоизоляции на основе введенных данных."""
        try:
            # Считываем и валидируем значения из полей
            raw_data = {key: entry.get().strip()
                        for key, entry in self.entries.items()}
            validator = InputValidator()
            validated_data = validator.validate_inputs(raw_data)

            # Получаем выбранные материалы
            inner_material = self.material_cb_inner.get()
            outer_material = self.material_cb_outer.get(
            ) if self.system_type.get() == "double" else None

            # Проверки по выбору материалов
            if self.system_type.get() == "double":
                if not outer_material:
                    messagebox.showerror(
                        "Ошибка", "Выберите внешний утеплитель.")
                    return
                if not inner_material:
                    messagebox.showerror(
                        "Ошибка", "Выберите внутренний утеплитель.")
                    return
            else:
                if not inner_material:
                    messagebox.showerror("Ошибка", "Выберите утеплитель.")
                    return

            # Получаем словарь с данными по материалам
            material_dict = {m["product_name_ru"]                             : m for m in self.materials_data}
            inner_data = material_dict.get(inner_material)
            outer_data = material_dict.get(
                outer_material) if outer_material else None

            if self.system_type.get() == "double":
                if not inner_data or not outer_data:
                    raise ValueError("Выбранные материалы не найдены в базе")
                calc = InsulationCalculator(
                    outer_material_ru_name=outer_material,
                    inner_material_ru_name=inner_material,
                    **validated_data
                )
            else:
                if not inner_data:
                    raise ValueError("Выбранный материал не найден в базе")
                calc = InsulationCalculator(
                    inner_material_ru_name=inner_material,
                    **validated_data
                )

            result = calc.summary()

            self.result = result
            self.display_result(result)

        except ValidationError as ve:
            messagebox.showerror("Ошибка ввода", str(ve))
        except Exception as e:
            logger.exception("Ошибка при расчете")
            messagebox.showerror(
                "Ошибка", f"Произошла ошибка при расчете:\n{e}")

    def display_result(self, result):
        """Отображает результаты расчета в таблице."""
        self.result_table.delete(*self.result_table.get_children())

        self.result_table.insert(
            "", "end",
            values=(
                "Тип системы",
                "Двухслойная" if result.get(
                    "system_type") == "double" else "Однослойная"
            )
        )

        if "outer_layer" in result and result["outer_layer"]:
            outer = result["outer_layer"]
            self.result_table.insert(
                "", "end", values=("", "--- Наружный слой ---"))
            self.result_table.insert("", "end", values=(
                "Материал", outer.get("material", "")))
            self.result_table.insert("", "end", values=(
                "Кол-во листов", outer.get("sheets_count", "")))
            self.result_table.insert("", "end", values=(
                "Объем, м³", outer.get("volume_m3", "")))

        if "inner_layer" in result and result["inner_layer"]:
            inner = result["inner_layer"]
            self.result_table.insert(
                "", "end", values=("", "--- Внутренний слой ---"))
            self.result_table.insert("", "end", values=(
                "Материал", inner.get("material", "")))
            self.result_table.insert("", "end", values=(
                "Кол-во листов", inner.get("sheets_count", "")))
            self.result_table.insert("", "end", values=(
                "Объем, м³", inner.get("volume_m3", "")))

    def create_menu(self):
        """Creates the main menu for the application."""
        menubar = Menu(self)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить Excel", command=self.save_excel)
        file_menu.add_command(label="Сохранить PDF", command=self.save_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def clear_fields(self):
        """Очищает все поля ввода и таблицу результатов."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        for item in self.result_table.get_children():
            self.result_table.delete(item)
        self.result = {}

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
