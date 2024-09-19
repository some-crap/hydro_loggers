import os
import pandas as pd
import tkinter as tk
import csv
from tkinter import filedialog, messagebox
import webbrowser

sensor_type_for_saving = 0


class SensorDataProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка файлов для датчиков")

        self.folder_path = None
        self.files_list = []
        self.dev_eui = None

        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        # Выбор типа датчика
        self.sensor_var = tk.StringVar(value="GORIZONT")

        label = tk.Label(frame, text="1. Выберите тип датчика:")
        label.pack(anchor='w')

        gorizont_rb = tk.Radiobutton(frame, text="GORIZONT", variable=self.sensor_var, value="GORIZONT", command=self.on_sensor_change)
        gorizont_rb.pack(anchor='w')

        promodem_rb = tk.Radiobutton(frame, text="PROMODEM", variable=self.sensor_var, value="PROMODEM", command=self.on_sensor_change)
        promodem_rb.pack(anchor='w')

        geokon_rb = tk.Radiobutton(frame, text="GEOKON", variable=self.sensor_var, value="GEOKON", command=self.on_sensor_change)
        geokon_rb.pack(anchor='w')

        # Поле для ввода ID датчика
        self.label_dev_eui = tk.Label(frame, text="2. Введите ID датчика (если не будет найден автоматически):")
        self.entry_dev_eui = tk.Entry(frame, width=30)

        # Кнопка для выбора папки
        self.button_select_folder = tk.Button(frame, text="3. Выбрать папку с файлами", command=self.select_folder)
        self.button_select_folder.pack(pady=5)

        # Метка для списка файлов
        self.label_files = tk.Label(frame, text="Список CSV-файлов в выбранной папке:")

        # Список файлов
        self.files_listbox = tk.Listbox(frame, width=60, height=10)

        # Кнопка для выбора файла результата (только для GEOKON)
        self.button_select_result_file = tk.Button(frame, text="4. Выбрать файл для сохранения результатов", command=self.select_result_file)

        # Кнопка для обработки файлов
        self.button_process = tk.Button(frame, text="5. Обработать файлы", command=self.process_files, state=tk.DISABLED)
        self.button_process.pack(pady=5)

        # Кнопка для сохранения итогового файла (не нужна для GEOKON)
        self.button_save = tk.Button(frame, text="6. Сохранить результат", command=self.save_output, state=tk.DISABLED)

        # Статусная метка
        self.status_label = tk.Label(frame, text="", fg="green")
        self.status_label.pack(pady=5)

        github_link = tk.Label(frame, text="Исходный код", fg="blue", cursor="hand2", anchor="w")
        github_link.pack(pady=5)
        github_link.bind("<Button-1>", lambda e: self.open_link("https://github.com/some-crap/hydro_loggers/tree/main"))

        telegram_link = tk.Label(frame, text="Разработка", fg="blue", cursor="hand2", anchor="w")
        telegram_link.pack(pady=5)
        telegram_link.bind("<Button-1>", lambda e: self.open_link("https://t.me/y_durov"))

        self.on_sensor_change()  # Инициализация интерфейса в соответствии с выбранным датчиком

    def on_sensor_change(self):
        sensor_type = self.sensor_var.get()
        if sensor_type == "GEOKON":
            # Скрыть элементы, не относящиеся к GEOKON
            self.label_dev_eui.pack_forget()
            self.entry_dev_eui.pack_forget()
            self.label_files.pack_forget()
            self.files_listbox.pack_forget()
            self.button_save.pack_forget()

            # Изменить текст кнопки выбора папки
            self.button_select_folder.config(text="2. Выбрать папку с исходным файлом")

            # Показать кнопку выбора файла результата
            self.button_select_result_file.pack(pady=5)

        else:
            # Показать элементы для GORIZONT и PROMODEM
            self.label_dev_eui.pack(pady=5, anchor='w')
            self.entry_dev_eui.pack(pady=5)
            self.label_files.pack(pady=5, anchor='w')
            self.files_listbox.pack(pady=5)
            self.button_save.pack(pady=10)

            # Скрыть кнопку выбора файла результата
            self.button_select_result_file.pack_forget()

            # Изменить текст кнопки выбора папки
            self.button_select_folder.config(text="3. Выбрать папку с файлами")

    def open_link(self, url):
        webbrowser.open_new(url)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if not self.folder_path:
            self.status_label.config(text="Папка не выбрана.", fg="red")
            self.button_process.config(state=tk.DISABLED)
            return

        sensor_type = self.sensor_var.get()
        if sensor_type == "GEOKON":
            self.status_label.config(text="Папка с исходным файлом выбрана.", fg="green")
            self.button_process.config(state=tk.NORMAL)
        else:
            self.files_listbox.delete(0, tk.END)
            self.files_list = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".csv")]

            for file in self.files_list:
                self.files_listbox.insert(tk.END, file)

            if not self.files_list:
                messagebox.showwarning("Предупреждение", "В выбранной папке нет файлов CSV!")
                self.button_process.config(state=tk.DISABLED)
            else:
                self.button_process.config(state=tk.NORMAL)
                self.status_label.config(text="Папка выбрана. Готово к обработке файлов.", fg="green")

    def select_result_file(self):
        # Выбор файла для сохранения результатов (для GEOKON)
        self.result_file_path = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if self.result_file_path:
            self.status_label.config(text="Файл для сохранения результатов выбран.", fg="green")
        else:
            self.status_label.config(text="Файл для сохранения результатов не выбран.", fg="red")

    def extract_dev_eui_promodem(self):
        # Поиск .txt файлов в папке и извлечение ID датчика
        txt_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".txt")]
        for txt_file in txt_files:
            file_path = os.path.join(self.folder_path, txt_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if "ID=" in line:
                            dev_eui = line.split("ID=")[1].strip().split(")")[0]
                            return dev_eui
            except Exception as e:
                print(f"Ошибка при обработке {txt_file}: {e}")
        return None

    def process_promodem_files(self):
        global sensor_type_for_saving
        sensor_type_for_saving = 1
        if not self.folder_path or not self.files_list:
            messagebox.showerror("Ошибка", "Папка не выбрана или файлы отсутствуют!")
            self.status_label.config(text="Ошибка: Папка не выбрана или файлы отсутствуют!", fg="red")
            return

        # Ищем ID датчика
        self.dev_eui = self.extract_dev_eui_promodem()
        if not self.dev_eui:
            self.dev_eui = self.entry_dev_eui.get()
            if self.dev_eui:
                messagebox.showinfo("Информация", "ID датчика взят из поля ввода.")
            else:
                messagebox.showerror("Ошибка", "ID датчика не найден и не введён!")
                self.status_label.config(text="Ошибка: ID датчика не найден и не введён!", fg="red")
                return

        output_data = []

        # Обработка всех файлов CSV
        for file_name in self.files_list:
            file_path = os.path.join(self.folder_path, file_name)
            try:
                # Чтение CSV файла, приведение названий столбцов к нижнему регистру
                df_raw = pd.read_csv(file_path, delimiter=";", header=0, dtype=str)
                df_raw.columns = [col.lower() for col in df_raw.columns]

                # Проверяем, есть ли столбец 'дата' или пытаемся найти похожий
                date_column = None
                for col in df_raw.columns:
                    if 'дата' in col:
                        date_column = col
                        break

                if not date_column:
                    messagebox.showerror("Ошибка", f"Не удалось найти столбец с датой в файле {file_name}")
                    self.status_label.config(text=f"Ошибка: Нет столбца даты в {file_name}", fg="red")
                    return

                # Фильтруем столбцы, начинающиеся с 'a' (a1, a2, ...)
                a_columns = [col for col in df_raw.columns if col.startswith("a")]

                if not a_columns:
                    messagebox.showerror("Ошибка", f"В файле {file_name} не найдено столбцов, начинающихся с 'a'")
                    self.status_label.config(text=f"Ошибка: Нет столбцов 'a' в {file_name}", fg="red")
                    return

                # Создание пустого DataFrame для добавления данных
                result_df = pd.DataFrame(columns=["ID_ДАТЧИКА", "КАНАЛ", "ДАТА", "ИЗМЕРЕНИЕ"])

                # Заполнение DataFrame данными
                for a_col in a_columns:
                    channel_number = a_col[1:]
                    rows_to_add = pd.DataFrame({
                        "ID_ДАТЧИКА": self.dev_eui,
                        "КАНАЛ": channel_number,
                        "ДАТА": df_raw[date_column],
                        "ИЗМЕРЕНИЕ": df_raw[a_col]
                    })
                    result_df = pd.concat([result_df, rows_to_add], ignore_index=True)
                    result_df.replace("", pd.NA, inplace=True)
                    result_df = result_df.dropna(how='any')
                output_data.append(result_df)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обработке файла {file_name}: {str(e)}")
                self.status_label.config(text=f"Ошибка при обработке {file_name}", fg="red")
                return

        self.output_df = pd.concat(output_data, ignore_index=True)

        if self.output_df.empty:
            messagebox.showwarning("Предупреждение", "Обработанные данные пусты!")
            self.status_label.config(text="Предупреждение: Обработанные данные пусты!", fg="orange")
        else:
            messagebox.showinfo("Успех", "Файлы успешно обработаны!")
            self.status_label.config(text="Файлы успешно обработаны!", fg="green")
            self.button_save.config(state=tk.NORMAL)

    def extract_dev_eui_gorizont(self, config_file_path):
        try:
            with open(config_file_path, 'r', encoding='utf-8') as config_file:
                for line in config_file:
                    if "DEV_EUI =" in line:
                        return line.split("=")[1].strip()
        except UnicodeDecodeError:
            with open(config_file_path, 'r', encoding='cp1251') as config_file:
                for line in config_file:
                    if "DEV_EUI =" in line:
                        return line.split("=")[1].strip()
        return None

    def process_gorizont_files(self):
        global sensor_type_for_saving
        sensor_type_for_saving = 2
        if not self.folder_path or not self.files_list:
            messagebox.showerror("Ошибка", "Папка не выбрана или файлы отсутствуют!")
            self.status_label.config(text="Ошибка: Папка не выбрана или файлы отсутствуют!", fg="red")
            return

        # Найти файл Config.txt для GORIZONT
        config_file_path = os.path.join(self.folder_path, 'Config.txt')
        if os.path.exists(config_file_path):
            self.dev_eui = self.extract_dev_eui_gorizont(config_file_path)
            if not self.dev_eui:
                self.dev_eui = self.entry_dev_eui.get()
                if self.dev_eui:
                    messagebox.showinfo("Информация", "ID датчика взят из поля ввода.")
                else:
                    messagebox.showerror("Ошибка", "ID датчика не найден и не введён вручную!")
                    self.status_label.config(text="Ошибка: ID датчика не найден и не введён!", fg="red")
                    return
        else:
            self.dev_eui = self.entry_dev_eui.get()
            if self.dev_eui:
                messagebox.showinfo("Информация", "ID датчика взят из поля ввода.")
            else:
                messagebox.showerror("Ошибка", "Файл Config.txt не найден, и ID датчика не введён вручную!")
                self.status_label.config(text="Ошибка: ID датчика не найден!", fg="red")
                return

        output_data = []

        # Обработка всех файлов CSV
        for file_name in self.files_list:
            file_path = os.path.join(self.folder_path, file_name)
            try:
                df_raw = pd.read_csv(file_path, skiprows=2, delimiter=";", header=None, dtype=str)

                if df_raw.shape[1] < 3:
                    raise ValueError(f"Недостаточно столбцов в файле {file_name}. Ожидалось минимум 3 столбца.")

                date_time_col = df_raw.iloc[:, 0]

                channels = []
                for col in range(1, len(df_raw.columns), 2):
                    if col + 1 < df_raw.shape[1]:
                        f_col = df_raw.columns[col]
                        r_col = df_raw.columns[col + 1]
                        channels.append((f_col, r_col))

                result_df = pd.DataFrame(columns=["ID_ДАТЧИКА", "НОМЕР_КАНАЛА", "ДАТА_ВРЕМЯ", "ЧАСТОТА", "СОПРОТИВЛЕНИЕ"])

                for i, (f_col, r_col) in enumerate(channels, start=1):
                    rows_to_add = pd.DataFrame({
                        "ID_ДАТЧИКА": self.dev_eui,
                        "НОМЕР_КАНАЛА": i,
                        "ДАТА_ВРЕМЯ": df_raw[0],
                        "ЧАСТОТА": '"' + df_raw[f_col] + '"',
                        "СОПРОТИВЛЕНИЕ": '"' + df_raw[r_col] + '"'
                    })
                    result_df = pd.concat([result_df, rows_to_add], ignore_index=True)
                    result_df.replace("", pd.NA, inplace=True)
                    result_df = result_df.dropna(how='any')
                output_data.append(result_df)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка при обработке файла {file_name}: {str(e)}")
                self.status_label.config(text=f"Ошибка при обработке {file_name}", fg="red")
                return

        self.output_df = pd.concat(output_data, ignore_index=True)
        self.output_df['ДАТА_ВРЕМЯ'] = pd.to_datetime(self.output_df['ДАТА_ВРЕМЯ'], dayfirst=True)
        self.output_df = self.output_df.sort_values(by="ДАТА_ВРЕМЯ")

        if self.output_df.empty:
            messagebox.showwarning("Предупреждение", "Обработанные данные пусты!")
            self.status_label.config(text="Предупреждение: Обработанные данные пусты!", fg="orange")
        else:
            messagebox.showinfo("Успех", "Файлы успешно обработаны!")
            self.status_label.config(text="Файлы успешно обработаны!", fg="green")
            self.button_save.config(state=tk.NORMAL)

    def process_geokon_files(self):
        if not self.folder_path:
            messagebox.showerror("Ошибка", "Папка с исходным файлом не выбрана!")
            self.status_label.config(text="Ошибка: Папка не выбрана!", fg="red")
            return

        # Поиск CSV-файла в выбранной папке
        source_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".csv")]
        if not source_files:
            messagebox.showerror("Ошибка", "В выбранной папке нет CSV-файлов!")
            self.status_label.config(text="Ошибка: В папке нет CSV-файлов!", fg="red")
            return

        input_file_path = os.path.join(self.folder_path, source_files[0])  # Предполагаем, что нужен первый CSV-файл

        if not hasattr(self, 'result_file_path'):
            messagebox.showerror("Ошибка", "Файл для сохранения результатов не выбран!")
            self.status_label.config(text="Ошибка: Файл для результатов не выбран!", fg="red")
            return

        columns = ['logger', 'year', 'month', 'day', 'hours', 'minutes', 'seconds', 'voltage',
                   'temp_outside', 'pressure_1', 'pressure_2', 'pressure_3', 'pressure_4',
                   'temp_1', 'temp_2', 'temp_3', 'temp_4', 'id']

        try:
            df = pd.read_csv(input_file_path, delimiter=",", names=columns, header=None)
            df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hours', 'minutes', 'seconds']])
            df['date'] = df['datetime'].dt.strftime('%d.%m.%Y %H:%M:%S')
            df.drop(['year', 'month', 'day', 'hours', 'minutes', 'seconds', 'datetime'], axis=1, inplace=True)
            columns_ordered = ['date'] + [col for col in df.columns if col != 'date']
            df = df[columns_ordered]
            df = df.replace(-999999.000, pd.NA)
            df.dropna(inplace=True)

            if os.path.exists(self.result_file_path):
                existing_data = pd.read_csv(self.result_file_path)
                combined_data = pd.concat([existing_data, df], ignore_index=True)
                combined_data.drop_duplicates(subset=['date'], keep='first', inplace=True)
                combined_data['date'] = pd.to_datetime(combined_data['date'], format='%d.%m.%Y %H:%M:%S')
                combined_data.sort_values(by='date', inplace=True)
                combined_data.to_csv(self.result_file_path, index=False)
            else:
                df.to_csv(self.result_file_path, index=False)

            messagebox.showinfo("Успех", "Данные успешно обработаны и сохранены!")
            self.status_label.config(text="Данные успешно обработаны и сохранены!", fg="green")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при обработке файла: {str(e)}")
            self.status_label.config(text="Ошибка при обработке файла!", fg="red")

    def process_files(self):
        self.status_label.config(text="", fg="green")
        sensor_type = self.sensor_var.get()
        if sensor_type == "GORIZONT":
            self.process_gorizont_files()
        elif sensor_type == "PROMODEM":
            self.process_promodem_files()
        elif sensor_type == "GEOKON":
            self.process_geokon_files()
        else:
            messagebox.showwarning("Ошибка", "Неизвестный тип датчика!")
            self.status_label.config(text="Ошибка: Неизвестный тип датчика!", fg="red")

    def save_output(self):
        global sensor_type_for_saving
        if not hasattr(self, 'output_df') or self.output_df.empty:
            messagebox.showerror("Ошибка", "Нет данных для сохранения! Сначала обработайте файлы.")
            self.status_label.config(text="Ошибка: Нет данных для сохранения!", fg="red")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            try:
                if sensor_type_for_saving == 1:
                    self.output_df.to_csv(save_path, index=False, header=False, quoting=csv.QUOTE_MINIMAL, escapechar='\\')
                elif sensor_type_for_saving == 2:
                    self.output_df.to_csv(save_path, index=False, header=False, quoting=3)
                else:
                    self.output_df.to_csv(save_path, index=False)
                messagebox.showinfo("Успех", f"Результаты успешно сохранены в {save_path}!")
                self.status_label.config(text=f"Результаты сохранены: {save_path}", fg="green")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении файла: {str(e)}")
                self.status_label.config(text="Ошибка при сохранении файла!", fg="red")
        else:
            messagebox.showwarning("Внимание", "Сохранение файла отменено.")
            self.status_label.config(text="Сохранение файла отменено.", fg="orange")


# Запуск интерфейса
root = tk.Tk()
app = SensorDataProcessorApp(root)
root.mainloop()
