# 🔍 Анализ существующей реферальной системы + Stars интеграция

## ✅ Что УЖЕ РЕАЛИЗОВАНО

### 1. База данных (ЕСТЬ)

**Таблица `referrals`** (миграция 006):
```sql
referrals:
  - id
  - referrer_id (numeric tg_id)
  - referred_id (numeric tg_id)
  - referrer_token (TEXT для веб-юзеров)
  - referred_token (TEXT для веб-юзеров)
  - reward_given (BOOLEAN)
  - reward_given_at (TIMESTAMP)
  - created_at
```

**Таблица `premium_tokens`** (миграция 006):
```sql
premium_tokens:
  - user_token (PRIMARY KEY)
  - is_premium (BOOLEAN)
  - premium_until (TIMESTAMPTZ)
  - updated_at
```

**Таблица `users`** (уже существует):
```sql
users:
  - id (numeric tg_id)
  - is_premium
  - premium_until
  - trial7h_used (для Trial 7 часов)
  - updated_at
```

### 2. API Endpoints (ЕСТЬ)

**`/api/referrals`** (файл: `anonimka-nextjs/src/app/api/referrals/route.ts`):

#### POST - Регистрация перехода по реферальной ссылке
```typescript
// Входные данные:
{
  referrer_token: string,  // токен пригласителя
  new_user_token: string   // токен нового пользователя
}

// Что делает:
1. Проверяет, не сам ли себя приглашает
2. Создает запись в referrals с NULL в referred_id
3. referred_id заполнится позже при создании анкеты
```

#### PUT - Выдача награды за реферала
```typescript
// Входные данные:
{
  new_user_token: string  // токен пользователя, создавшего анкету
}

// Что делает:
1. Находит запись реферала по referred_token ИЛИ referred_id
2. Обновляет referred_id если был NULL
3. Проверяет reward_given (защита от дублей)
4. АКЦИЯ: PRO выдаётся ОДИН РАЗ только новым пользователям
5. Проверяет premium_until: если != NULL → реферер УЖЕ получал PRO → отказ
6. Выдаёт 30 дней PRO через premium_tokens (веб) ИЛИ users (Telegram)
7. Устанавливает reward_given = TRUE
```

**ВАЖНО**: Награда выдаётся ТОЛЬКО РАЗ. Если у реферера `premium_until != NULL` → акция НЕ работает.

#### GET - Статистика рефералов
```typescript
// Параметры: ?userId=<token или numeric>
// Возвращает: { total, rewarded, pending, referrals: [...] }
```

**`/api/premium`** (файл: `anonimka-nextjs/src/app/api/premium/route.ts`):

#### POST action: 'get-user-status'
```typescript
// Входные данные:
{ action: 'get-user-status', params: { userId } }

// Возвращает:
{
  isPremium: boolean,
  premiumUntil: string | null,
  trial7h_used: boolean,
  limits: { photos, ads, pin }
}

// ПРИОРИТЕТ: Сначала проверяет premium_tokens, потом users
```

#### POST action: 'toggle-premium'
```typescript
// Активирует PRO (для тестирования или Trial 7h)
{ action: 'toggle-premium', params: { userId, trial7h: true/false } }

// Trial 7h: одноразовый, устанавливает trial7h_used = true
```

### 3. Фронтенд (ЕСТЬ)

**WebApp** (`anonimka-nextjs/public/webapp/`):

#### Реферальная ссылка
- Формат: `https://t.me/anonimka_kz_bot?startapp=ref_<user_token>`
- Модальное окно "Пригласи друга" с кнопками копирования и шаринга
- Функция `showReferralModal()` генерирует ссылку

#### Обработка реферальной ссылки
```javascript
// app.js функция handleReferralLink():
1. Проверяет start_param из Telegram WebApp
2. Если формат ref_<token> → сохраняет в localStorage.pending_referral
3. Редиректит в Telegram если переход из веба

// app.js функция finalizePendingReferral():
1. Читает localStorage.pending_referral
2. Отправляет POST /api/referrals с { referrer_token, new_user_token }
3. Устанавливает referral_processed = 'true'
```

