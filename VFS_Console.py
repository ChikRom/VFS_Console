import os
import re
import sys
import csv
import base64
import argparse
import tkinter as tk
from tkinter import scrolledtext

# Поддержка Windows: если HOME не задан, используем USERPROFILE
if 'HOME' not in os.environ and 'USERPROFILE' in os.environ:
    os.environ['HOME'] = os.environ['USERPROFILE']

# --- Парсинг аргументов командной строки ---
parser = argparse.ArgumentParser(description="VFS Console Emulator")
parser.add_argument("--vfs", type=str, help="Путь к виртуальной файловой системе (CSV-файл)")
parser.add_argument("--script", type=str, help="Путь к стартовому скрипту")
args = parser.parse_args()

# --- Отладочный вывод параметров ---
print("=== Отладка: параметры запуска ===")
print(f"VFS путь: {args.vfs if args.vfs else 'не задан'}")
print(f"Стартовый скрипт: {args.script if args.script else 'не задан'}")
print("==================================\n")

# --- Загрузка VFS из CSV ---
vfs = []          # Список всех элементов VFS
current_dir = "/" # Текущая директория

def load_vfs(csv_path):
    global vfs
    if not os.path.exists(csv_path):
        print(f"Ошибка: VFS файл '{csv_path}' не найден!")
        sys.exit(1)

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required_columns = ['path', 'type', 'content']
            if not all(col in reader.fieldnames for col in required_columns):
                print("Ошибка: Неверный формат CSV. Ожидаются колонки: path, type, content")
                sys.exit(1)

            vfs = list(reader)
            # Проверим, что корень есть
            if not any(item['path'] == '/' and item['type'] == 'dir' for item in vfs):
                print("Ошибка: В VFS отсутствует корневая директория '/'")
                sys.exit(1)

            print(f"VFS успешно загружена из {csv_path}")
    except Exception as e:
        print(f"Ошибка при загрузке VFS: {e}")
        sys.exit(1)

# Загружаем VFS, если указан аргумент
if args.vfs:
    load_vfs(args.vfs)
else:
    print("Предупреждение: VFS не указана. Работа в ограниченном режиме.")
    vfs = [{"path": "/", "type": "dir", "content": ""}]

# --- Функция для раскрытия переменных окружения ---
def expand_env_vars(text):
    def replace_var(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, match.group(0))

    pattern = r'\$(\w+)|\$\{(\w+)\}'
    return re.sub(pattern, replace_var, text)

# --- Функция обработки команды ---
def execute_command(command_line):
    global current_dir
    if not command_line.strip():
        return ""

    command_line = expand_env_vars(command_line)
    parts = command_line.split()
    if not parts:
        return ""

    cmd = parts[0]
    args_list = parts[1:]

    if cmd == "ls":
        items = []
        current_clean = current_dir.rstrip('/')
        for item in vfs:
            path = item['path']
            if path == current_clean:
                continue  # не показываем саму текущую директорию
            if path.startswith(current_clean + '/') or (current_clean == '/' and path.startswith('/')):
                # Убираем текущий путь, оставляем только имя
                rel_path = path[len(current_clean):].lstrip('/')
                if '/' not in rel_path or rel_path.endswith('/'):  # только первый уровень
                    name = rel_path.split('/')[0]
                    items.append(name + ('/' if item['type'] == 'dir' else ''))

        if items:
            return '\n'.join(sorted(set(items))) + '\n'
        else:
            return ""


    elif cmd == "cd":

        if len(args_list) != 1:
            return "Ошибка: cd требует ровно один аргумент\n"

        target = args_list[0]

        # Обработка ..

        if target == "..":

            if current_dir == "/":
                return ""  # уже в корне

            # Убираем последнюю папку

            parts = current_dir.rstrip('/').split('/')

            new_path = '/'.join(parts[:-1]) or '/'

            current_dir = new_path + ('/' if new_path != '/' else '')

            return ""

        # Абсолютный путь

        if target.startswith('/'):

            if target == '/':

                new_path = '/'

            else:

                new_path = target.rstrip('/') + '/'

        else:

            # Относительный путь

            new_path = (current_dir.rstrip('/') + '/' + target).rstrip('/') + '/'

        # Проверяем, существует ли такая директория

        check_path = new_path.rstrip('/') if new_path != '/' else '/'

        if any(item['path'] == check_path and item['type'] == 'dir' for item in vfs):

            current_dir = new_path

            return ""

        else:

            return f"Ошибка: директория '{target}' не найдена\n"

    elif cmd == "cat":
        if len(args_list) != 1:
            return "Ошибка: cat требует ровно один аргумент\n"
        filename = args_list[0]

        # Формируем полный путь
        full_path = os.path.join(current_dir.rstrip('/'), filename).replace('\\', '/')
        if not full_path.startswith('/'):
            full_path = '/' + full_path

        # Ищем файл
        for item in vfs:
            if item['path'] == full_path and item['type'] == 'file':
                try:
                    decoded = base64.b64decode(item['content']).decode('utf-8')
                    return decoded + '\n'
                except Exception:
                    return "Ошибка: не удалось декодировать содержимое файла\n"
        return f"Ошибка: файл '{filename}' не найден\n"

    elif cmd == "vfs-save":
        if len(args_list) != 1:
            return "Ошибка: vfs-save требует ровно один аргумент — путь для сохранения\n"
        save_path = args_list[0]
        try:
            with open(save_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['path', 'type', 'content'])
                writer.writeheader()
                writer.writerows(vfs)
            return f"VFS сохранена в {save_path}\n"
        except Exception as e:
            return f"Ошибка при сохранении VFS: {e}\n"

    elif cmd == "exit":
        root.quit()
        return "Выход...\n"

    else:
        return f"Ошибка: неизвестная команда '{cmd}'\n"

# --- Функция обработки ввода (вызывается при Enter или из скрипта) ---
def on_enter(event=None, command_text=None):
    # Если команда передана из скрипта — используем её, иначе из поля ввода
    command = command_text if command_text is not None else entry.get()

    # Выводим команду с приглашением, как в реальной консоли
    output_area.insert(tk.END, f"$ {command}\n")

    # Выполняем команду
    result = execute_command(command)
    output_area.insert(tk.END, result)

    # Если команда из интерфейса — очищаем поле ввода
    if command_text is None:
        entry.delete(0, tk.END)

    # Прокручиваем вниз
    output_area.see(tk.END)

# --- Создание GUI ---
root = tk.Tk()
root.title("VFS Console Emulator")

output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_area.pack(padx=10, pady=10)
output_area.insert(tk.END, f"Добро пожаловать в VFS консоль! Текущая директория: {current_dir}\n")
output_area.config(state=tk.NORMAL)

entry = tk.Entry(root, width=80)
entry.pack(padx=10, pady=5)
entry.bind("<Return>", on_enter)

button = tk.Button(root, text="Выполнить", command=on_enter)
button.pack(pady=5)

# --- Выполнение стартового скрипта (если указан) ---
if args.script and os.path.exists(args.script):
    with open(args.script, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Используем after, чтобы команды не блокировали GUI
        root.after(i * 300, lambda cmd=line: on_enter(command_text=cmd))

# --- Запуск GUI ---
root.mainloop()