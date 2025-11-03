# Инструкция по запуску нового бота с Neon интеграцией

## Что изменилось

Создан новый файл `bot_neon.py` который работает с Neon PostgreSQL вместо локальной памяти.

### Основные улучшения:

1. ✅ **Синхронизация с WebApp** - все чаты и сообщения хранятся в Neon
2. ✅ **Уведомления** - бот получает уведомления через API
3. ✅ **Команды:**
   - `/start` - приветствие и ссылка на WebApp
   - `/my_chats` - список активных чатов
4. ✅ **Отправка сообщений** - через выбранный активный чат
5. ✅ **Чтение сообщений** - помечаются как прочитанные

## Запуск нового бота

### 1. Остановите старый бот (если запущен)

```bash
# Найдите процесс старого бота
ps aux | grep bot.py

# Убейте процесс
kill <PID>
```

### 2. Установите зависимости (если нужно)

```bash
cd anon-board-bot
pip install python-telegram-bot aiohttp
```

### 3. Настройте переменные окружения

Убедитесь что установлены:
- `TELEGRAM_BOT_TOKEN` - токен бота
- `VERCEL_API_URL` - URL вашего API (по умолчанию `https://anonimka.kz`)

### 4. Запустите новый бот

```bash
python bot_neon.py
```

### 5. Для production (с автозапуском)

Создайте systemd service:

```ini
# /etc/systemd/system/anonimka-bot.service
[Unit]
Description=Anonimka Telegram Bot with Neon
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/anon-board-bot
Environment="TELEGRAM_BOT_TOKEN=your_token_here"
Environment="VERCEL_API_URL=https://anonimka.kz"
ExecStart=/usr/bin/python3 bot_neon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable anonimka-bot
sudo systemctl start anonimka-bot
sudo systemctl status anonimka-bot
```

## Тестирование

1. Откройте бота в Telegram
2. Отправьте `/start` - должна появиться кнопка WebApp
3. Создайте чат в WebApp
4. Отправьте `/my_chats` - должен появиться список чатов
5. Выберите чат и отправьте сообщение
6. Проверьте в WebApp - сообщение должно появиться

## Отличия от старого бота

| Функция | Старый бот (bot.py) | Новый бот (bot_neon.py) |
|---------|---------------------|-------------------------|
| База данных | Локальная память (bot_data) | Neon PostgreSQL |
| Синхронизация | Нет | Да, через API |
| Уведомления | Через callback_data | Через API + уведомления |
| Хранение сообщений | Временно в памяти | Постоянно в БД |
| Чаты | Теряются при перезапуске | Сохраняются |

## Проблемы?

### Бот не отправляет сообщения
- Проверьте что Neon база данных настроена (миграции выполнены)
- Проверьте логи: `journalctl -u anonimka-bot -f`

### Не приходят уведомления
- Проверьте что `TELEGRAM_BOT_TOKEN` в переменных окружения совпадает с токеном в Vercel

### Чаты не загружаются
- Проверьте что API доступен: `curl https://anonimka.kz/api/neon-chats`
- Проверьте что пользователь авторизован в WebApp

## После запуска

Старый `bot.py` можно оставить как резерв или удалить после успешного тестирования нового бота.
