# 🚀 Инструкция по применению изменений: Stars + Реферальная система

## ✅ Что было сделано

### 1. API Endpoints (Next.js)
- ✅ `/api/premium/activate` - активация PRO через Stars (бот вызывает после оплаты)
- ✅ `/api/premium/calculate` - расчёт цены для slider UI (1-12 месяцев)

### 2. База данных
- ✅ `021_premium_transactions.sql` - миграция для хранения истории покупок

### 3. Бот (bot_neon.py)
- ✅ Добавлена команда `/referral` с реферальной ссылкой и статистикой
- ✅ Зарегистрирован handler для команды

### 4. WebApp (Frontend)
- ✅ Обновлён текст: "когда он создаст анкету" вместо "авторизуется"
- ✅ Добавлено предупреждение об одноразовой акции

### 5. Документация
- ✅ `REFERRAL_STARS_INTEGRATION.md` - полный анализ существующей системы + план интеграции
- ✅ Настоящий файл с инструкциями по деплою

---

## 📋 Чеклист применения изменений

### Шаг 1: Применить миграцию к базе данных (NEON)

**Где**: Neon Console → SQL Editor → Execute SQL

**Файл**: `anonimka-nextjs/migrations/021_premium_transactions.sql`

**Команды**:
```sql
BEGIN;

CREATE TABLE IF NOT EXISTS premium_transactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER,
  telegram_id BIGINT NOT NULL,
  months INTEGER NOT NULL,
  amount_stars INTEGER NOT NULL,
  transaction_id TEXT,
  payment_method TEXT DEFAULT 'stars',
  status TEXT DEFAULT 'completed',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_premium_trans_user ON premium_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_trans_telegram_id ON premium_transactions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_premium_trans_created ON premium_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_premium_trans_transaction_id ON premium_transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_premium_trans_status ON premium_transactions(status);

COMMIT;
```

**Проверка**:
```sql
SELECT * FROM premium_transactions LIMIT 1;
```

---

### Шаг 2: Деплой Next.js изменений (Vercel)

**Файлы для коммита**:
1. `src/app/api/premium/activate/route.ts` (НОВЫЙ)
2. `src/app/api/premium/calculate/route.ts` (НОВЫЙ)
3. `public/webapp/index.html` (ИЗМЕНЁН)
4. `migrations/021_premium_transactions.sql` (НОВЫЙ)

**Команды**:
```bash
cd "e:\my project\app chat\anonimka-nextjs"

# Git add
git add src/app/api/premium/activate/route.ts
git add src/app/api/premium/calculate/route.ts
git add public/webapp/index.html
git add migrations/021_premium_transactions.sql

# Git commit
git commit -m "Add Stars payment integration: /api/premium/activate + /calculate"

# Git push (автоматический деплой на Vercel)
git push origin main
```

**Проверка после деплоя**:
```bash
# Проверить endpoint activate
curl -X POST https://anonimka.kz/api/premium/activate \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456, "months": 1, "transaction_id": "test_123", "amount": 50}'

# Ожидаемый ответ:
# {"success":true,"premium_until":"2025-02-XX...","months":1,"amount_stars":50,"stacked":false}

# Проверить endpoint calculate
curl https://anonimka.kz/api/premium/calculate?months=5

# Ожидаемый ответ:
# {"months":5,"stars":187,"currency":"XTR","discount":26,"rub_equivalent":374,"kzt_equivalent":1870}
```

---

### Шаг 3: Обновить бота на VPS

**SSH подключение**:
```bash
ssh root@46.17.40.243
cd /root/anonimka.online
```

**Git pull изменений**:
```bash
git pull origin main
```

**Проверить изменения**:
```bash
# Проверить что команда /referral добавлена
grep -A 5 "referral_command" bot_neon.py

# Проверить что handler зарегистрирован
grep "referral" bot_neon.py | grep add_handler
```

**Перезапустить бота**:
```bash
# Найти процесс
ps aux | grep bot_neon.py

# Убить старый процесс
kill <PID>

# Запустить новый
nohup python3 bot_neon.py > bot.log 2>&1 &

# Проверить логи
tail -f bot.log
```

**Альтернатива (если используется systemd)**:
```bash
sudo systemctl restart anonimka-bot
sudo systemctl status anonimka-bot
journalctl -u anonimka-bot -f
```

---

## 🧪 Тестирование

### Тест 1: Реферальная программа

