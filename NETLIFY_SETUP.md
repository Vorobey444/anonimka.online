# 🚀 Настройка Netlify для отправки писем

## ✨ Что получаем
- 📧 Письма отправляются с **wish.online@yandex.kz**
- 📨 Приходят на **vorobey469@yandex.ru**
- 🌐 Работает **прямо на сайте** без сервера
- ⚡ **Мгновенная отправка** через Serverless

## 🎯 Инструкция по настройке

### 1. Создание аккаунта Netlify
1. Идите на https://netlify.com
2. Регистрируйтесь через GitHub
3. Авторизуйте доступ к репозиторию

### 2. Подключение репозитория
1. New site from Git → GitHub
2. Выберите репозиторий `anonimka.online`
3. **Build settings:**
   - Build command: `npm install`
   - Publish directory: `.`
   - Functions directory: `netlify/functions`

### 3. Настройка Environment Variables
В Netlify Dashboard → Site settings → Environment variables:

- **Key:** `YANDEX_APP_PASSWORD`
- **Value:** `aitmytqacblwvpjc`

### 4. Деплой
- Нажмите "Deploy site"
- Получите URL типа `https://your-site-name.netlify.app`

### 5. Обновление кода
В файле `webapp/app.js` замените:
```javascript
const netlifyUrl = 'https://anonimka-online.netlify.app/.netlify/functions/send-email';
```
на ваш реальный Netlify URL.

## 🔄 Как это работает

```
Пользователь → Форма на сайте → Netlify Function → Yandex SMTP → Письмо
```

## ✅ После настройки

1. **Тестируем форму** на сайте
3. **Проверяем почту** vorobey469@yandex.ru
3. **Письма приходят** с wish.online@yandex.kz

## 🆘 Альтернатива

Если Netlify не подходит, можно использовать:
- **Vercel** (аналогично Netlify)
- **Railway** (простой деплой)
- **Heroku** (классическое решение)

Все файлы уже готовы! Просто загружайте на любую из этих платформ! 🎉