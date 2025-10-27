# 🌐 Настройка Custom Domain для anonimka.online

## ✅ ГОТОВО:
- Сайт работает: https://vorobey444.github.io/anonimka.online/
- CNAME файл создан в GitHub репозитории
- GitHub Pages настроен и активен

## 📋 НУЖНО НАСТРОИТЬ DNS:

### 1️⃣ Зайдите в панель управления доменом anonimka.online

### 2️⃣ Найдите раздел "DNS" или "DNS Management"

### 3️⃣ Добавьте CNAME запись:
```
Type: CNAME
Name: @ (или anonimka.online, или оставьте пустым)
Value: vorobey444.github.io
TTL: 3600 (или Auto)
```

### 4️⃣ Для поддомена www (опционально):
```
Type: CNAME  
Name: www
Value: vorobey444.github.io
TTL: 3600
```

### 5️⃣ Удалите конфликтующие записи:
- Удалите старые A записи для @
- Удалите старые AAAA записи для @
- Оставьте только CNAME записи

## ⏰ ВРЕМЯ АКТИВАЦИИ:
- DNS пропагация: 5-30 минут (обычно 10 минут)
- GitHub SSL сертификат: автоматически через 24 часа
- Полная активация: до 24 часов

## 🔍 ПРОВЕРКА НАСТРОЙКИ:

### Через командную строку:
```cmd
nslookup anonimka.online
# Должен показать vorobey444.github.io
```

### Через онлайн-сервисы:
- https://dnschecker.org
- Введите: anonimka.online
- Тип: CNAME
- Должен показывать: vorobey444.github.io

## 🌍 ПОПУЛЯРНЫЕ ПРОВАЙДЕРЫ DNS:

### Cloudflare:
1. DNS → Records → Add record
2. Type: CNAME, Name: anonimka.online, Target: vorobey444.github.io

### Namecheap:
1. Domain List → Manage → Advanced DNS
2. Add New Record → CNAME Record
3. Host: @, Value: vorobey444.github.io

### GoDaddy:
1. My Products → DNS → Manage Zones
2. Add → Type: CNAME, Name: @, Data: vorobey444.github.io

### Reg.ru:
1. Управление доменами → DNS-серверы и управление зоной
2. Добавить запись → CNAME, Имя: @, Значение: vorobey444.github.io

## 🔧 ПРОБЛЕМЫ И РЕШЕНИЯ:

### Если показывает 404:
- Подождите до 24 часов для полной активации DNS
- Проверьте CNAME запись в DNS

### Если показывает "Site not found":
- Убедитесь, что CNAME файл существует в gh-pages ветке
- Проверьте настройки GitHub Pages

### Если SSL не работает:
- GitHub автоматически создаст SSL сертификат
- Время создания: до 24 часов после настройки DNS

## 📱 РЕЗУЛЬТАТ:
После настройки DNS будут работать оба адреса:
- ✅ https://anonimka.online (основной)
- ✅ https://vorobey444.github.io/anonimka.online/ (резервный)

## 🎯 СТАТУС ДЕПЛОЯ v3.0:
- ✅ Файлы загружены в gh-pages
- ✅ GitHub Pages активен
- ✅ CNAME файл создан
- ⏳ DNS настройка (вручную)
- ⏳ SSL сертификат (автоматически)

---
© 2025 AnonBoard v3.0 - Полностью развернуто!