1. **Создать реферальную ссылку**:
   - Отправить боту `/referral`
   - Проверить что вернулась ссылка `https://t.me/anonimka_kz_bot?startapp=ref_<YOUR_TG_ID>`
   - Проверить статистику (total=0, rewarded=0, pending=0)

2. **Пригласить друга**:
   - Создать тестовый Telegram аккаунт
   - Перейти по реферальной ссылке
   - Открыть WebApp
   - Создать анкету (POST /api/ads)

3. **Проверить награду**:
   - После создания анкеты должен вызваться `PUT /api/referrals`
   - Проверить в логах бота: `[REFERRAL REWARD] ✅ PRO выдан впервые до: ...`
   - Проверить в базе:
   ```sql
   SELECT is_premium, premium_until FROM users WHERE id = <YOUR_TG_ID>;
   -- Должно быть: is_premium = true, premium_until = NOW() + 30 days
   ```

4. **Проверить одноразовость**:
   - Пригласить второго друга
   - Второй друг создаёт анкету
   - Награда НЕ должна выдаться (т.к. premium_until != NULL)
   - В логах: `[REFERRAL REWARD] ⚠️ Реферер уже получал PRO — акция действует один раз`

### Тест 2: Покупка PRO через Stars

1. **Купить 1 месяц**:
   - Отправить боту `/premium`
   - Нажать "🔥 1 месяц - 50 Stars"
   - Оплатить через Stars (ТЕСТОВЫЙ РЕЖИМ: используйте test bot token)
   - После оплаты проверить сообщение: "🎉 Поздравляем! PRO активирована на 1 мес."

2. **Проверить активацию**:
   - Проверить в базе:
   ```sql
   SELECT is_premium, premium_until FROM users WHERE id = <YOUR_TG_ID>;
   ```
   - Проверить транзакцию:
   ```sql
   SELECT * FROM premium_transactions WHERE telegram_id = <YOUR_TG_ID> ORDER BY created_at DESC LIMIT 1;
   ```

3. **Тест стекирования**:
   - Купить ещё 1 месяц
   - Проверить что premium_until увеличился на 30 дней (не сбросился)

### Тест 3: Расчёт цены (API)

```bash
# Тест для 1 месяца
curl https://anonimka.kz/api/premium/calculate?months=1
# Ожидается: {"months":1,"stars":50,"discount":0}

# Тест для 3 месяцев
curl https://anonimka.kz/api/premium/calculate?months=3
# Ожидается: {"months":3,"stars":130,"discount":17}

# Тест для 5 месяцев (интерполяция)
curl https://anonimka.kz/api/premium/calculate?months=5
# Ожидается: {"months":5,"stars":187,"discount":26}

# Тест для 12 месяцев
curl https://anonimka.kz/api/premium/calculate?months=12
# Ожидается: {"months":12,"stars":360,"discount":41}
```

---

## 🔍 Проверка логов

### Логи API (Vercel)

