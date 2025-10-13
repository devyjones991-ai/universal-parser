#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов с различными конфигурациями
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Запуск команды с выводом описания"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Команда: {command}")
    print()
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов Universal Parser")
    parser.add_argument("--type", choices=["unit", "integration", "performance", "all"], 
                       default="all", help="Тип тестов для запуска")
    parser.add_argument("--coverage", action="store_true", help="Включить проверку покрытия")
    parser.add_argument("--parallel", action="store_true", help="Запустить тесты параллельно")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--fast", action="store_true", help="Пропустить медленные тесты")
    
    args = parser.parse_args()
    
    # Базовые опции pytest
    pytest_args = ["pytest"]
    
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    if args.coverage:
        pytest_args.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    if args.parallel:
        pytest_args.extend(["-n", "auto"])
    
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    
    # Выбор типа тестов
    if args.type == "unit":
        pytest_args.extend(["-m", "not integration and not slow"])
    elif args.type == "integration":
        pytest_args.extend(["-m", "integration"])
    elif args.type == "performance":
        pytest_args.extend(["-m", "slow"])
    
    # Добавляем путь к тестам
    pytest_args.append("tests/")
    
    # Формируем команду
    command = " ".join(pytest_args)
    
    print("🚀 Запуск тестов Universal Parser")
    print(f"📊 Тип тестов: {args.type}")
    print(f"📈 Покрытие: {'Да' if args.coverage else 'Нет'}")
    print(f"⚡ Параллельно: {'Да' if args.parallel else 'Нет'}")
    print(f"🏃 Быстрый режим: {'Да' if args.fast else 'Нет'}")
    
    # Запускаем тесты
    success = run_command(command, "Запуск тестов")
    
    if success:
        print("\n✅ Все тесты прошли успешно!")
        
        if args.coverage:
            print("\n📊 Отчет о покрытии создан в htmlcov/index.html")
        
        return 0
    else:
        print("\n❌ Некоторые тесты провалились!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