#### Выдача награды
```javascript
// Вызывается в createAd() после создания анкеты:
const reward = await fetch('/api/referrals', {
  method: 'PUT',
  body: JSON.stringify({ new_user_token })
});
```

**УСЛОВИЕ ВЫДАЧИ**: Награда вызывается **КОГДА ПОЛЬЗОВАТЕЛЬ СОЗДАЛ АНКЕТУ** (POST /api/ads).

### 4. Бот (ЕСТЬ частично)

**bot_neon.py** (строки 104-114):
```python
# Обработка реферальных ссылок
if start_param.startswith('ref_'):
    referrer_token = start_param.replace('ref_', '')
    webapp_url = f"{API_BASE_URL}/webapp?ref={referrer_token}"
    
    # Открывает WebApp с параметром ?ref=
```

---

## ❌ Что ОТСУТСТВУЕТ и нужно ДОБАВИТЬ

### 1. API Endpoint для активации PRO через Stars (НЕТ)

**`/api/premium/activate`** - вызывается ботом после оплаты Stars

```typescript
// POST /api/premium/activate
{
  telegram_id: number,     // tg_id покупателя
  months: number,          // 1, 3, 6, 12
  transaction_id: string,  // ID транзакции Stars
  amount: number          // Сумма в Stars (50, 130, 215, 360)
}

// Что должно делать:
1. Проверить, существует ли users.id = telegram_id
2. Если нет → создать запись с id = telegram_id
3. Рассчитать новый premium_until:
   - Если is_premium = false ИЛИ premium_until истёк:
       premium_until = NOW() + months
   - Если is_premium = true И premium_until > NOW():
       premium_until = GREATEST(premium_until, NOW()) + months (стекирование)
4. UPDATE users SET is_premium = true, premium_until = <новая дата>
5. INSERT INTO premium_transactions (для статистики)
6. Вернуть { success: true, premium_until }
```

**ВАЖНО**: Stars платежи СТЕКИРУЮТСЯ (в отличие от реферальной акции).

### 2. Таблица premium_transactions (НЕТ)

Для статистики покупок через Stars:

```sql
CREATE TABLE IF NOT EXISTS premium_transactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER,  -- users.id (numeric tg_id)
  telegram_id BIGINT NOT NULL,
  
  -- Детали покупки
  months INTEGER NOT NULL,
  amount_stars INTEGER NOT NULL,
  transaction_id TEXT,
  payment_method TEXT DEFAULT 'stars',
  
  -- Статус
  status TEXT DEFAULT 'completed',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_premium_trans_user ON premium_transactions(user_id);
CREATE INDEX idx_premium_trans_telegram_id ON premium_transactions(telegram_id);
CREATE INDEX idx_premium_trans_created ON premium_transactions(created_at);
```

### 3. Slider UI для покупки PRO (НЕТ)

**Компонент React/HTML** для WebApp:

```jsx
// Ползунок выбора месяцев (1-12)
<input type="range" min="1" max="12" value={months} />

// Цены:
const prices = {
  1: 50,   // -0%
  3: 130,  // -17% (156 → 130)
  6: 215,  // -30% (300 → 215)
  12: 360  // -41% (600 → 360)
};

// Формула для промежуточных месяцев:
function calculatePrice(months) {
  if (months <= 3) return 50 * months - Math.floor(months * 8.67);
  if (months <= 6) return 50 * months - Math.floor(months * 14.17);
  return 50 * months - Math.floor(months * 20);
}

// Кнопка "Купить" → Вызывает Telegram.WebApp.openInvoice() с Stars
```

**API для расчёта цены**: `/api/premium/calculate?months=5`

```typescript
// GET /api/premium/calculate?months=5
// Возвращает: { months: 5, stars: 210, currency: "XTR", discount: 28 }
```

