import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

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

        label = tk.Label(frame, text="Выберите тип датчика:")
        label.pack()

        gorizont_rb = tk.Radiobutton(frame, text="GORIZONT", variable=self.sensor_var, value="GORIZONT")
        gorizont_rb.pack()

        promodem_rb = tk.Radiobutton(frame, text="PROMODEM", variable=self.sensor_var, value="PROMODEM")
        promodem_rb.pack()

        # Поле для ввода ID датчика
        label_dev_eui = tk.Label(frame, text="ID датчика (если не найден в файлах):")
        label_dev_eui.pack(pady=5)
        self.entry_dev_eui = tk.Entry(frame)
        self.entry_dev_eui.pack(pady=5)

        # Кнопка для выбора папки
        button_select_folder = tk.Button(frame, text="Выбрать папку с файлами", command=self.select_folder)
        button_select_folder.pack()

        # Список файлов
        self.files_listbox = tk.Listbox(frame, width=60, height=10)
        self.files_listbox.pack(pady=5)

        # Кнопка для обработки файлов
        button_process = tk.Button(frame, text="Обработать файлы", command=self.process_files)
        button_process.pack()

        # Кнопка для сохранения итогового файла
        button_save = tk.Button(frame, text="Сохранить результат", command=self.save_output)
        button_save.pack(pady=10)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if not self.folder_path:
            return

        self.files_listbox.delete(0, tk.END)
        # Приводим все имена файлов к нижнему регистру для проверки на расширение .csv
        self.files_list = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".csv")]

        # Отобразить прочитанные файлы в интерфейсе
        for file in self.files_list:
            self.files_listbox.insert(tk.END, file)

        if not self.files_list:
            messagebox.showwarning("Предупреждение", "В выбранной папке нет файлов CSV!")

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
        if not self.folder_path or not self.files_list:
            messagebox.showerror("Ошибка", "Папка не выбрана или файлы отсутствуют!")
            return
    
        # Ищем ID датчика
        self.dev_eui = self.extract_dev_eui_promodem()
        if not self.dev_eui:
            messagebox.showwarning("Предупреждение", "ID датчика не найден в файлах. Использую введённый ID.")
            self.dev_eui = self.entry_dev_eui.get()
    
        if not self.dev_eui:
            messagebox.showerror("Ошибка", "ID датчика не найден и не введён!")
            return
    
        output_data = []

        # Обработка всех файлов CSV
        for file_name in self.files_list:
            file_path = os.path.join(self.folder_path, file_name)
            try:
                # Чтение CSV файла, приведение названий столбцов к нижнему регистру
                df_raw = pd.read_csv(file_path, delimiter=";", header=0, dtype=str)
                df_raw.columns = [col.lower() for col in df_raw.columns]  # Приводим все имена столбцов к нижнему регистру

                # Проверяем, есть ли столбец 'дата' или пытаемся найти похожий
                date_column = None
                for col in df_raw.columns:
                    if 'дата' in col:
                        date_column = col
                        break

                if not date_column:
                    messagebox.showerror("Ошибка", f"Не удалось найти столбец с датой в файле {file_name}")
                    return

                # Фильтруем столбцы, начинающиеся с 'a' (a1, a2, ...), где число после 'a' — это номер канала
                a_columns = [col for col in df_raw.columns if col.startswith("a")]
    
                if not a_columns:
                    messagebox.showerror("Ошибка", f"В файле {file_name} не найдено столбцов, начинающихся с 'a'")
                    return
    
                # Создание пустого DataFrame для добавления данных
                result_df = pd.DataFrame(columns=["ID_ДАТЧИКА", "КАНАЛ", "ДАТА", "ИЗМЕРЕНИЕ"])
    
                # Заполнение DataFrame данными
                for a_col in a_columns:
                    channel_number = a_col[1:]  # Номер канала — всё после 'a'
                    rows_to_add = pd.DataFrame({
                        "ID_ДАТЧИКА": self.dev_eui,
                        "КАНАЛ": channel_number,
                        "ДАТА": df_raw[date_column],  # Используем найденный столбец с датой
                        "ИЗМЕРЕНИЕ": '"' + df_raw[a_col] + '"'  # Значение из a{i} в кавычках
                    })
                    result_df = pd.concat([result_df, rows_to_add], ignore_index=True)

                output_data.append(result_df)
    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обработке файла {file_name}: {str(e)}")
                return
    
        # Объединение данных из всех файлов
        self.output_df = pd.concat(output_data, ignore_index=True)

        if self.output_df.empty:
            messagebox.showwarning("Предупреждение", "Обработанные данные пусты!")
        else:
            messagebox.showinfo("Успех", "Файлы успешно обработаны!")

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
        if not self.folder_path or not self.files_list:
            messagebox.showerror("Ошибка", "Папка не выбрана или файлы отсутствуют!")
            return

        # Найти файл Config.txt для GORIZONT
        config_file_path = os.path.join(self.folder_path, 'Config.txt')
        if os.path.exists(config_file_path):
            self.dev_eui = self.extract_dev_eui_gorizont(config_file_path)
            if not self.dev_eui:
                messagebox.showwarning("Предупреждение", "Не удалось извлечь DEV_EUI из файла Config.txt. Будет использован ID из поля ввода.")
                self.dev_eui = self.entry_dev_eui.get()
        else:
            messagebox.showwarning("Предупреждение", "Файл Config.txt не найден. Будет использован ID из поля ввода.")
            self.dev_eui = self.entry_dev_eui.get()

        if not self.dev_eui:
            messagebox.showerror("Ошибка", "ID датчика не найден и не введён вручную!")
            return

        output_data = []

        # Обработка всех файлов CSV
        for file_name in self.files_list:
            file_path = os.path.join(self.folder_path, file_name)
            try:
                # Чтение данных начиная с третьей строки (пропускаем две строки заголовков)
                df_raw = pd.read_csv(file_path, skiprows=2, delimiter=";", header=None, dtype=str)  # Читаем как строки, чтобы сохранить пробелы
                
                # Проверяем, что файл имеет хотя бы 3 столбца (дата/время и пара F1/R1)
                if df_raw.shape[1] < 3:
                    raise ValueError(f"Недостаточно столбцов в файле {file_name}. Ожидалось минимум 3 столбца.")

                # Первым столбцом должна быть дата и время
                date_time_col = df_raw.iloc[:, 0]  # Столбец с датой и временем
                
                # Определение каналов F{i} и R{i}
                channels = []
                for col in range(1, len(df_raw.columns), 2):
                    if col + 1 < df_raw.shape[1]:  # Проверяем, что столбцы F{i} и R{i} существуют
                        f_col = df_raw.columns[col]
                        r_col = df_raw.columns[col + 1]
                        channels.append((f_col, r_col))

                # Создание пустого DataFrame для добавления данных
                result_df = pd.DataFrame(columns=["ID_ДАТЧИКА", "НОМЕР_КАНАЛА", "ДАТА_ВРЕМЯ", "ЧАСТОТА", "СОПРОТИВЛЕНИЕ"])

                # Заполнение DataFrame данными
                for i, (f_col, r_col) in enumerate(channels, start=1):
                    rows_to_add = pd.DataFrame({
                        "ID_ДАТЧИКА": self.dev_eui,
                        "НОМЕР_КАНАЛА": i,
                        "ДАТА_ВРЕМЯ": df_raw[0],  # Дата и время
                        "ЧАСТОТА": '"' + df_raw[f_col] + '"',  # Частота с кавычками
                        "СОПРОТИВЛЕНИЕ": '"' + df_raw[r_col] + '"'  # Сопротивление с кавычками
                    })
                    # Объединяем текущие строки с результатом
                    result_df = pd.concat([result_df, rows_to_add], ignore_index=True)

                output_data.append(result_df)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка при обработке файла {file_name}: {str(e)}")
                return

        # Объединение данных из всех файлов
        self.output_df = pd.concat(output_data, ignore_index=True)

        # Сортировка по дате и времени
        self.output_df['ДАТА_ВРЕМЯ'] = pd.to_datetime(self.output_df['ДАТА_ВРЕМЯ'], dayfirst=True)
        self.output_df = self.output_df.sort_values(by="ДАТА_ВРЕМЯ")

        if self.output_df.empty:
            messagebox.showwarning("Предупреждение", "Обработанные данные пусты!")
        else:
            messagebox.showinfo("Успех", "Файлы успешно обработаны!")

    def process_files(self):
        sensor_type = self.sensor_var.get()
        if sensor_type == "GORIZONT":
            self.process_gorizont_files()
        elif sensor_type == "PROMODEM":
            self.process_promodem_files()
        else:
            messagebox.showwarning("Ошибка", "Неизвестный тип датчика!")

    def save_output(self):
        if not hasattr(self, 'output_df') or self.output_df.empty:
            messagebox.showerror("Ошибка", "Нет данных для сохранения! Сначала обработайте файлы.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            # Сохраняем данные без заголовков
            self.output_df.to_csv(save_path, index=False, header=False, quoting=3)  # quoting=3 для сохранения кавычек как есть
            messagebox.showinfo("Успех", f"Результаты успешно сохранены в {save_path}!")
        else:
            messagebox.showwarning("Внимание", "Сохранение файла отменено.")

# Запуск интерфейса
root = tk.Tk()
app = SensorDataProcessorApp(root)
root.mainloop()
