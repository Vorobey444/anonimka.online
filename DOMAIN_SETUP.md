# 🌐 Настройка домена anonimka.online для Telegram Mini App

## 📋 План развертывания

### Шаг 1: Создание GitHub репозитория
1. Идите на https://github.com
2. Нажмите "New repository" (зелёная кнопка)
3. Название: `anonimka-miniapp` (или любое другое)
4. Сделайте репозиторий **Public** (обязательно для GitHub Pages)
5. Нажмите "Create repository"

### Шаг 2: Загрузка файлов
1. В созданном репозитории нажмите "uploading an existing file"
2. Перетащите файлы из папки `webapp/`:
   - `index.html`
   - `style.css` 
   - `app.js`
3. В поле "Commit changes" напишите: "Initial Mini App files"
4. Нажмите "Commit changes"

### Шаг 3: Включение GitHub Pages
1. В репозитории перейдите в `Settings` (вкладка справа)
2. Прокрутите до раздела `Pages` (в левом меню)
3. В `Source` выберите `Deploy from a branch`
4. В `Branch` выберите `main` и папку `/ (root)`
5. Нажмите `Save`

Через 2-3 минуты ваш сайт будет доступен по адресу:
`https://your-username.github.io/anonimka-miniapp/`

### Шаг 4: Настройка домена anonimka.online
1. В разделе `Pages` найдите поле `Custom domain`
2. Введите: `anonimka.online`
3. Нажмите `Save`
4. Поставьте галочку `Enforce HTTPS` (обязательно!)

### Шаг 5: Настройка DNS у регистратора домена
В панели управления доменом `anonimka.online` создайте записи:

```
Тип    Имя    Значение
CNAME  www    your-username.github.io
A      @      185.199.108.153
A      @      185.199.109.153  
A      @      185.199.110.153
A      @      185.199.111.153
```

*(Замените `your-username` на ваш реальный GitHub username)*

### Шаг 6: Обновление бота
После настройки домена обновите `webapp_bot.py`:

```python
WEBAPP_URL = "https://anonimka.online/"
```

## 🚀 Быстрый способ (альтернатива)

Если GitHub Pages кажется сложным, можете использовать:

### Netlify (проще):
1. Идите на https://netlify.com
2. Перетащите папку `webapp/` на сайт
3. В настройках добавьте домен `anonimka.online`
4. Настройте DNS как покажет Netlify

### Vercel (ещё проще):
1. Идите на https://vercel.com  
2. Импортируйте из GitHub или загрузите файлы
3. Добавьте домен `anonimka.online`
4. Следуйте инструкциям по DNS

## ⚡ Результат
После настройки пользователи смогут:
1. Найти вашего бота в Telegram
2. Нажать `/start`
3. Нажать "🚀 Открыть приложение" 
4. Увидеть красивый киберпанк интерфейс на `anonimka.online`

## 🔧 Проверка работы
1. Откройте `https://anonimka.online` в браузере
2. Должен загрузиться киберпанк интерфейс
3. Если работает - обновите URL в боте
4. Запустите `start_webapp_bot.bat`

---

💡 **Подсказка**: Начните с GitHub Pages - это бесплатно и надёжно. Если возникнут сложности, помогу настроить Netlify или Vercel.