### 4. Обновление условий реферальной программы

**Текущее условие**: "когда он авторизуется"  
**Новое условие**: "когда он создаст АНКЕТУ"

**ГДЕ МЕНЯТЬ**:
- `anonimka-nextjs/public/webapp/index.html` строка 1377:
  ```html
  <!-- БЫЛО: -->
  Пригласи друга через Telegram, и когда он авторизуется
  
  <!-- СТАЛО: -->
  Пригласи друга через Telegram, и когда он создаст анкету
  ```

- Модальное окно "Пригласи друга" → обновить текст

### 5. Команда /referral в боте (НЕТ)

```python
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реферальная программа - получить ссылку"""
    user = update.effective_user
    
    # Получаем статистику из API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/referrals?userId={user.id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    total = data.get('total', 0)
                    rewarded = data.get('rewarded', 0)
                    
                    # Генерируем реферальную ссылку
                    # ВОПРОС: Telegram-пользователи не имеют user_token
                    # Решение: использовать numeric ID как ref_<tg_id>
                    ref_link = f"https://t.me/{context.bot.username}?startapp=ref_{user.id}"
                    
                    text = (
                        f"🎁 <b>Пригласи друга - получи 30 дней PRO!</b>\n\n"
                        f"<b>Твоя реферальная ссылка:</b>\n"
                        f"<code>{ref_link}</code>\n\n"
                        f"<b>Как это работает:</b>\n"
                        f"1️⃣ Отправь ссылку другу\n"
                        f"2️⃣ Друг переходит и <b>создаёт анкету</b>\n"
                        f"3️⃣ Ты получаешь 30 дней PRO! 🎉\n\n"
                        f"👥 Приглашено друзей: <b>{total}</b>\n"
                        f"✅ Получено PRO: <b>{rewarded}</b>\n\n"
                        f"⚠️ <i>Акция действует ОДИН РАЗ для новых пользователей</i>"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("📤 Поделиться ссылкой", 
                                            url=f"https://t.me/share/url?url={ref_link}&text=Попробуй Anonimka - анонимные знакомства! Получим PRO на месяц 🎁")]
                    ]
                    
                    await update.message.reply_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
    except Exception as e:
        logger.error(f"❌ Ошибка /referral: {e}")
```

**ПРОБЛЕМА**: Telegram-пользователи НЕ имеют `user_token` (только веб-юзеры).

**РЕШЕНИЕ**: 
1. В боте использовать `ref_{telegram_id}` вместо `ref_{user_token}`
2. API /api/referrals должен поддерживать numeric ID как referrer_token
3. Уже реализовано в коде: `isDigits(referrer_token)` → преобразует в refTgId

---

## 🎯 План интеграции Stars с реферальной системой

### Этап 1: Создать API endpoint /api/premium/activate

