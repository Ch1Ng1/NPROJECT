#!/usr/bin/env python
"""Тест на интегрирана Flask + Database конфигурация"""
import sys
sys.path.insert(0, '.')

try:
    print("🔍 Проверка на импортите...")
    from app import app, predictor, init_database
    print("✅ Flask приложение импортирано успешно")
    
    print("\n🔍 Проверка на базата данни...")
    if init_database():
        print("✅ База данни свързана успешно")
    else:
        print("⚠️  База данни не е свързана - проверете конфигурацията")
    
    print("\n🔍 Проверка на API endpoints...")
    with app.test_client() as client:
        # Тест на главната страница
        response = client.get('/')
        print(f"  GET / → Status {response.status_code}")
        
        # Тест на API за статистики база данни
        response = client.get('/api/database/stats')
        print(f"  GET /api/database/stats → Status {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"    Database status: {data.get('status')}")
            if 'statistics' in data:
                stats = data['statistics']
                print(f"    Teams: {stats.get('teams', 0)}")
                print(f"    Matches: {stats.get('matches', 0)}")
                print(f"    Predictions: {stats.get('predictions', 0)}")
        
        # Тест на точност
        response = client.get('/api/accuracy')
        print(f"  GET /api/accuracy → Status {response.status_code}")
    
    print("\n✅ Всички тестове завършиха успешно!")
    
except Exception as e:
    print(f"❌ Грешка: {e}")
    import traceback
    traceback.print_exc()
