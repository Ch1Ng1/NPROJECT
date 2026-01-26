#!/usr/bin/env python
"""Преглед конфигурация"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=== MySQL Конфигурация ===")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"User: {os.getenv('DB_USER')}")
print(f"Password: {'*' * len(os.getenv('DB_PASSWORD', ''))}")
print(f"Database: {os.getenv('DB_NAME')}")
print(f"Port: {os.getenv('DB_PORT')}")

print("\n=== Тест на Свързване ===")
try:
    import mysql.connector
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    if db.is_connected():
        print("✅ УСПЕШНО СВЪРЗВАНЕ!")
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📊 Таблици: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        db.close()
    else:
        print("❌ Грешка при свързване")
except Exception as e:
    print(f"❌ Грешка: {e}")