**Файл**: `anonimka-nextjs/src/app/api/premium/activate/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { sql } from '@vercel/postgres';

export async function POST(request: NextRequest) {
  try {
    const { telegram_id, months, transaction_id, amount } = await request.json();
    
    // Валидация
    if (!telegram_id || !months || !transaction_id || !amount) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }
    
    // Проверяем пользователя
    const user = await sql`SELECT id, is_premium, premium_until FROM users WHERE id = ${telegram_id}`;
    
    let newPremiumUntil: Date;
    const now = new Date();
    
    if (user.rows.length === 0) {
      // Создаём нового пользователя
      newPremiumUntil = new Date(now);
      newPremiumUntil.setMonth(newPremiumUntil.getMonth() + months);
      
      await sql`
        INSERT INTO users (id, is_premium, premium_until)
        VALUES (${telegram_id}, true, ${newPremiumUntil.toISOString()})
      `;
    } else {
      // Обновляем существующего
      const userData = user.rows[0];
      const currentUntil = userData.premium_until ? new Date(userData.premium_until) : null;
      
      // Стекирование: если PRO активен, добавляем месяцы к текущему сроку
      if (userData.is_premium && currentUntil && currentUntil > now) {
        newPremiumUntil = new Date(currentUntil);
        newPremiumUntil.setMonth(newPremiumUntil.getMonth() + months);
      } else {
        // PRO истёк или не был активен
        newPremiumUntil = new Date(now);
        newPremiumUntil.setMonth(newPremiumUntil.getMonth() + months);
      }
      
      await sql`
        UPDATE users
        SET is_premium = true,
            premium_until = ${newPremiumUntil.toISOString()},
            updated_at = NOW()
        WHERE id = ${telegram_id}
      `;
    }
    
    // Записываем транзакцию
    await sql`
      INSERT INTO premium_transactions (user_id, telegram_id, months, amount_stars, transaction_id)
      VALUES (${telegram_id}, ${telegram_id}, ${months}, ${amount}, ${transaction_id})
    `;
    
    console.log(`✅ PRO активирован: tg_id=${telegram_id}, +${months} мес, до ${newPremiumUntil.toISOString()}`);
    
    return NextResponse.json({
      success: true,
      premium_until: newPremiumUntil.toISOString(),
      months,
      stacked: user.rows.length > 0 && user.rows[0].is_premium
    });
    
  } catch (error: any) {
    console.error('[PREMIUM ACTIVATE] Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
```

### Этап 2: Создать миграцию для premium_transactions

**Файл**: `anonimka-nextjs/migrations/021_premium_transactions.sql`

```sql
-- Migration 021: Premium Transactions для покупок через Stars
BEGIN;

CREATE TABLE IF NOT EXISTS premium_transactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER,
  telegram_id BIGINT NOT NULL,
  
  -- Детали покупки
  months INTEGER NOT NULL,
  amount_stars INTEGER NOT NULL,
  transaction_id TEXT,
  payment_method TEXT DEFAULT 'stars',
  
  -- Статус
  status TEXT DEFAULT 'completed',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_premium_trans_user ON premium_transactions(user_id);
CREATE INDEX idx_premium_trans_telegram_id ON premium_transactions(telegram_id);
CREATE INDEX idx_premium_trans_created ON premium_transactions(created_at DESC);

COMMIT;
```

### Этап 3: Обновить бота (bot_neon.py)

Код уже добавлен в bot_neon.py (строки 1130-1200):
- ✅ premium_command() - показывает тарифы
- ✅ buy_premium_callback() - создаёт Stars invoice
- ✅ successful_payment_callback() - вызывает POST /api/premium/activate

**ПРОВЕРИТЬ**:
1. API_BASE_URL правильно настроен
2. Цены актуальны (50/130/215/360 Stars)
3. Хендлеры зарегистрированы в main()

### Этап 4: Добавить /referral команду в бота

```python
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/referrals?userId={user.id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    total = data.get('total', 0)
                    rewarded = data.get('rewarded', 0)
                    
                    ref_link = f"https://t.me/{context.bot.username}?startapp=ref_{user.id}"
                    
                    text = (
                        f"🎁 <b>Пригласи друга - получи 30 дней PRO!</b>\n\n"
                        f"<b>Твоя реферальная ссылка:</b>\n"
                        f"<code>{ref_link}</code>\n\n"
                        f"<b>Как это работает:</b>\n"
                        f"1️⃣ Отправь ссылку другу\n"
                        f"2️⃣ Друг переходит и <b>создаёт анкету</b>\n"
                        f"3️⃣ Ты получаешь 30 дней PRO! 🎉\n\n"
                        f"👥 Приглашено: <b>{total}</b> друзей\n"
                        f"✅ Награда получена: <b>{rewarded}</b> раз\n\n"
                        f"⚠️ <i>Акция действует ОДИН РАЗ для новых пользователей</i>"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("📤 Поделиться ссылкой", 
                                            url=f"https://t.me/share/url?url={ref_link}&text=Попробуй Anonimka - анонимные знакомства!")]
                    ]
                    
                    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    except Exception as e:
        logger.error(f"❌ /referral error: {e}")

# В main() добавить:
application.add_handler(CommandHandler("referral", referral_command))
```

