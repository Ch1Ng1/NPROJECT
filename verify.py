#!/usr/bin/env python3
"""
🎯 Smart Football Predictor - v2.0 Verification Script
Проверява дали всички компоненти са функционални
"""

import sys
import os
from pathlib import Path

def check_file_exists(path: str, min_size: int = 0) -> bool:
    """Проверява дали файл съществува и има достатъчен размер"""
    p = Path(path)
    if not p.exists():
        print(f"❌ {path} - НЕ СЪЩЕСТВУВА")
        return False
    if p.stat().st_size < min_size:
        print(f"❌ {path} - ТА ЛИЧ (только {p.stat().st_size} bytes, необходимо {min_size})")
        return False
    print(f"✅ {path} - OK ({p.stat().st_size} bytes)")
    return True

def check_import(module_name: str) -> bool:
    """Проверява дали модул може да се импортира"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - импортиран успешно")
        return True
    except Exception as e:
        print(f"❌ {module_name} - {str(e)}")
        return False

def check_directory_exists(path: str) -> bool:
    """Проверява дали директория съществува"""
    p = Path(path)
    if p.exists() and p.is_dir():
        print(f"✅ {path} - директория съществува")
        return True
    print(f"❌ {path} - директория НЕ СЪЩЕСТВУВА")
    return False

def main():
    """Главна функция за проверка"""
    print("=" * 60)
    print("🎯 Smart Football Predictor - v2.0 ПРОВЕРКА")
    print("=" * 60)
    
    all_ok = True
    
    # Проверка на файлове
    print("\n📁 Проверка на файлове:")
    print("-" * 60)
    
    files = {
        'app.py': 1000,
        'predictor.py': 5000,
        'utils.py': 1000,
        'requirements.txt': 50,
        '.env': 50,
        '.gitignore': 10,
        'README.md': 500,
        'templates/index.html': 5000,
        'templates/styles.css': 5000,
        'templates/script.js': 5000,
    }
    
    for file, min_size in files.items():
        if not check_file_exists(file, min_size):
            all_ok = False
    
    # Проверка на директории
    print("\n📂 Проверка на директории:")
    print("-" * 60)
    
    directories = [
        'logs',
        'templates',
        '.venv',
    ]
    
    for dir_path in directories:
        if not check_directory_exists(dir_path):
            all_ok = False
    
    # Проверка на импорти
    print("\n📦 Проверка на импорти:")
    print("-" * 60)
    
    modules = [
        'flask',
        'requests',
        'dotenv',
        'predictor',
        'utils',
    ]
    
    for module in modules:
        if not check_import(module):
            all_ok = False
    
    # Резюме
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ ВСЕ КОМПОНЕНТИ ГОТОВИ ЗА ИЗПЪЛНЕНИЕ!")
        print("\nЗАПУСК:")
        print("  cd c:\\xampp\\htdocs\\NPROJECT")
        print("  .venv\\Scripts\\python.exe app.py")
        print("\nТогава отворете:")
        print("  http://localhost:5000")
        return 0
    else:
        print("❌ НЯКОИ КОМПОНЕНТИ НЕ СА ГОТОВИ")
        return 1

if __name__ == '__main__':
    sys.exit(main())
