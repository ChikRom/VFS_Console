import os
import re
import tkinter as tk
from tkinter import scrolledtext

# Поддержка Windows: если HOME не задан, используем USERPROFILE
if 'HOME' not in os.environ and 'USERPROFILE' in os.environ:
    os.environ['HOME'] = os.environ['USERPROFILE']

# --- Функция для раскрытия переменных окружения ---
def expand_env_vars(text):
    # Находим все $VAR или ${VAR}
    def replace_var(match):
        var_name = match.group(1) or match.group(2)  # $VAR или ${VAR}
        return os.environ.get(var_name, match.group(0))  # если нет — оставляем как есть

    # Регулярное выражение для $VAR и ${VAR}
    pattern = r'\$(\w+)|\$\{(\w+)\}'
    return re.sub(pattern, replace_var, text)

# --- Функция обработки команды ---
def execute_command(command_line):
    if not command_line.strip():
        return ""

    # Раскрываем переменные окружения
    command_line = expand_env_vars(command_line)

    # Разбиваем на части
    parts = command_line.split()
    if not parts:
        return ""

    cmd = parts[0]
    args = parts[1:]

    # Обработка команд
    if cmd == "ls":
        return f"ls {' '.join(args)}\n"

    elif cmd == "cd":
        if len(args) != 1:
            return "Ошибка: cd требует ровно один аргумент\n"
        return f"cd {args[0]}\n"

    elif cmd == "exit":
        root.quit()  # Закрываем приложение
        return "Выход...\n"

    else:
        return f"Ошибка: неизвестная команда '{cmd}'\n"

# --- Функция обработки ввода ---
def on_enter(event=None):
    # Получаем введённую строку
    command = entry.get()
    output_area.insert(tk.END, f"$ {command}\n")

    # Выполняем команду
    result = execute_command(command)
    output_area.insert(tk.END, result)

    # Очищаем поле ввода
    entry.delete(0, tk.END)

    # Прокручиваем вниз
    output_area.see(tk.END)

# --- Создание GUI ---
root = tk.Tk()
root.title("VFS")  # Требование 2: заголовок окна

# Поле вывода (история команд и результатов)
output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_area.pack(padx=10, pady=10)
output_area.insert(tk.END, "Добро пожаловать в VFS консоль!\n")
output_area.config(state=tk.NORMAL)  # чтобы можно было писать

# Поле ввода
entry = tk.Entry(root, width=80)
entry.pack(padx=10, pady=5)
entry.bind("<Return>", on_enter)  # Нажатие Enter

# Кнопка "Выполнить"
button = tk.Button(root, text="Выполнить", command=on_enter)
button.pack(pady=5)

# Запуск GUI
root.mainloop()