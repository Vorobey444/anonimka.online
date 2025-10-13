#!/usr/bin/env python3
"""
Простой HTTP сервер для размещения Telegram Web App
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Настройки сервера
PORT = 8000
WEBAPP_DIR = Path(__file__).parent / "webapp"

class WebAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBAPP_DIR), **kwargs)
    
    def end_headers(self):
        # Добавляем CORS заголовки для работы с Telegram
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Обработка preflight запросов
        self.send_response(200)
        self.end_headers()

def main():
    """Запуск сервера"""
    
    # Проверяем существование директории webapp
    if not WEBAPP_DIR.exists():
        print(f"❌ Директория {WEBAPP_DIR} не найдена!")
        return
    
    print(f"🌐 Запуск веб-сервера для Telegram Mini App...")
    print(f"📁 Директория: {WEBAPP_DIR}")
    print(f"🔗 Локальный URL: http://localhost:{PORT}")
    print(f"🌍 Сетевой URL: http://192.168.1.100:{PORT} (замените IP на ваш)")
    print()
    print("📋 Для использования с Telegram Bot:")
    print(f"   1. Разместите файлы на публичном HTTPS сервере")
    print(f"   2. Замените WEBAPP_URL в webapp_bot.py на ваш URL")
    print(f"   3. Запустите бота с помощью: python webapp_bot.py")
    print()
    print("⚠️  Для локального тестирования используйте ngrok:")
    print("   ngrok http 8000")
    print()
    
    try:
        with socketserver.TCPServer(("", PORT), WebAppHandler) as httpd:
            print(f"✅ Сервер запущен на порту {PORT}")
            print("🔄 Нажмите Ctrl+C для остановки")
            
            # Открываем браузер (опционально)
            # webbrowser.open(f'http://localhost:{PORT}')
            
            httpd.serve_forever()
    
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except OSError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        print(f"💡 Попробуйте другой порт или закройте процессы на порту {PORT}")

if __name__ == "__main__":
    main()