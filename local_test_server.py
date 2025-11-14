"""
Локальный тестовый сервер для проверки бота
Эмулирует API /api/world-chat
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import urllib.parse

# Хранилище сообщений в памяти
messages_storage = []

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # Парсим query параметры
        parsed_url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_url.query)
        
        if parsed_url.path == '/api/world-chat':
            limit = int(query.get('limit', [100])[0])
            msg_type = query.get('type', ['world'])[0]
            
            # Фильтруем по типу
            filtered = [m for m in messages_storage if m['type'] == msg_type]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'messages': filtered[-limit:],
                'total': len(filtered)
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/world-chat':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            # Валидация
            if not data.get('user_token') or not data.get('nickname') or not data.get('message'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'user_token, nickname и message обязательны'
                }).encode())
                return
            
            # Проверка длины
            if len(data['message']) > 50:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Сообщение слишком длинное (макс. 50 символов)'
                }).encode())
                return
            
            # Сохраняем сообщение
            message = {
                'id': len(messages_storage) + 1,
                'userToken': data['user_token'],
                'nickname': data['nickname'],
                'message': data['message'],
                'type': data.get('type', 'world'),
                'isBot': data.get('is_bot', False),
                'createdAt': datetime.now().isoformat()
            }
            messages_storage.append(message)
            
            print(f"📨 Новое сообщение: [{message['nickname']}] {message['message']}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'message': message
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Подавляем стандартные логи
        pass

def main():
    port = 3001
    server = HTTPServer(('localhost', port), Handler)
    print("=" * 50)
    print("🧪 Локальный тестовый сервер для бота")
    print("=" * 50)
    print(f"\n✅ Сервер запущен на http://localhost:{port}")
    print(f"\n💡 API endpoint: http://localhost:{port}/api/world-chat")
    print("\n📝 Для использования с ботом, добавьте в .env:")
    print(f"   VERCEL_API_URL=http://localhost:{port}")
    print("\n⏹️  Для остановки нажмите Ctrl+C")
    print("\n" + "─" * 50 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✋ Сервер остановлен")
        server.shutdown()

if __name__ == '__main__':
    main()
