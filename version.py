#!/usr/bin/env python3
"""
Скрипт для управления версиями проекта
"""

import re
import sys
from pathlib import Path

def get_current_version():
    """Получить текущую версию из VERSION файла"""
    version_file = Path("VERSION")
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"

def update_version(new_version):
    """Обновить версию во всех файлах"""
    # Обновляем VERSION файл
    Path("VERSION").write_text(f"{new_version}\n")
    
    # Обновляем pyproject.toml
    pyproject_file = Path("pyproject.toml")
    if pyproject_file.exists():
        content = pyproject_file.read_text()
        content = re.sub(r'version = "[^"]*"', f'version = "{new_version}"', content)
        pyproject_file.write_text(content)
    
    # Обновляем __init__.py если есть
    init_file = Path("__init__.py")
    if init_file.exists():
        content = init_file.read_text()
        content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{new_version}"', content)
        init_file.write_text(content)
    
    print(f"✅ Версия обновлена до {new_version}")

def bump_version(version_type):
    """Увеличить версию"""
    current = get_current_version()
    parts = current.split(".")
    
    if len(parts) != 3:
        print("❌ Неверный формат версии")
        return
    
    major, minor, patch = map(int, parts)
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    else:
        print("❌ Неверный тип версии. Используйте: major, minor, patch")
        return
    
    new_version = f"{major}.{minor}.{patch}"
    update_version(new_version)

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python version.py current          - показать текущую версию")
        print("  python version.py bump major       - увеличить major версию")
        print("  python version.py bump minor       - увеличить minor версию")
        print("  python version.py bump patch       - увеличить patch версию")
        print("  python version.py set 1.2.3        - установить конкретную версию")
        return
    
    command = sys.argv[1]
    
    if command == "current":
        print(f"Текущая версия: {get_current_version()}")
    elif command == "bump":
        if len(sys.argv) < 3:
            print("❌ Укажите тип версии: major, minor, patch")
            return
        bump_version(sys.argv[2])
    elif command == "set":
        if len(sys.argv) < 3:
            print("❌ Укажите версию")
            return
        version = sys.argv[2]
        if re.match(r'^\d+\.\d+\.\d+$', version):
            update_version(version)
        else:
            print("❌ Неверный формат версии. Используйте: X.Y.Z")
    else:
        print("❌ Неизвестная команда")

if __name__ == "__main__":
    main()


