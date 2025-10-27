#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер для отправки писем через Яндекс.Почту
Использует технический ящик wish.online@yandex.kz для отправки писем
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Конфигурация почты
EMAIL_CONFIG = {
    'smtp_server': 'smtp.yandex.kz',
    'smtp_port': 587,
    'sender_email': 'wish.online@yandex.kz',
    'sender_password': 'aitmytqacblwvpjc',
    'recipient_email': 'aleksey@vorobey444.ru'
}

def send_email(sender_email, subject, message):
    """
    Отправляет письмо через Яндекс.Почту
    """
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = subject
        
        # Формируем тело письма
        email_body = f"""
Новое сообщение с сайта anonimka.online

От: {sender_email}
Тема: {subject}
Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Сообщение:
{message}

---
Это письмо отправлено автоматически с сайта anonimka.online
Для ответа используйте адрес: {sender_email}
"""
        
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Подключаемся к серверу и отправляем
        context = ssl.create_default_context()
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        logger.info(f"Письмо успешно отправлено от {sender_email}")
        return True, None
        
    except Exception as e:
        error_msg = f"Ошибка отправки письма: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

@app.route('/send-email', methods=['POST'])
def handle_send_email():
    """
    API endpoint для отправки писем
    """
    try:
        data = request.get_json()
        
        # Валидация данных
        sender_email = data.get('senderEmail', '').strip()
        subject = data.get('subject', 'Сообщение с anonimka.online').strip()
        message = data.get('message', '').strip()
        
        if not sender_email or not message:
            return jsonify({
                'success': False,
                'error': 'Отсутствуют обязательные поля'
            }), 400
        
        if len(message) < 10:
            return jsonify({
                'success': False,
                'error': 'Сообщение слишком короткое'
            }), 400
        
        # Отправляем письмо
        success, error = send_email(sender_email, subject, message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Письмо успешно отправлено'
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500
            
    except Exception as e:
        logger.error(f"Ошибка в handle_send_email: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500

@app.route('/api/send-email', methods=['POST'])
def handle_send_email_api():
    """
    API endpoint для отправки писем (альтернативный путь)
    """
    return handle_send_email()

@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервера
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'email_config': {
            'smtp_server': EMAIL_CONFIG['smtp_server'],
            'sender_email': EMAIL_CONFIG['sender_email'],
            'recipient_email': EMAIL_CONFIG['recipient_email']
        }
    })

@app.route('/', methods=['GET'])
def root():
    """
    Корневая страница
    """
    return jsonify({
        'service': 'Email Service for anonimka.online',
        'version': '1.0',
        'endpoints': ['/send-email', '/api/send-email', '/health']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Запуск сервера email на порту {port}")
    logger.info(f"Debug режим: {debug_mode}")
    logger.info(f"SMTP сервер: {EMAIL_CONFIG['smtp_server']}")
    logger.info(f"Отправитель: {EMAIL_CONFIG['sender_email']}")
    logger.info(f"Получатель: {EMAIL_CONFIG['recipient_email']}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)