### Этап 5: Обновить тексты в WebApp

**Файл**: `anonimka-nextjs/public/webapp/index.html` строка 1377

```html
<!-- БЫЛО: -->
<p>Пригласи друга через Telegram, и когда он авторизуется - ты получишь...</p>

<!-- СТАЛО: -->
<p>Пригласи друга через Telegram, и когда он <strong style="color: var(--neon-pink);">создаст анкету</strong> - ты получишь...</p>
```

### Этап 6: Slider UI для покупки (опционально)

**Компонент для WebApp**:

```html
<!-- В модальное окно PRO -->
<div id="premiumSliderModal" class="modal">
  <div class="modal-content">
    <h2>💎 Купить PRO подписку</h2>
    
    <div class="slider-container">
      <label>Выбери срок подписки:</label>
      <input type="range" id="monthsSlider" min="1" max="12" value="1" 
             oninput="updatePremiumPrice()">
      <div class="slider-value">
        <span id="monthsDisplay">1</span> месяц(ев)
      </div>
    </div>
    
    <div class="price-display">
      <div class="price">
        <span id="starsAmount">50</span> Stars
        <span class="currency">(~<span id="rubAmount">99</span>₽)</span>
      </div>
      <div class="discount" id="discountBadge" style="display: none;">
        -<span id="discountPercent">0</span>% скидка!
      </div>
    </div>
    
    <button class="neon-button primary" onclick="buyPremiumStars()">
      ⭐ Купить через Stars
    </button>
  </div>
</div>

<script>
function updatePremiumPrice() {
  const months = parseInt(document.getElementById('monthsSlider').value);
  document.getElementById('monthsDisplay').textContent = months;
  
  // Цены (примерные для промежуточных месяцев)
  const prices = {
    1: { stars: 50, discount: 0 },
    2: { stars: 92, discount: 8 },
    3: { stars: 130, discount: 17 },
    4: { stars: 168, discount: 16 },
    5: { stars: 206, discount: 18 },
    6: { stars: 215, discount: 30 },
    7: { stars: 245, discount: 30 },
    8: { stars: 275, discount: 31 },
    9: { stars: 290, discount: 36 },
    10: { stars: 310, discount: 38 },
    11: { stars: 335, discount: 39 },
    12: { stars: 360, discount: 41 }
  };
  
  const price = prices[months];
  document.getElementById('starsAmount').textContent = price.stars;
  document.getElementById('rubAmount').textContent = Math.round(price.stars * 2);
  
  const discountBadge = document.getElementById('discountBadge');
  const discountPercent = document.getElementById('discountPercent');
  
  if (price.discount > 0) {
    discountPercent.textContent = price.discount;
    discountBadge.style.display = 'block';
  } else {
    discountBadge.style.display = 'none';
  }
}

async function buyPremiumStars() {
  const months = parseInt(document.getElementById('monthsSlider').value);
  const stars = parseInt(document.getElementById('starsAmount').textContent);
  
  // Создать invoice через бота
  // Telegram.WebApp.openInvoice() - НЕ работает для Stars
  // Нужно вызвать команду в боте: /premium → кнопка с callback_data
  
  alert(`Для покупки ${months} месяцев за ${stars} Stars откройте бота @anonimka_kz_bot и нажмите /premium`);
}
</script>
```

**API для расчёта**: `/api/premium/calculate`