1. Зайти на [vercel.com](https://vercel.com)
2. Выбрать проект `anonimka-nextjs`
3. Перейти в **Logs**
4. Искать:
   - `[PREMIUM ACTIVATE]` - логи активации PRO
   - `[REFERRAL REWARD]` - логи выдачи реферальной награды

### Логи бота (VPS)

```bash
ssh root@46.17.40.243
cd /root/anonimka.online

# Читать логи в реальном времени
tail -f bot.log

# Искать ошибки
grep "❌" bot.log | tail -20

# Искать успешные платежи
grep "💰 Успешный платеж" bot.log

# Искать реферальные команды
grep "🔗 /referral" bot.log
```

### Логи базы данных (Neon)

```sql
-- Проверить последние транзакции PRO
SELECT 
  telegram_id,
  months,
  amount_stars,
  status,
  created_at
FROM premium_transactions
ORDER BY created_at DESC
LIMIT 10;

-- Проверить кто получил PRO через реферальную программу
SELECT 
  r.id,
  r.referrer_id,
  r.referred_id,
  r.reward_given,
  r.reward_given_at,
  u.is_premium,
  u.premium_until
FROM referrals r
LEFT JOIN users u ON u.id = r.referrer_id
WHERE r.reward_given = TRUE
ORDER BY r.reward_given_at DESC
LIMIT 10;

-- Проверить пользователей с активным PRO
SELECT 
  id,
  is_premium,
  premium_until,
  created_at
FROM users
WHERE is_premium = TRUE AND premium_until > NOW()
ORDER BY premium_until DESC
LIMIT 20;
```

---

## ⚠️ Возможные проблемы и решения

### Проблема 1: API endpoint 404

**Симптомы**: Бот логирует `❌ API /api/premium/activate вернул статус 404`

**Решение**:
1. Проверить что файл `src/app/api/premium/activate/route.ts` существует
2. Проверить деплой на Vercel: `git push origin main`
3. Проверить URL: должен быть `https://anonimka.kz/api/premium/activate` (без `/src/app`)

### Проблема 2: База данных - таблица не существует

**Симптомы**: Ошибка `relation "premium_transactions" does not exist`

**Решение**:
1. Зайти в Neon Console
2. Выполнить миграцию `021_premium_transactions.sql`
3. Проверить: `SELECT * FROM premium_transactions LIMIT 1;`

### Проблема 3: Реферальная награда не выдаётся

**Симптомы**: Друг создал анкету, но награда не пришла

**Диагностика**:
```sql
-- Проверить запись реферала
SELECT * FROM referrals WHERE referred_id = <FRIEND_TG_ID>;

-- Проверить флаг reward_given
-- Если reward_given = FALSE → награда не выдана
-- Если reward_given = TRUE → награда уже была выдана ранее

-- Проверить premium_until реферера
SELECT id, premium_until FROM users WHERE id = <REFERRER_TG_ID>;
-- Если premium_until != NULL → реферер УЖЕ получал PRO → акция не работает
```

**Решение**:
- Если `reward_given = FALSE` и `premium_until = NULL` → вручную вызвать API:
```bash
curl -X PUT https://anonimka.kz/api/referrals \
  -H "Content-Type: application/json" \
  -d '{"new_user_token":"<FRIEND_TOKEN>"}'
```

### Проблема 4: Бот не отвечает на /referral

**Симптомы**: Команда `/referral` не работает

**Диагностика**:
```bash
ssh root@46.17.40.243
cd /root/anonimka.online

# Проверить что команда добавлена
grep "referral_command" bot_neon.py

# Проверить что handler зарегистрирован
grep "CommandHandler.*referral" bot_neon.py
```

**Решение**:
1. Выполнить `git pull origin main`
2. Перезапустить бота: `kill <PID>` → `nohup python3 bot_neon.py &`
3. Проверить логи: `tail -f bot.log`

---

## 📊 Мониторинг и статистика

### Команды для админа

```sql
-- Сколько всего PRO активаций через Stars
SELECT COUNT(*) as total_sales FROM premium_transactions WHERE status = 'completed';

-- Сколько заработано Stars
SELECT SUM(amount_stars) as total_earned FROM premium_transactions WHERE status = 'completed';

-- Самые популярные тарифы
SELECT months, COUNT(*) as count FROM premium_transactions GROUP BY months ORDER BY count DESC;

-- Сколько рефералов привели друзей
SELECT COUNT(*) as successful_referrals FROM referrals WHERE reward_given = TRUE;

-- Топ рефереров
SELECT 
  referrer_id,
  COUNT(*) as friends_invited
FROM referrals
WHERE reward_given = TRUE
GROUP BY referrer_id
ORDER BY friends_invited DESC
LIMIT 10;

-- Активные PRO пользователи
SELECT COUNT(*) FROM users WHERE is_premium = TRUE AND premium_until > NOW();
```

---

## ✅ Финальная проверка

- [ ] Миграция 021 применена к базе
- [ ] API `/api/premium/activate` возвращает 200 при тестовом запросе
- [ ] API `/api/premium/calculate` возвращает корректные цены
- [ ] Next.js деплой завершён (Vercel показывает зелёный статус)
- [ ] Бот перезапущен на VPS
- [ ] Команда `/referral` работает и возвращает ссылку
- [ ] Команда `/premium` работает и показывает тарифы
- [ ] Тестовая покупка через Stars прошла успешно
- [ ] Тестовый реферал получил награду
- [ ] WebApp показывает обновлённый текст "создаст анкету"

---

## 🎉 Готово!

Система Stars + Реферальная программа полностью интегрирована и готова к работе.

**Что дальше?**
1. Slider UI для выбора месяцев (опционально)
2. Trial 7 часов (уже реализован в `/api/premium`)
3. Админ-панель для статистики продаж
4. Автоматическое продление PRO (рекуррентные платежи)

**Документация**:
- `REFERRAL_STARS_INTEGRATION.md` - полный анализ системы
- `AFFILIATE_PROGRAM_GUIDE.md` - гайд по партнёрской программе
- `PREMIUM_SYSTEM_SPEC.md` - спецификация PRO системы

**Поддержка**: aleksey@vorobey444.ru
