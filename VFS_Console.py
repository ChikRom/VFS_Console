import os
import re
import sys
import argparse
import tkinter as tk
from tkinter import scrolledtext

# Поддержка Windows: если HOME не задан, используем USERPROFILE
if 'HOME' not in os.environ and 'USERPROFILE' in os.environ:
    os.environ['HOME'] = os.environ['USERPROFILE']

# --- Парсинг аргументов командной строки ---
parser = argparse.ArgumentParser(description="VFS Console Emulator")
parser.add_argument("--vfs", type=str, help="Путь к виртуальной файловой системе (tar-архив)")
parser.add_argument("--script", type=str, help="Путь к стартовому скрипту")
args = parser.parse_args()

# --- Отладочный вывод параметров ---
print("=== Отладка: параметры запуска ===")
print(f"VFS путь: {args.vfs if args.vfs else 'не задан'}")
print(f"Стартовый скрипт: {args.script if args.script else 'не задан'}")
print("==================================\n")

# --- Функция для раскрытия переменных окружения ---
def expand_env_vars(text):
    def replace_var(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, match.group(0))

    pattern = r'\$(\w+)|\$\{(\w+)\}'
    return re.sub(pattern, replace_var, text)

# --- Функция обработки команды ---
def execute_command(command_line):
    if not command_line.strip():
        return ""

    command_line = expand_env_vars(command_line)
    parts = command_line.split()
    if not parts:
        return ""

    cmd = parts[0]
    args_list = parts[1:]

    if cmd == "ls":
        return f"ls {' '.join(args_list)}\n"

    elif cmd == "cd":
        if len(args_list) != 1:
            return "Ошибка: cd требует ровно один аргумент\n"
        return f"cd {args_list[0]}\n"

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
root.title("VFS")

output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_area.pack(padx=10, pady=10)
output_area.insert(tk.END, "Добро пожаловать в VFS консоль!\n")
output_area.config(state=tk.NORMAL)

entry = tk.Entry(root, width=80)
entry.pack(padx=10, pady=5)
entry.bind("<Return>", on_enter)

button = tk.Button(root, text="Выполнить", command=on_enter)
button.pack(pady=5)

# --- Выполнение стартового скрипта (если указан) ---
# --- Выполнение стартового скрипта (если указан) ---
if args.script and os.path.exists(args.script):
    with open(args.script, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        root.after(100, lambda cmd=line: on_enter(command_text=cmd))

    # Добавляем задержку, чтобы GUI не закрывался сразу
    root.after(500, lambda: None)  # Подождать 5 секунд

# --- Запуск GUI ---
root.mainloop()