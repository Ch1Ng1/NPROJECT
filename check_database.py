#!/usr/bin/env python
"""Проверка на базата данни"""
from database import DatabaseManager

db = DatabaseManager()

if db.connection and db.connection.is_connected():
    print("✅ Свързване успешно!")
    
    cursor = db.connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print(f"\n📊 Брой таблици: {len(tables)}")
    print("\n📋 Таблици:")
    for t in tables:
        print(f"  ✓ {t[0]}")
    
    # Проверяване на брой редове в главната таблица
    cursor.execute("SELECT COUNT(*) FROM teams")
    teams_count = cursor.fetchone()[0]
    print(f"\n👥 Брой отбори: {teams_count}")
    
else:
    print("❌ Грешка при свързване към базата")
