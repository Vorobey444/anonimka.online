"""
Тестовый скрипт для проверки работы бота активности
Отправляет несколько тестовых сообщений
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('VERCEL_API_URL', 'https://anonimka.kz')

async def test_send_message(user_token, nickname, message):
    """Отправить тестовое сообщение"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/world-chat",
                json={
                    "user_token": user_token,
                    "nickname": nickname,
                    "message": message,
                    "type": "world",
                    "is_bot": False
                }
            ) as response:
                if response.status == 200:
                    print(f"✅ Отправлено: {message}")
                    return True
                else:
                    print(f"❌ Ошибка {response.status}")
                    text = await response.text()
                    print(f"   {text}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_get_messages():
    """Получить сообщения из чата"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/api/world-chat?limit=10"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    messages = data.get('messages', [])
                    print(f"\n📨 Последние {len(messages)} сообщений:")
                    for msg in messages[-5:]:  # Показываем последние 5
                        bot_mark = "🤖" if msg.get('isBot') else "👤"
                        print(f"  {bot_mark} {msg.get('message', '')[:60]}")
                    return True
                else:
                    print(f"❌ Ошибка получения: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    print("=" * 50)
    print("🧪 Тестирование бота активности")
    print("=" * 50)
    print()
    
    # Проверяем API
    print("1️⃣ Проверка доступности API...")
    if not await test_get_messages():
        print("\n❌ API недоступен!")
        print("   Проверьте:")
        print("   - Файл .env (VERCEL_API_URL)")
        print("   - API endpoint /api/world-chat")
        print("   - Таблицу world_chat_messages в БД")
        return
    
    print("\n✅ API работает!")
    
    # Отправляем тестовые сообщения
    print("\n2️⃣ Отправка тестовых сообщений...")
    
    test_messages = [
        ("test_user_1", "Тестер1", "Привет всем!"),
        ("test_user_2", "Тестер2", "Как дела?"),
        ("test_user_3", "Тестер3", "Кто тут?"),
    ]
    
    for user_token, nickname, message in test_messages:
        await test_send_message(user_token, nickname, message)
        await asyncio.sleep(1)
    
    # Проверяем что сообщения появились
    print("\n3️⃣ Проверка отправленных сообщений...")
    await asyncio.sleep(2)
    await test_get_messages()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("=" * 50)
    print()
    print("💡 Теперь можно запустить бота:")
    print("   - start_activity_bot.bat (базовая версия)")
    print("   - start_smart_bot.bat (умная версия)")
    print()

if __name__ == '__main__':
    asyncio.run(main())
