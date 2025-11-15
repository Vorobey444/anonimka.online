# 🚀 Руководство по развертыванию ботов на VPS

## Шаг 1: Подключение к VPS серверу

### Получите данные от провайдера VPS:
- IP адрес сервера
- Имя пользователя (обычно `root` или `ubuntu`)
- Пароль или SSH ключ

### Подключение через SSH (из PowerShell на Windows):

```powershell
# Если у вас есть пароль:
ssh root@ВАШ_IP_АДРЕС

# Если используется SSH ключ:
ssh -i путь\к\ключу.pem root@ВАШ_IP_АДРЕС
```

**Альтернатива:** Используйте **PuTTY** для подключения к VPS (скачать: https://www.putty.org/)

---

## Шаг 2: Установка необходимого ПО на VPS

После подключения к серверу выполните следующие команды:

### Обновление системы:
```bash
sudo apt update
sudo apt upgrade -y
```

### Установка Python 3.11:
```bash
sudo apt install python3 python3-pip python3-venv -y
python3 --version
```

### Установка Git:
```bash
sudo apt install git -y
git --version
```

### Установка Node.js (если нужен для вашего проекта):
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
node --version
npm --version
```

---

## Шаг 3: Загрузка кода на VPS

### Вариант А: Через GitHub (рекомендуется)

1. **Загрузите код на GitHub** (если еще не сделали):
   ```powershell
   # На вашем локальном компьютере в папке проекта:
   cd "e:\my project\app chat\anon-board-bot"
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git
   git push -u origin main
   ```

2. **Клонируйте на VPS**:
   ```bash
   cd ~
   git clone https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git
   cd ВАШ_РЕПОЗИТОРИЙ
   ```

### Вариант Б: Через SCP (прямая загрузка файлов)

На вашем локальном компьютере (PowerShell):
```powershell
scp -r "e:\my project\app chat\anon-board-bot" root@ВАШ_IP:/root/bots/
```

### Вариант В: Через FileZilla/WinSCP (графический интерфейс)
- Скачайте **WinSCP**: https://winscp.net/
- Подключитесь к VPS используя IP, логин и пароль
- Перетащите папку `anon-board-bot` на сервер

---

## Шаг 4: Настройка переменных окружения

На VPS создайте файл `.env`:

```bash
cd ~/anon-board-bot  # или путь к вашей папке
nano .env
```

Добавьте ваши токены и настройки:
```env
BOT_TOKEN=ваш_токен_бота
DATABASE_URL=postgresql://user:password@host:5432/database
# Добавьте остальные переменные
```

**Сохраните:** `Ctrl+O`, `Enter`, затем `Ctrl+X`

---

## Шаг 5: Установка зависимостей

### Создание виртуального окружения:
```bash
cd ~/anon-board-bot
python3 -m venv venv
source venv/bin/activate
```

### Установка Python зависимостей:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Установка дополнительных зависимостей для ботов:
```bash
pip install python-telegram-bot python-dotenv psycopg2-binary requests aiohttp
```

---

## Шаг 6: Настройка автозапуска ботов (systemd)

### Создание systemd сервиса для основного бота:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Вставьте следующее содержимое:
```ini
[Unit]
Description=Telegram Anon Board Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/anon-board-bot
Environment="PATH=/root/anon-board-bot/venv/bin"
ExecStart=/root/anon-board-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Сохраните:** `Ctrl+O`, `Enter`, затем `Ctrl+X`

### Создание сервиса для activity бота:

```bash
sudo nano /etc/systemd/system/activity-bot.service
```

```ini
[Unit]
Description=Telegram Activity Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/anon-board-bot
Environment="PATH=/root/anon-board-bot/venv/bin"
ExecStart=/root/anon-board-bot/venv/bin/python chat_activity_bot_realistic.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Активация и запуск сервисов:

```bash
# Перезагрузка конфигурации systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-bot.service
sudo systemctl enable activity-bot.service

# Запуск ботов
sudo systemctl start telegram-bot.service
sudo systemctl start activity-bot.service
```

---

## Шаг 7: Управление ботами

### Проверка статуса:
```bash
sudo systemctl status telegram-bot.service
sudo systemctl status activity-bot.service
```

### Просмотр логов:
```bash
# Логи основного бота
sudo journalctl -u telegram-bot.service -f

# Логи activity бота
sudo journalctl -u activity-bot.service -f

# Последние 100 строк
sudo journalctl -u telegram-bot.service -n 100
```

### Перезапуск ботов:
```bash
sudo systemctl restart telegram-bot.service
sudo systemctl restart activity-bot.service
```

### Остановка ботов:
```bash
sudo systemctl stop telegram-bot.service
sudo systemctl stop activity-bot.service
```

---

## Шаг 8: Настройка файрвола (опционально, но рекомендуется)

```bash
# Установка ufw
sudo apt install ufw -y

# Разрешить SSH
sudo ufw allow ssh
sudo ufw allow 22/tcp

# Если используете веб-интерфейс
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить файрвол
sudo ufw enable
sudo ufw status
```

---

## 🔧 Обновление кода на VPS

Когда вы внесли изменения в код:

### Через Git:
```bash
cd ~/anon-board-bot
git pull origin main
sudo systemctl restart telegram-bot.service
sudo systemctl restart activity-bot.service
```

### Через SCP (с локального компьютера):
```powershell
scp "e:\my project\app chat\anon-board-bot\bot.py" root@ВАШ_IP:/root/anon-board-bot/
```
Затем на VPS:
```bash
sudo systemctl restart telegram-bot.service
```

---

## 📊 Мониторинг ресурсов

### Проверка использования памяти и CPU:
```bash
htop
# или
top
```

### Проверка места на диске:
```bash
df -h
```

### Проверка запущенных процессов:
```bash
ps aux | grep python
```

---

## 🐛 Решение проблем

### Бот не запускается:
1. Проверьте логи: `sudo journalctl -u telegram-bot.service -n 50`
2. Проверьте правильность `.env` файла
3. Убедитесь что все зависимости установлены: `pip list`

### Бот отключается через некоторое время:
- Проверьте настройки `Restart=always` в systemd сервисе
- Проверьте логи на наличие ошибок

### База данных недоступна:
- Проверьте правильность `DATABASE_URL` в `.env`
- Убедитесь что база данных доступна с VPS (проверьте файрвол)

---

## 🔐 Безопасность

1. **Измените SSH порт** (опционально):
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Измените Port 22 на другой (например 2222)
   sudo systemctl restart sshd
   ```

2. **Отключите вход по паролю**, используйте только SSH ключи:
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Установите: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

3. **Регулярно обновляйте систему**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Используйте fail2ban** для защиты от брутфорса:
   ```bash
   sudo apt install fail2ban -y
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

---

## 📝 Полезные команды

```bash
# Проверка всех активных сервисов
systemctl list-units --type=service --state=running

# Освобождение места (очистка кеша apt)
sudo apt clean
sudo apt autoremove

# Просмотр открытых портов
sudo netstat -tulpn

# Тест подключения к базе данных
psql $DATABASE_URL

# Создание бэкапа
tar -czf backup-$(date +%Y%m%d).tar.gz ~/anon-board-bot
```

---

## ✅ Чеклист развертывания

- [ ] VPS арендован и доступен
- [ ] SSH подключение работает
- [ ] Python 3.11+ установлен
- [ ] Git установлен
- [ ] Код загружен на VPS
- [ ] Файл `.env` создан с правильными токенами
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены (`requirements.txt`)
- [ ] Systemd сервисы созданы
- [ ] Боты запущены и работают
- [ ] Логи проверены на наличие ошибок
- [ ] Автозапуск при перезагрузке настроен
- [ ] Файрвол настроен (опционально)
- [ ] Мониторинг настроен

---

## 🆘 Нужна помощь?

Если возникли проблемы, предоставьте:
1. Вывод команды: `sudo journalctl -u telegram-bot.service -n 50`
2. Версию Python: `python3 --version`
3. Установленные пакеты: `pip list`
4. Содержимое systemd сервиса: `cat /etc/systemd/system/telegram-bot.service`
