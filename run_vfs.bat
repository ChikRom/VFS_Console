@echo off
chcp 65001 >nul
echo Запуск VFS консоли с тестовым скриптом...
python vfs_console.py --vfs dummy.tar --script test_script.txt
pause