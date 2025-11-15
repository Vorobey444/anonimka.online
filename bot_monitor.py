#!/usr/bin/env python3
"""
🔍 Скрипт мониторинга ботов
- Проверяет запущены ли боты
- Отправляет уведомление в Telegram если бот упал
- Проверяет логи на критические ошибки
"""

import os
import subprocess
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = 884253640
CHECK_INTERVAL = 300  # 5 минут

SERVICES_TO_MONITOR = [
    'telegram-bot.service'
]

def send_telegram_alert(message):
    """Отправить уведомление админу в Telegram"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден")
        return
    
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': ADMIN_ID,
            'text': f'🚨 <b>ALERT от мониторинга ботов</b>\n\n{message}',
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Уведомление отправлено: {message[:50]}...")
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")

def check_service_status(service_name):
    """Проверить статус systemd сервиса"""
    try:
        result = subprocess.run(
            ['/usr/bin/systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        print(f"❌ Ошибка проверки {service_name}: {e}")
        return False

def get_service_logs(service_name, lines=20):
    """Получить последние логи сервиса"""
    try:
        result = subprocess.run(
            ['/usr/bin/journalctl', '-u', service_name, '-n', str(lines), '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except Exception as e:
        print(f"❌ Ошибка получения логов {service_name}: {e}")
        return ""

def check_for_errors_in_logs(service_name):
    """Проверить логи на критические ошибки"""
    logs = get_service_logs(service_name, lines=50)
    
    error_keywords = [
        'ERROR',
        'CRITICAL',
        'Exception',
        'Traceback',
        'Failed',
        'Connection refused',
        'Timeout'
    ]
    
    errors = []
    for line in logs.split('\n'):
        for keyword in error_keywords:
            if keyword in line:
                errors.append(line.strip())
                break
    
    return errors

def restart_service(service_name):
    """Попытаться перезапустить сервис"""
    try:
        subprocess.run(
            ['/usr/bin/systemctl', 'restart', service_name],
            timeout=30
        )
        time.sleep(5)  # Ждем 5 секунд после перезапуска
        return check_service_status(service_name)
    except Exception as e:
        print(f"❌ Ошибка перезапуска {service_name}: {e}")
        return False

def monitor_bots():
    """Основной цикл мониторинга"""
    print(f"🔍 Запуск мониторинга ботов...")
    print(f"📊 Проверка каждые {CHECK_INTERVAL} секунд")
    print(f"📱 Уведомления отправляются на Telegram ID: {ADMIN_ID}")
    
    # Отправляем уведомление о запуске мониторинга
    send_telegram_alert(
        f"✅ Мониторинг ботов запущен\n"
        f"⏰ Интервал проверки: {CHECK_INTERVAL // 60} минут\n"
        f"🤖 Отслеживаемые сервисы:\n" + 
        "\n".join([f"  • {s}" for s in SERVICES_TO_MONITOR])
    )
    
    service_down_count = {service: 0 for service in SERVICES_TO_MONITOR}
    
    while True:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{'='*60}")
            print(f"[{timestamp}] Проверка статуса ботов...")
            
            for service in SERVICES_TO_MONITOR:
                is_active = check_service_status(service)
                
                if is_active:
                    print(f"✅ {service}: активен")
                    service_down_count[service] = 0
                    
                    # Проверяем логи на ошибки
                    errors = check_for_errors_in_logs(service)
                    if errors:
                        error_summary = '\n'.join(errors[-3:])  # Последние 3 ошибки
                        print(f"⚠️  Обнаружены ошибки в {service}")
                        send_telegram_alert(
                            f"⚠️ <b>Ошибки в {service}</b>\n\n"
                            f"<code>{error_summary[:1000]}</code>\n\n"
                            f"Бот работает, но есть ошибки в логах."
                        )
                else:
                    service_down_count[service] += 1
                    print(f"❌ {service}: НЕ АКТИВЕН (попыток: {service_down_count[service]})")
                    
                    # Пытаемся перезапустить
                    print(f"🔄 Попытка перезапустить {service}...")
                    restarted = restart_service(service)
                    
                    if restarted:
                        print(f"✅ {service} успешно перезапущен")
                        send_telegram_alert(
                            f"🔄 <b>{service} был перезапущен</b>\n\n"
                            f"Бот упал, но автоматически восстановлен."
                        )
                        service_down_count[service] = 0
                    else:
                        # Если не удалось перезапустить
                        logs = get_service_logs(service, lines=30)
                        send_telegram_alert(
                            f"🚨 <b>КРИТИЧНО: {service} не работает!</b>\n\n"
                            f"❌ Бот упал и не запускается более {service_down_count[service] * CHECK_INTERVAL // 60} минут\n\n"
                            f"📋 <b>Последние логи:</b>\n"
                            f"<code>{logs[-1000:]}</code>"
                        )
            
            print(f"\n⏳ Следующая проверка через {CHECK_INTERVAL} секунд...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⛔ Мониторинг остановлен пользователем")
            send_telegram_alert("⛔ Мониторинг ботов остановлен")
            break
        except Exception as e:
            print(f"❌ Критическая ошибка мониторинга: {e}")
            send_telegram_alert(
                f"💥 <b>Ошибка в скрипте мониторинга</b>\n\n"
                f"<code>{str(e)}</code>\n\n"
                f"Мониторинг продолжит работу."
            )
            time.sleep(60)  # Ждем минуту перед следующей попыткой

if __name__ == '__main__':
    monitor_bots()
