#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Профессиональный Email сервер для anonimka.online
Отправка с технического адреса wish.online@yandex.kz
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import logging
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email конфигурация
SMTP_SERVER = 'smtp.yandex.ru'
SMTP_PORT = 587
SENDER_EMAIL = 'wish.online@yandex.kz'
SENDER_PASSWORD = 'aitmytqacblwvpjc'  # Пароль приложения
RECIPIENT_EMAIL = 'vorobey469@yandex.ru'

def send_email_via_yandex(sender_email, subject, message):
    """
    Отправка email через Yandex SMTP
    """
    try:
        logger.info(f"📧 Подготовка письма от {sender_email}")
        
        # Создание сообщения
        msg = MIMEMultipart('alternative')
        msg['From'] = Header(f'Anonimka.Online <{SENDER_EMAIL}>', 'utf-8')
        msg['To'] = Header(f'Алексей <{RECIPIENT_EMAIL}>', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Reply-To'] = Header(sender_email, 'utf-8')
        
        # Создание HTML и текстовой версии
        text_body = f"""
Новое сообщение с сайта anonimka.online

От: {sender_email}
Тема: {subject}
Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Сообщение:
{message}

---
Это письмо отправлено с сайта anonimka.online
Для ответа используйте адрес: {sender_email}
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .message {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .info {{ color: #666; font-size: 14px; margin-top: 20px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🌟 Новое сообщение с anonimka.online</h2>
        </div>
        <div class="content">
            <div class="info">
                <strong>От:</strong> {sender_email}<br>
                <strong>Тема:</strong> {subject}<br>
                <strong>Время:</strong> {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}<br>
            </div>
            <div class="message">
                <strong>Сообщение:</strong><br><br>
                {message.replace(chr(10), '<br>')}
            </div>
            <div class="footer">
                Письмо отправлено с сайта <strong>anonimka.online</strong><br>
                Для ответа используйте адрес: <strong>{sender_email}</strong>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        # Добавление частей сообщения
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Подключение к SMTP серверу
        logger.info(f"🔗 Подключение к {SMTP_SERVER}:{SMTP_PORT}")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Включение шифрования
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            # Отправка письма
            server.send_message(msg, from_addr=SENDER_EMAIL, to_addrs=[RECIPIENT_EMAIL])
            
        logger.info("✅ Письмо успешно отправлено через Yandex SMTP")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Ошибка аутентификации SMTP: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ Ошибка SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Общая ошибка отправки: {e}")
        return False

@app.route('/send-email', methods=['POST', 'OPTIONS'])
def send_email():
    """
    Endpoint для отправки email
    """
    if request.method == 'OPTIONS':
        # Обработка preflight запроса
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        data = request.get_json()
        logger.info(f"📨 Получен запрос на отправку: {data}")
        
        # Валидация данных
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
            
        sender_email = data.get('senderEmail', '').strip()
        subject = data.get('subject', 'Сообщение с anonimka.online').strip()
        message = data.get('message', '').strip()
        
        if not sender_email or not message:
            return jsonify({'error': 'Отсутствуют обязательные поля'}), 400
            
        # Базовая валидация email
        if '@' not in sender_email or '.' not in sender_email.split('@')[1]:
            return jsonify({'error': 'Неверный формат email'}), 400
            
        if len(message) < 10:
            return jsonify({'error': 'Сообщение слишком короткое'}), 400
        
        # Отправка письма
        success = send_email_via_yandex(sender_email, subject, message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Письмо успешно отправлено',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Ошибка отправки письма'}), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки запроса: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервера
    """
    return jsonify({
        'status': 'ok',
        'service': 'Yandex Email Server',
        'version': '1.0',
        'sender': SENDER_EMAIL,
        'recipient': RECIPIENT_EMAIL,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test-email', methods=['POST'])
def test_email():
    """
    Тестовая отправка письма
    """
    try:
        success = send_email_via_yandex(
            'test@anonimka.online',
            'Тестовое письмо от Yandex сервера',
            'Это тестовое сообщение для проверки работы нового email сервера с Yandex SMTP.\n\nВсе работает отлично! 🎉'
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Тестовое письмо отправлено',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Ошибка отправки тестового письма'}), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестовой отправки: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Запуск Yandex Email Server для anonimka.online")
    print(f"📧 Отправитель: {SENDER_EMAIL}")
    print(f"📬 Получатель: {RECIPIENT_EMAIL}")
    print(f"🌐 Сервер: http://localhost:5000")
    print("📡 Endpoints:")
    print("   POST /send-email - отправка письма")
    print("   GET /health - проверка работоспособности")
    print("   POST /test-email - тестовая отправка")
    
    app.run(debug=True, host='0.0.0.0', port=5000)