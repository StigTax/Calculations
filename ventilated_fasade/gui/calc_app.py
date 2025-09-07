# from reports.report_generator import ReportGenerator
from logic.validators import InputValidator, ValidationError
from data.materials import GetInsulationMaterials
from data.people import get_session, get_engineer, upsert_engineer, list_managers, add_manager, upsert_address
from data.sync import sync_db_with_fixture
from logic.calculator import InsulationCalculator
from data.services_calc import create_calc, create_revision
from data.models_calc import Calculation
from config import DB_URL
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
        logger.info('Запуск приложения InsulationCalculatorApp')

        try:
            materials = GetInsulationMaterials()
            self.materials_list = materials.get_all_ru_names()
            self.materials_data = materials.get_all_materials()
            logger.debug(f'Загружены материалы: {self.materials_list}')
        except Exception as e:
            logger.error(f'Не удалось загрузить материалы: {e}', exc_info=True)
            messagebox.showerror(
                'Ошибка', f'Не удалось загрузить материалы: {e}')
            self.materials_list = []
            self.materials_data = []

        self.result = {}
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.calc_frame = ttk.Frame(self.notebook)
        self.materials_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.calc_frame, text='Калькулятор')
        self.notebook.add(self.materials_frame, text='Материалы')

        self.create_calc_tab()

        self.create_menu()

        self.material_columns = (
            'index',
            'product_name_ru',
            'volume_m3',
            'construction_name',
            'material_type_type',
            'size_length_mm',
            'size_width_mm',
            'thickness_mm'
        )

    def _gather_input_payload(self) -> dict:
        return {
            "system_type": self.system_type.get(),
            "area_m2": self.entries["area_m2"].get().strip(),
            "building_height_m": self.entries["building_height_m"].get().strip(),
            "count_corner": self.entries["count_corner"].get().strip(),
            "perimeter_m": self.entries["perimeter_m"].get().strip(),
            "inner_material": self.material_cb_inner.get().strip(),
            "outer_material": self.material_cb_outer.get().strip() if self.system_type.get()=="double" else self.material_cb_inner.get().strip(),
            "manager": self.manager_cb.get().strip() if hasattr(self, "manager_cb") else "",
            "address": {
                "line1": self.addr_line1.get().strip(), "city": self.addr_city.get().strip(),
                "region": self.addr_region.get().strip(), "postal_code": self.addr_postal.get().strip(),
                "note": self.addr_note.get().strip(),
            }
        }

    def create_calc_tab(self):
        """Создает вкладку с интерфейсом калькулятора."""
        # Основной фрейм разделен на 2 колонки: левая (элементы управления) и правая (таблица)
        for c in (0, 1):
            self.calc_frame.grid_columnconfigure(c, weight=(1 if c == 0 else 2))
        for r in (0, 1, 2):
            self.calc_frame.grid_rowconfigure(r, weight=(1 if r == 1 else 0))

        # ---------- ЛЕВАЯ СТОРОНА (ввод) ----------
        # 1) Верх: тип системы + выбор материалов
        left_top = ttk.LabelFrame(self.calc_frame, text="Параметры системы")
        left_top.grid(row=0, column=0, sticky="nsew", padx=10, pady=(8, 4))

        # 2) Середина: менеджер + адрес + габариты
        left_mid = ttk.LabelFrame(self.calc_frame, text="Объект")
        left_mid.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        left_mid.grid_columnconfigure(0, weight=1)
        left_mid.grid_columnconfigure(1, weight=1)

        # 3) Низ: кнопки
        left_bottom = ttk.Frame(self.calc_frame)
        left_bottom.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 8))

        # ---------- ПРАВАЯ СТОРОНА (вывод) ----------
        # A) Верх: таблица «Объект»
        right_top = ttk.LabelFrame(self.calc_frame, text="Информация об объекте")
        right_top.grid(row=0, column=1, sticky="nsew", padx=(4, 10), pady=(8, 4))

        # B) Середина: таблица «Результаты»
        right_mid = ttk.LabelFrame(self.calc_frame, text="Результаты расчёта")
        right_mid.grid(row=1, column=1, sticky="nsew", padx=(4, 10), pady=4)
        right_mid.grid_columnconfigure(0, weight=1)
        right_mid.grid_rowconfigure(0, weight=1)

        # C) Низ: резерв (пока пустой)
        right_bottom = ttk.LabelFrame(self.calc_frame, text="Резерв")
        right_bottom.grid(row=2, column=1, sticky="nsew", padx=(4, 10), pady=(4, 8))

        # ====== Содержание ЛЕВО — верх: тип системы + материалы ======
        self.system_type = tk.StringVar(value="mono")
        system_frame = ttk.Frame(left_top)
        system_frame.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Radiobutton(system_frame, text="Моносистема (один слой)",
                        variable=self.system_type, value="mono",
                        command=self.toggle_material_fields).pack(side="left", padx=6)
        ttk.Radiobutton(system_frame, text="Двухслойная система",
                        variable=self.system_type, value="double",
                        command=self.toggle_material_fields).pack(side="left", padx=6)

        # Материалы
        mat_frame = ttk.Frame(left_top)
        mat_frame.pack(fill="x", padx=8, pady=(4, 8))
        self.material_label_inner = ttk.Label(mat_frame, text="Выберите материал для внутреннего слоя:")
        self.material_label_inner.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.material_cb_inner = ttk.Combobox(mat_frame, values=self.materials_list, state="readonly")
        self.material_cb_inner.grid(row=1, column=0, columnspan=2, sticky="ew")
        if self.materials_list:
            self.material_cb_inner.set(self.materials_list[0])

        ttk.Label(mat_frame, text="Выберите материал для внешнего слоя:").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.material_cb_outer = ttk.Combobox(mat_frame, values=self.materials_list, state="readonly")
        self.material_cb_outer.grid(row=3, column=0, columnspan=2, sticky="ew")
        if self.materials_list:
            self.material_cb_outer.set(self.materials_list[0])

        mat_frame.grid_columnconfigure(0, weight=1)
        mat_frame.grid_columnconfigure(1, weight=1)

        # ====== Содержание ЛЕВО — середина: менеджер + адрес + габариты ======
        # Менеджер
        ttk.Label(left_mid, text="Менеджер:").grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")
        self.manager_cb = ttk.Combobox(left_mid, values=[], state="readonly", width=28)
        self.manager_cb.grid(row=0, column=1, padx=8, pady=(8, 4), sticky="ew")
        ttk.Button(left_mid, text="Добавить менеджера", command=self.open_add_manager)\
            .grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        self.reload_managers()

        # Адрес
        row0 = 2
        ttk.Label(left_mid, text="Адрес (улица, дом):").grid(row=row0, column=0, padx=8, pady=(4, 2), sticky="w")
        self.addr_line1 = ttk.Entry(left_mid); self.addr_line1.grid(row=row0, column=1, padx=8, pady=(4, 2), sticky="ew")
        ttk.Label(left_mid, text="Город:").grid(row=row0+1, column=0, padx=8, pady=2, sticky="w")
        self.addr_city = ttk.Entry(left_mid); self.addr_city.grid(row=row0+1, column=1, padx=8, pady=2, sticky="ew")
        ttk.Label(left_mid, text="Регион:").grid(row=row0+2, column=0, padx=8, pady=2, sticky="w")
        self.addr_region = ttk.Entry(left_mid); self.addr_region.grid(row=row0+2, column=1, padx=8, pady=2, sticky="ew")
        ttk.Label(left_mid, text="Индекс:").grid(row=row0+3, column=0, padx=8, pady=2, sticky="w")
        self.addr_postal = ttk.Entry(left_mid); self.addr_postal.grid(row=row0+3, column=1, padx=8, pady=2, sticky="ew")
        ttk.Label(left_mid, text="Примечание:").grid(row=row0+4, column=0, padx=8, pady=2, sticky="w")
        self.addr_note = ttk.Entry(left_mid); self.addr_note.grid(row=row0+4, column=1, padx=8, pady=2, sticky="ew")

        # Габариты
        fields = [
            ("Площадь, м²", "area_m2"),
            ("Высота здания, м", "building_height_m"),
            ("Количество углов", "count_corner"),
            ("Периметр, м", "perimeter_m"),
        ]
        self.entries = {}
        base = row0 + 5
        for i, (label_text, key) in enumerate(fields):
            ttk.Label(left_mid, text=label_text).grid(row=base+i, column=0, padx=8, pady=2, sticky="w")
            e = ttk.Entry(left_mid); e.grid(row=base+i, column=1, padx=8, pady=2, sticky="ew")
            self.entries[key] = e

        # ====== Содержание ЛЕВО — низ: кнопки ======
        btns = ttk.Frame(left_bottom)
        btns.pack(fill="x", padx=8, pady=8)
        tk.Button(btns, text="Рассчитать", command=self.calculate).pack(side="left", padx=(0, 6))
        tk.Button(btns, text="Очистить", command=self.clear_fields,
                bg="red", fg="white", activebackground="#a80000", activeforeground="white").pack(side="left")

        # ====== ПРАВО — верх: таблица «Объект» ======
        self.object_columns = ("address", "area", "height", "corners", "perimeter")
        self.object_table = ttk.Treeview(right_top, columns=self.object_columns, show="headings", height=1)
        obj_headers = {
            "address": "Адрес объекта",
            "area": "Площадь, м²",
            "height": "Высота, м",
            "corners": "Углы, шт",
            "perimeter": "Периметр, м",
        }
        obj_widths = [280, 110, 110, 100, 120]
        for c, w in zip(self.object_columns, obj_widths):
            self.object_table.heading(c, text=obj_headers[c])
            self.object_table.column(c, width=w, anchor=("w" if c == "address" else "e"), stretch=(c == "address"))
        self.object_table.pack(fill="x", padx=8, pady=8)

        # ====== ПРАВО — середина: таблица «Результаты» ======
        self.result_columns = ("layer", "system", "material", "sheets", "volume", "fasteners", "flen")
        self.result_table = ttk.Treeview(right_mid, columns=self.result_columns, show="headings", height=16)
        headers = {
            "layer": "Слой",
            "system": "Тип системы",
            "material": "Материал",
            "sheets": "Кол-во листов",
            "volume": "Объём, м³",
            "fasteners": "Крепёж, шт",
            "flen": "Длина, мм",
        }
        widths  = [ 90, 120, 260, 120, 110, 110, 100 ]
        anchors = [ "w","center","w","e","e","e","e" ]
        for col, w, a in zip(self.result_columns, widths, anchors):
            self.result_table.heading(col, text=headers[col])
            self.result_table.column(col, width=w, anchor=a, stretch=(col == "material"))

        vsb = ttk.Scrollbar(right_mid, orient="vertical", command=self.result_table.yview)
        self.result_table.configure(yscrollcommand=vsb.set)
        self.result_table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        vsb.grid(row=0, column=1, sticky="ns", pady=8)

        # ====== Инициал: скрыть внешний слой для моносистемы ======
        self.toggle_material_fields()
    def toggle_material_fields(self):
        """
        Переключает видимость полей для внешнего слоя
        в зависимости от выбранного типа системы.
        """
        if self.system_type.get() == 'mono':
            # Для моносистемы скрываем внешний слой
            self.material_cb_outer.grid_remove()
            # Переименовываем label для внутреннего слоя
            self.material_label_inner.config(text='Выберите материал:')
        else:
            # Для двухслойной системы показываем оба слоя
            self.material_cb_outer.grid()
            # Возвращаем стандартное название label
            self.material_label_inner.config(
                text='Выберите материал для внутреннего слоя:')

    def calculate(self):
        """Выполняет расчет теплоизоляции на основе введенных данных."""
        try:
            raw_data = {key: entry.get().strip()
                        for key, entry in self.entries.items()}
            validator = InputValidator()
            validated_data = validator.validate_inputs(raw_data)

            inner_material = (self.material_cb_inner.get() or '').strip()
            outer_material = (
                self.material_cb_outer.get() or ''
            ).strip() if self.system_type.get() == 'double' else inner_material

            # Проверки по выбору материалов
            if not inner_material:
                messagebox.showerror('Ошибка', 'Выберите утеплитель.')
                return
            if self.system_type.get() == 'double' and not outer_material:
                messagebox.showerror('Ошибка', 'Выберите внешний утеплитель.')
                return

            # Получаем словарь с данными по материалам
            material_dict = {m['product_name_ru']
                : m for m in self.materials_data}
            if outer_material and outer_material not in material_dict:
                messagebox.showerror(
                    'Ошибка', f'Материал "{outer_material}" не найден в базе.')
                return
            if self.system_type.get(
            ) == 'double' and inner_material not in material_dict:
                messagebox.showerror(
                    'Ошибка', f'Материал "{inner_material}" не найден в базе.')
                return

            calc = InsulationCalculator(
                outer_material_ru_name=outer_material,
                inner_material_ru_name=inner_material if self.system_type.get(
                ) == 'double' else None,
                **validated_data
            )

            self.calc = calc
            result = calc.summary()
            self.result = result
            self.display_result(result)

        except ValidationError as ve:
            messagebox.showerror('Ошибка ввода', str(ve))
        except Exception as e:
            logger.exception('Ошибка при расчете')
            messagebox.showerror(
                'Ошибка', f'Произошла ошибка при расчете:\n{e}')

    def display_result(self, result):
        """Отображает результаты расчета в таблице."""
        self.object_table.delete(*self.object_table.get_children())
        addr = ", ".join([x for x in [
            self.addr_line1.get().strip(),
            self.addr_city.get().strip(),
            self.addr_region.get().strip(),
            self.addr_postal.get().strip()
        ] if x])
        # габариты из валидированных данных — они уже ушли в расчет
        area = self.entries["area_m2"].get().strip()
        height = self.entries["building_height_m"].get().strip()
        corners = self.entries["count_corner"].get().strip()
        perim = self.entries["perimeter_m"].get().strip()
        self.object_table.insert("", "end", values=(addr, area, height, corners, perim))

        self.result_table.delete(*self.result_table.get_children())

        outer = result.get('outer_layer') or {}
        inner = result.get('inner_layer') or {}
        system_type = result.get('system_type', 'mono')

        def g(layer, path, default=""):
            cur = layer or {}
            for p in (path if isinstance(path, (list, tuple)) else [path]):
                cur = (cur or {}).get(p, None)
            return default if cur is None else cur

        def fmt_num(v, nd=2):
            if v in ("", None):
                return ""
            try:
                return f"{float(v):.{nd}f}"
            except (TypeError, ValueError):
                return v

        # Наружный слой
        self.result_table.insert("", "end", values=(
            "Наружный",
            "Двухслойная" if system_type else "Однослойная",
            outer.get("material", ""),
            fmt_num(outer.get("sheets"), 0),
            fmt_num(outer.get("volume"), 3),
            fmt_num(g(outer, ("fasteners", "count")), 0),
            fmt_num(g(outer, ("fasteners", "length")), 0),
        ))

        # Внутренний слой (если есть)
        if system_type and inner:
            self.result_table.insert("", "end", values=(
                "Внутренний",
                "Двухслойная",
                inner.get("material", ""),
                fmt_num(inner.get("sheets"), 0),
                fmt_num(inner.get("volume"), 3),
                fmt_num(g(inner, ("fasteners", "count")), 0),
                fmt_num(g(inner, ("fasteners", "length")), 0),
            ))

        # Итого (по числовым)
        total_sheets = (
            outer.get("sheets") or 0) + (inner.get("sheets") or 0
                                         )
        total_volume = (
            outer.get("volume") or 0.0) + (inner.get("volume") or 0.0
                                           )
        total_fast = (g(outer, ("fasteners", "count"), 0) or 0) + \
            (g(inner, ("fasteners", "count"), 0) or 0)
        max_len = ' '

        self.result_table.insert("", "end", values=(
            "ИТОГО", "", "",
            fmt_num(total_sheets, 0),
            fmt_num(total_volume, 3),
            fmt_num(total_fast, 0),
            fmt_num(max_len, 0),
        ))

    def create_menu(self):
        '''Creates the main menu for the application.'''
        menubar = Menu(self)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить расчёт…", command=self.save_calculation)
        file_menu.add_command(label="Сохранить как версию…", command=self.save_calculation_revision)
        file_menu.add_separator()
        file_menu.add_command(
            label='Загрузить фикстуру в БД', command=self.load_fixture)
        file_menu.add_separator()
        file_menu.add_command(label='Сохранить Excel', command=self.save_excel)
        file_menu.add_command(label='Сохранить PDF', command=self.save_pdf)
        file_menu.add_separator()
        file_menu.add_command(label='Выход', command=self.quit)
        menubar.add_cascade(label='Файл', menu=file_menu)

        db_menu = Menu(menubar, tearoff=0)
        db_menu.add_command(
            label="Инженер…", command=self.open_engineer_dialog)
        menubar.add_cascade(label="База данных", menu=db_menu)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label='О программе', command=self.show_about)
        menubar.add_cascade(label='Справка', menu=help_menu)

        self.config(menu=menubar)

    def load_fixture(self):
        """Загрузка фикстур руками."""
        path = filedialog.askopenfilename(
            title='Выберите JSON-файл фикстуры',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
        )
        if not path:
            return
        try:
            sync_db_with_fixture(path, DB_URL)
            messagebox.showinfo('Успех', f'Фикстура успешо загружена: {path}')
            self.reload_materials()
        except Exception as e:
            logger.exception('Ошибка загрузки фикстуры')
            messagebox.showerror(
                'Ошибка', f'Не удалось загрузить фикстуру: {e}'
            )

    def reload_materials(self):
        try:
            repo = GetInsulationMaterials()
            self.materials_list = repo.get_all_ru_names()

            self.material_cb_inner.configure(values=self.materials_list)
            if self.materials_list:
                self.material_cb_inner.set(self.materials_list[0])
        except Exception as e:
            logger.exception('Ошибка обновления материалов')
            messagebox.showerror(
                'Ошибка', f'Не удалось обновить материалы:\n{e}'
            )

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
            logger.warning('Попытка сохранения отчета без данных')
            messagebox.showerror(
                'Ошибка', 'Нет данных для сохранения. '
                'Сначала выполните расчет.'
            )
            return
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')]
            )
            if filename:
                rg = ReportGenerator(self.calc)
                rg.generate_excel_report(filename)
                logger.info(f'Отчет успешно сохранен в Excel: {filename}')
                messagebox.showinfo(
                    'Успех', f'Отчет успешно сохранен: {filename}'
                )
        except Exception as e:
            logger.error(
                f'Ошибка при сохранении Excel отчета: {e}', exc_info=True
            )
            messagebox.showerror('Ошибка', f'Не удалось сохранить отчет: {e}')

    def save_pdf(self):
        """Сохраняет отчет в формате PDF."""
        if not hasattr(self, 'result') or not self.result:
            logger.warning('Попытка сохранения PDF отчета без данных')
            messagebox.showerror(
                'Ошибка', 'Нет данных для сохранения. '
                'Сначала выполните расчет.'
            )
            return
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension='.pdf',
                filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')]
            )
            if filename:
                rg = ReportGenerator(self.calc)
                rg.generate_pdf_report(filename)
                logger.info(f'Отчет успешно сохранен в PDF: {filename}')
                messagebox.showinfo(
                    'Успех', f'Отчет успешно сохранен: {filename}'
                )
        except Exception as e:
            logger.error(
                f'Ошибка при сохранении PDF отчета: {e}', exc_info=True
            )
            messagebox.showerror(
                'Ошибка', f'Не удалось сохранить отчет: {e}'
            )

    def open_engineer_dialog(self):
        win = tk.Toplevel(self)
        win.title("Инженер")
        win.grab_set()
        # поля
        tk.Label(win, text="Имя").grid(
            row=0, column=0, sticky="e", padx=6, pady=4)
        tk.Label(win, text="Фамилия").grid(
            row=1, column=0, sticky="e", padx=6, pady=4)
        tk.Label(win, text="Email").grid(
            row=2, column=0, sticky="e", padx=6, pady=4)
        tk.Label(win, text="Телефон").grid(
            row=3, column=0, sticky="e", padx=6, pady=4)
        e1 = ttk.Entry(win)
        e2 = ttk.Entry(win)
        e3 = ttk.Entry(win)
        e4 = ttk.Entry(win)
        e1.grid(row=0, column=1, padx=6, pady=4)
        e2.grid(row=1, column=1, padx=6, pady=4)
        e3.grid(row=2, column=1, padx=6, pady=4)
        e4.grid(row=3, column=1, padx=6, pady=4)

        # префилл
        with get_session() as s:
            eng = get_engineer(s)
            if eng:
                e1.insert(0, eng.first_name)
                e2.insert(0, eng.last_name)
                if eng.email:
                    e3.insert(0, eng.email)
                if eng.phone:
                    e4.insert(0, eng.phone)

        def save():
            fn, ln = e1.get().strip(), e2.get().strip()
            if not fn or not ln:
                messagebox.showerror("Ошибка", "Имя и Фамилия обязательны.")
                return
            with get_session() as s:
                upsert_engineer(s, fn, ln, e3.get().strip()
                                or None, e4.get().strip() or None)
                s.commit()
            messagebox.showinfo("OK", "Инженер сохранён.")
            win.destroy()

        ttk.Button(win, text="Сохранить", command=save).grid(
            row=4, column=0, columnspan=2, pady=8)

    def reload_managers(self):
        try:
            with get_session() as s:
                items = list_managers(s)
                self._managers = items
                values = [f"{m.first_name} {m.last_name}" for m in items]
                self.manager_cb.configure(values=values, state=(
                    "readonly" if values else "disabled"))
                if values:
                    self.manager_cb.set(values[0])
        except Exception as e:
            logger.exception("Ошибка загрузки менеджеров")
            messagebox.showerror(
                "Ошибка", f"Не удалось загрузить менеджеров:\n{e}")

    def open_add_manager(self):
        win = tk.Toplevel(self)
        win.title("Добавить менеджера")
        win.grab_set()
        labels = ["Имя", "Фамилия", "Email", "Телефон"]
        entries = []
        for i, lab in enumerate(labels):
            ttk.Label(win, text=lab).grid(
                row=i, column=0, sticky="e", padx=6, pady=4)
            en = ttk.Entry(win, width=30)
            en.grid(row=i, column=1, padx=6, pady=4)
            entries.append(en)

        def save():
            fn, ln, em, ph = [e.get().strip() or None for e in entries]
            if not fn or not ln:
                messagebox.showerror("Ошибка", "Имя и Фамилия обязательны.")
                return
            with get_session() as s:
                # если дубль — вернёт существующего
                m = add_manager(s, fn, ln, em, ph)
                s.commit()
            messagebox.showinfo(
                "OK", f"Менеджер «{m.first_name} {m.last_name}» сохранён.")
            win.destroy()
            self.reload_managers()
            # выделим в комбобоксе только что добавленного
            full = f"{m.first_name} {m.last_name}"
            self.manager_cb.set(full)

        ttk.Button(win, text="Сохранить", command=save).grid(
            row=4, column=0, columnspan=2, pady=8)

    def save_calculation(self):
        if not getattr(self, "result", None):
            messagebox.showerror("Ошибка", "Сначала выполните расчёт.")
            return
        with get_session() as s:
            eng = get_engineer(s)
            if not eng:
                messagebox.showerror("Ошибка", "Сначала укажите инженера (База данных → Инженер).")
                return
            a = self._gather_input_payload()["address"]
            adr = upsert_address(s, a["line1"], a["city"] or None, a["region"] or None, a["postal_code"] or None, a["note"] or None)
            payload_in = self._gather_input_payload()
            payload_out = self.result
            calc = create_calc(s, eng, adr.id, payload_in, payload_out)
            # привяжем менеджера, если выбран
            if self.manager_cb.get():
                full = self.manager_cb.get()
                m = next((x for x in list_managers(s) if f"{x.first_name} {x.last_name}"==full), None)
                if m:
                    calc.managers.append(m)
            s.commit()
            messagebox.showinfo("Сохранено", f"Расчёт сохранён с номером:\n{calc.number}")
            self.current_calc_base = calc.base_number  # запомним для ревизий

    def save_calculation_revision(self):
        if not getattr(self, "result", None) or not getattr(self, "current_calc_base", None):
            messagebox.showerror("Ошибка", "Нет базового расчёта. Сначала сохраните первичную версию.")
            return
        with get_session() as s:
            payload_in = self._gather_input_payload()
            payload_out = self.result
            rev = create_revision(s, self.current_calc_base, payload_in, payload_out)
            s.commit()
            messagebox.showinfo("Сохранено", f"Создана версия:\n{rev.number}")
            
    def show_about(self):
        """Показывает информацию об авторе."""
        messagebox.showinfo(
            'О программе',
            'Программа расчета теплоизоляции фасадов НФС\n'
            'Версия: 0.1.0 (Альфа-версия)\n'
            'Разработчик: Ефремчев Никита\n'
            'GitHub: https://github.com/StigTax\n'
            'Дата: 2025'
        )


if __name__ == '__main__':
    app = InsulationCalculatorApp()
    app.mainloop()