```typescript
// GET /api/premium/calculate?months=5
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const months = parseInt(searchParams.get('months') || '1');
  
  const prices: Record<number, { stars: number; discount: number }> = {
    1: { stars: 50, discount: 0 },
    3: { stars: 130, discount: 17 },
    6: { stars: 215, discount: 30 },
    12: { stars: 360, discount: 41 }
  };
  
  // Линейная интерполяция для промежуточных месяцев
  let stars = 50 * months;
  let discount = 0;
  
  if (months <= 3) {
    discount = Math.floor(months * 5.67); // до -17%
  } else if (months <= 6) {
    discount = Math.floor(17 + (months - 3) * 4.33); // -17% до -30%
  } else {
    discount = Math.floor(30 + (months - 6) * 1.83); // -30% до -41%
  }
  
  stars = Math.floor(stars * (100 - discount) / 100);
  
  return NextResponse.json({
    months,
    stars,
    currency: 'XTR',
    discount,
    rub_equivalent: stars * 2
  });
}
```

---

## 📋 Чеклист внедрения

### Backend (Next.js API)
- [ ] Создать `/api/premium/activate/route.ts`
- [ ] Создать миграцию `021_premium_transactions.sql`
- [ ] Применить миграцию к базе Neon
- [ ] Создать `/api/premium/calculate/route.ts` для slider
- [ ] Протестировать endpoint через Postman

### Bot (bot_neon.py)
- [x] Команда `/premium` с кнопками тарифов (УЖЕ ЕСТЬ)
- [x] Callback `buy_premium_callback()` - создание invoice (УЖЕ ЕСТЬ)
- [x] Handler `successful_payment_callback()` - вызов API (УЖЕ ЕСТЬ)
- [ ] Добавить команду `/referral` для статистики
- [ ] Проверить регистрацию handlers в main()

### Frontend (WebApp)
- [ ] Обновить текст "создаст анкету" вместо "авторизуется"
- [ ] Добавить модальное окно с slider для выбора месяцев (опционально)
- [ ] Интегрировать кнопку "Купить PRO" в WebApp
- [ ] Добавить отображение статуса PRO в профиле

### Тестирование
- [ ] Тест 1: Реферальная ссылка → создание анкеты → награда 30 дней
- [ ] Тест 2: Покупка 1 месяца через Stars (50 Stars)
- [ ] Тест 3: Покупка 3 месяцев (130 Stars) - проверка скидки
- [ ] Тест 4: Стекирование PRO (купить 1 мес, потом ещё 1 мес)
- [ ] Тест 5: Акция один раз (второй реферал не даёт PRO)

---

## 💡 Важные моменты

### 1. Реферальная акция - ОДИН РАЗ
- Награда выдаётся только если `premium_until = NULL`
- Если реферер УЖЕ получал PRO (купил или получил от другого реферала) → награда НЕ выдаётся
- Это защита от абуза

### 2. Stars платежи - СТЕКИРУЮТСЯ
- Если PRO активен: `premium_until += months`
- Если PRO истёк: `premium_until = NOW() + months`
- Нет ограничений на количество покупок

### 3. Условие выдачи награды
- Награда вызывается в `POST /api/ads` после успешного создания анкеты
- НЕ при авторизации, НЕ при регистрации
- Текст "создаст анкету" уже корректный в логике, нужно обновить только UI

### 4. Telegram vs Web пользователи
- Telegram: numeric `id` в таблице `users`, PRO в `is_premium/premium_until`
- Web: `user_token` в таблице `premium_tokens`, PRO в `is_premium/premium_until`
- API поддерживает оба канала автоматически

### 5. Цены и скидки
- 1 месяц: 50 Stars (499₸) - 0% скидка
- 3 месяца: 130 Stars (1,299₸) - 17% скидка
- 6 месяцев: 215 Stars (2,149₸) - 30% скидка
- 12 месяцев: 360 Stars (3,499₸) - 41% скидка

---

## 🚀 Следующие шаги

1. **Создать API endpoint** `/api/premium/activate` (5 мин)
2. **Применить миграцию** `021_premium_transactions.sql` (2 мин)
3. **Добавить `/referral` в бота** (10 мин)
4. **Обновить тексты в WebApp** (2 мин)
5. **Протестировать** полный флоу (30 мин)
6. **Опционально**: Slider UI для multi-month покупок (1-2 часа)

**Готово к внедрению!** 🎉
