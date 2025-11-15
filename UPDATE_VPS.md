# 🔄 Обновление ботов на VPS

## Шаг 1: Подключитесь к VPS

```bash
ssh root@ВАШ_IP
cd ~/anonimka.online
```

## Шаг 2: Обновите systemd сервис для activity бота

Текущий сервис использует старую версию бота. Нужно изменить на AI версию:

```bash
sudo nano /etc/systemd/system/activity-bot.service
```

Измените строку `ExecStart`:

**Было:**
```ini
ExecStart=/root/anonimka.online/venv/bin/python chat_activity_bot_realistic.py
```

**Должно быть:**
```ini
ExecStart=/root/anonimka.online/venv/bin/python chat_activity_bot_ai.py
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 3: Установите зависимость OpenAI

```bash
source venv/bin/activate
pip install openai
```

## Шаг 4: Создайте файл мониторинга bot_monitor.py

```bash
nano bot_monitor.py
```

Скопируйте содержимое из локального файла `bot_monitor.py` (см. ниже) и вставьте.

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 5: Создайте systemd сервис для мониторинга

```bash
sudo nano /etc/systemd/system/bot-monitor.service
```

Вставьте:
```ini
[Unit]
Description=Bot Health Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/anonimka.online
Environment="PATH=/root/anonimka.online/venv/bin"
ExecStart=/root/anonimka.online/venv/bin/python bot_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 6: Перезапустите все сервисы

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск мониторинга
sudo systemctl enable bot-monitor.service

# Перезапустите activity бота
sudo systemctl restart activity-bot.service

# Запустите мониторинг
sudo systemctl start bot-monitor.service

# Проверьте статус
sudo systemctl status telegram-bot.service
sudo systemctl status activity-bot.service
sudo systemctl status bot-monitor.service
```

## Шаг 7: Проверьте логи

```bash
# Логи основного бота
sudo journalctl -u telegram-bot.service -n 50 -f

# Логи activity бота (AI)
sudo journalctl -u activity-bot.service -n 50 -f

# Логи мониторинга
sudo journalctl -u bot-monitor.service -n 50 -f
```

## 🔔 Мониторинг

Теперь вы будете получать уведомления в Telegram (ID: 884253640) если:
- ✅ Бот упал и автоматически перезапущен
- ❌ Бот упал и не запускается
- ⚠️ Обнаружены критические ошибки в логах

Мониторинг проверяет статус каждые 5 минут.

## 📊 Управление ботами

### Проверка статуса:
```bash
sudo systemctl status telegram-bot.service
sudo systemctl status activity-bot.service
sudo systemctl status bot-monitor.service
```

### Перезапуск:
```bash
sudo systemctl restart telegram-bot.service
sudo systemctl restart activity-bot.service
```

### Остановка:
```bash
sudo systemctl stop telegram-bot.service
sudo systemctl stop activity-bot.service
```

### Просмотр логов в реальном времени:
```bash
sudo journalctl -u telegram-bot.service -f
```

### Последние 100 строк логов:
```bash
sudo journalctl -u telegram-bot.service -n 100
```

## ✅ Готово!

После выполнения всех шагов:
- Боты работают 24/7
- Автозапуск при перезагрузке VPS
- Мониторинг отправляет уведомления в Telegram
- Activity бот использует AI (OpenAI GPT)

---

## 🐛 Решение проблем

### Activity бот не запускается:

```bash
# Проверьте логи
sudo journalctl -u activity-bot.service -n 100

# Убедитесь что OpenAI установлен
source venv/bin/activate
pip list | grep openai

# Проверьте что OPENAI_API_KEY в .env
cat .env | grep OPENAI
```

### Мониторинг не отправляет уведомления:

```bash
# Проверьте что токен бота в .env
cat .env | grep TELEGRAM_BOT_TOKEN

# Проверьте логи мониторинга
sudo journalctl -u bot-monitor.service -n 50
```

### Бот работает но не отвечает:

```bash
# Перезапустите бота
sudo systemctl restart telegram-bot.service

# Проверьте логи на ошибки
sudo journalctl -u telegram-bot.service -n 100 | grep ERROR
```
