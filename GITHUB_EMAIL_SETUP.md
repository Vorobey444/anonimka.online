# 📧 Настройка GitHub Actions для Email

## 🚀 Что это дает
- ✅ Письма отправляются **прямо с GitHub**
- ✅ От вашего технического адреса `wish.online@yandex.kz`
- ✅ Приходят на `aleksey@vorobey444.ru`
- ✅ **Без локального сервера!**

## 🔐 Настройка секретов

### 1. Создание Personal Access Token
1. Идите в GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Создайте новый токен с правами:
   - `repo` (полный доступ к репозиториям)
   - `workflow` (доступ к GitHub Actions)

### 2. Добавление секретов в репозиторий
Перейдите в ваш репозиторий `anonimka.online`:
- Settings → Secrets and variables → Actions → New repository secret

Добавьте два секрета:

**Секрет 1:**
- Name: `YANDEX_APP_PASSWORD`
- Value: `aitmytqacblwvpjc`

**Секрет 2:**
- Name: `GITHUB_TOKEN`
- Value: [ваш Personal Access Token]

## 📝 Обновление JavaScript

В файле `webapp/app.js` нужно заменить токен в строке:
```javascript
'Authorization': 'token ВАШ_GITHUB_TOKEN',
```

## 🔄 Как это работает

1. **Пользователь** заполняет форму на сайте
2. **JavaScript** отправляет API запрос в GitHub
3. **GitHub Actions** получает данные и запускает workflow
4. **Yandex SMTP** отправляет письмо с вашего адреса
5. **Письмо приходит** на aleksey@vorobey444.ru

## ✨ Преимущества

- 🌐 **Работает везде** - не нужен сервер
- 🔒 **Безопасно** - секреты хранятся в GitHub
- 📧 **Профессионально** - письма от вашего домена
- 🚀 **Быстро** - мгновенная отправка
- 💰 **Бесплатно** - GitHub Actions дают 2000 минут/месяц

## 🎯 После настройки

После добавления секретов и токена:
1. Деплоим обновленный код
2. Форма будет работать автоматически
3. Письма будут приходить от `wish.online@yandex.kz`

---

## 🆘 Помощь

Если нужна помощь с настройкой - скажите, и я помогу создать токены и секреты!