# 🎯 Система монетизации PRO с Trial, Рефералами и Ползунком

## 📊 Воронка конверсии:

```
РЕГИСТРАЦИЯ
    ↓
🆓 Trial 7 часов (автоматически)
    ↓
⏰ Trial закончился → Выбор:
    ↓
    ├─→ 🎁 Пригласить друга → 30 дней PRO бесплатно
    │   (друг создал профиль → награда)
    │
    └─→ 💰 Купить PRO → Ползунок выбора периода
        ├─→ Оплата Stars (50-360 Stars)
        └─→ Оплата валютой (499₸-3,499₸)
```

---

## 🔧 1. База данных (SQL миграция)

```sql
-- ============================================
-- ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ - ДОПОЛНЕНИЯ
-- ============================================

ALTER TABLE users 
-- PRO подписка
ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS premium_until TIMESTAMP,
ADD COLUMN IF NOT EXISTS premium_trial_used BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS premium_trial_started_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS premium_transaction_id TEXT,
ADD COLUMN IF NOT EXISTS premium_months INTEGER,

-- Реферальная система
ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20) UNIQUE,
ADD COLUMN IF NOT EXISTS referred_by BIGINT, -- telegram_id пригласителя
ADD COLUMN IF NOT EXISTS referral_reward_given BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS total_referrals INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS successful_referrals INTEGER DEFAULT 0; -- кто создал профиль

-- Функция генерации реферального кода
CREATE OR REPLACE FUNCTION generate_referral_code(user_telegram_id BIGINT)
RETURNS VARCHAR(20) AS $$
BEGIN
  RETURN CONCAT('ref_', SUBSTRING(MD5(user_telegram_id::TEXT), 1, 8));
END;
$$ LANGUAGE plpgsql;

-- Автоматически создаем реферальный код при создании пользователя
CREATE OR REPLACE FUNCTION set_referral_code()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.referral_code IS NULL THEN
    NEW.referral_code := generate_referral_code(NEW.telegram_id);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_referral_code
BEFORE INSERT ON users
FOR EACH ROW EXECUTE FUNCTION set_referral_code();

-- ============================================
-- ТАБЛИЦА РЕФЕРАЛОВ
-- ============================================

CREATE TABLE IF NOT EXISTS referrals (
  id SERIAL PRIMARY KEY,
  referrer_telegram_id BIGINT NOT NULL,  -- кто пригласил
  referred_telegram_id BIGINT NOT NULL,  -- кого пригласили
  referral_code VARCHAR(20),
  
  -- Статусы
  registered BOOLEAN DEFAULT false,      -- зарегистрировался
  profile_created BOOLEAN DEFAULT false, -- создал профиль
  reward_given BOOLEAN DEFAULT false,    -- награда выдана
  
  -- Даты
  registered_at TIMESTAMP,
  profile_created_at TIMESTAMP,
  reward_given_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(referrer_telegram_id, referred_telegram_id)
);

CREATE INDEX idx_referrals_referrer ON referrals(referrer_telegram_id);
CREATE INDEX idx_referrals_referred ON referrals(referred_telegram_id);
CREATE INDEX idx_referrals_code ON referrals(referral_code);

-- ============================================
-- ТАБЛИЦА PREMIUM ТРАНЗАКЦИЙ
-- ============================================

CREATE TABLE IF NOT EXISTS premium_transactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  telegram_id BIGINT NOT NULL,
  
  -- Детали покупки
  months INTEGER NOT NULL,
  amount_stars INTEGER,              -- если оплата Stars
  amount_currency DECIMAL(10,2),     -- если оплата валютой
  currency VARCHAR(3),                -- KZT, RUB, USD
  payment_method VARCHAR(20),        -- 'stars', 'card', 'referral'
  
  -- Telegram транзакция
  transaction_id TEXT UNIQUE,
  telegram_payment_charge_id TEXT,
  
  -- Даты
  created_at TIMESTAMP DEFAULT NOW(),
  activated_at TIMESTAMP
);

CREATE INDEX idx_premium_trans_telegram_id ON premium_transactions(telegram_id);
CREATE INDEX idx_premium_trans_transaction_id ON premium_transactions(transaction_id);

-- ============================================
-- ПРЕДСТАВЛЕНИЕ ДЛЯ СТАТИСТИКИ РЕФЕРАЛОВ
-- ============================================

CREATE OR REPLACE VIEW referral_stats AS
SELECT 
  u.telegram_id,
  u.referral_code,
  u.total_referrals,
  u.successful_referrals,
  COUNT(r.id) FILTER (WHERE r.registered = true) as registered_count,
  COUNT(r.id) FILTER (WHERE r.profile_created = true) as profile_created_count,
  COUNT(r.id) FILTER (WHERE r.reward_given = true) as reward_given_count
FROM users u
LEFT JOIN referrals r ON r.referrer_telegram_id = u.telegram_id
GROUP BY u.telegram_id, u.referral_code, u.total_referrals, u.successful_referrals;
```

---

## 🎯 2. API Endpoints

### 2.1. `/api/premium/check` - Проверка статуса PRO

```typescript
// GET /api/premium/check?telegram_id=123456
export default async function handler(req, res) {
  const { telegram_id } = req.query;
  
  const user = await sql`
    SELECT 
      telegram_id,
      is_premium,
      premium_until,
      premium_trial_used,
      premium_trial_started_at,
      referral_code,
      total_referrals
    FROM users 
    WHERE telegram_id = ${telegram_id}
  `;
  
  if (!user[0]) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  const now = new Date();
  const u = user[0];
  
  // Проверяем Trial (7 часов = 25200 секунд)
  let trial_active = false;
  let trial_remaining = 0;
  
  if (u.premium_trial_started_at && !u.premium_trial_used) {
    const trial_elapsed = (now - new Date(u.premium_trial_started_at)) / 1000;
    trial_remaining = Math.max(0, 25200 - trial_elapsed);
    trial_active = trial_remaining > 0;
  }
  
  // Проверяем платную подписку
  const premium_active = u.is_premium && u.premium_until && new Date(u.premium_until) > now;
  
  return res.json({
    telegram_id: u.telegram_id,
    has_premium: premium_active || trial_active,
    premium_type: premium_active ? 'paid' : (trial_active ? 'trial' : 'none'),
    premium_until: u.premium_until,
    trial_remaining_seconds: Math.floor(trial_remaining),
    trial_used: u.premium_trial_used,
    referral_code: u.referral_code,
    total_referrals: u.total_referrals
  });
}
```

### 2.2. `/api/premium/start-trial` - Старт Trial

```typescript
// POST /api/premium/start-trial
export default async function handler(req, res) {
  const { telegram_id } = req.body;
  
  // Проверяем не использован ли уже Trial
  const check = await sql`
    SELECT premium_trial_used, premium_trial_started_at 
    FROM users 
    WHERE telegram_id = ${telegram_id}
  `;
  
  if (check[0]?.premium_trial_used) {
    return res.status(400).json({ error: 'Trial already used' });
  }
  
  // Запускаем Trial
  const result = await sql`
    UPDATE users 
    SET 
      premium_trial_started_at = NOW(),
      is_premium = true,
      updated_at = NOW()
    WHERE telegram_id = ${telegram_id}
    RETURNING telegram_id, premium_trial_started_at
  `;
  
  return res.json({
    success: true,
    trial_started: result[0].premium_trial_started_at,
    trial_ends_in_seconds: 25200 // 7 часов
  });
}
```

### 2.3. `/api/referral/register` - Регистрация по рефералке

```typescript
// POST /api/referral/register
export default async function handler(req, res) {
  const { telegram_id, referral_code } = req.body;
  
  if (!referral_code || !telegram_id) {
    return res.status(400).json({ error: 'Missing data' });
  }
  
  // Находим пригласителя
  const referrer = await sql`
    SELECT telegram_id FROM users WHERE referral_code = ${referral_code}
  `;
  
  if (!referrer[0]) {
    return res.status(404).json({ error: 'Invalid referral code' });
  }
  
  const referrer_id = referrer[0].telegram_id;
  
  // Нельзя пригласить самого себя
  if (referrer_id === telegram_id) {
    return res.status(400).json({ error: 'Cannot refer yourself' });
  }
  
  // Создаем запись реферала
  await sql`
    INSERT INTO referrals 
      (referrer_telegram_id, referred_telegram_id, referral_code, registered, registered_at)
    VALUES 
      (${referrer_id}, ${telegram_id}, ${referral_code}, true, NOW())
    ON CONFLICT (referrer_telegram_id, referred_telegram_id) DO NOTHING
  `;
  
  // Обновляем referred_by у нового пользователя
  await sql`
    UPDATE users 
    SET referred_by = ${referrer_id}
    WHERE telegram_id = ${telegram_id}
  `;
  
  return res.json({ success: true, referrer_id });
}
```

### 2.4. `/api/referral/complete` - Завершение реферала (создан профиль)

```typescript
// POST /api/referral/complete
export default async function handler(req, res) {
  const { telegram_id } = req.body;
  
  // Находим реферальную запись
  const referral = await sql`
    SELECT r.*, u.telegram_id as referrer_id
    FROM referrals r
    JOIN users u ON u.telegram_id = r.referrer_telegram_id
    WHERE r.referred_telegram_id = ${telegram_id}
      AND r.profile_created = false
  `;
  
  if (!referral[0]) {
    return res.json({ success: false, message: 'No referral found' });
  }
  
  const ref = referral[0];
  
  // Отмечаем что профиль создан
  await sql`
    UPDATE referrals 
    SET 
      profile_created = true,
      profile_created_at = NOW()
    WHERE id = ${ref.id}
  `;
  
  // Увеличиваем счетчик у пригласителя
  await sql`
    UPDATE users 
    SET 
      total_referrals = total_referrals + 1,
      successful_referrals = successful_referrals + 1
    WHERE telegram_id = ${ref.referrer_id}
  `;
  
  // Даем награду обоим (30 дней PRO)
  const premium_until = new Date();
  premium_until.setDate(premium_until.getDate() + 30);
  
  // Пригласителю
  await sql`
    UPDATE users 
    SET 
      is_premium = true,
      premium_until = GREATEST(
        COALESCE(premium_until, NOW()), 
        ${premium_until.toISOString()}
      )
    WHERE telegram_id = ${ref.referrer_id}
  `;
  
  // Приглашенному
  await sql`
    UPDATE users 
    SET 
      is_premium = true,
      premium_until = ${premium_until.toISOString()}
    WHERE telegram_id = ${telegram_id}
  `;
  
  // Отмечаем что награда выдана
  await sql`
    UPDATE referrals 
    SET reward_given = true, reward_given_at = NOW()
    WHERE id = ${ref.id}
  `;
  
  return res.json({
    success: true,
    message: 'Both users received 30 days PRO',
    referrer_id: ref.referrer_id,
    referred_id: telegram_id
  });
}
```

### 2.5. `/api/premium/calculate` - Расчет цены для ползунка

```typescript
// GET /api/premium/calculate?months=6&location=KZ
export default async function handler(req, res) {
  const { months, location = 'KZ' } = req.query;
  
  const monthsNum = parseInt(months);
  
  if (monthsNum < 1 || monthsNum > 12) {
    return res.status(400).json({ error: 'Months must be 1-12' });
  }
  
  // Базовая цена за месяц
  const base_price_stars = 50;
  const base_price_kzt = 499;
  const base_price_rub = 103;
  
  // Скидки
  const discount = monthsNum >= 12 ? 0.41 : 
                   monthsNum >= 6 ? 0.30 :
                   monthsNum >= 3 ? 0.17 : 0;
  
  // Расчет
  const full_price_stars = base_price_stars * monthsNum;
  const discounted_stars = Math.round(full_price_stars * (1 - discount));
  
  const full_price_kzt = base_price_kzt * monthsNum;
  const discounted_kzt = Math.round(full_price_kzt * (1 - discount));
  
  const full_price_rub = base_price_rub * monthsNum;
  const discounted_rub = Math.round(full_price_rub * (1 - discount));
  
  const savings_stars = full_price_stars - discounted_stars;
  const savings_kzt = full_price_kzt - discounted_kzt;
  const savings_rub = full_price_rub - discounted_rub;
  
  // Дата окончания
  const premium_until = new Date();
  premium_until.setMonth(premium_until.getMonth() + monthsNum);
  
  return res.json({
    months: monthsNum,
    discount_percent: Math.round(discount * 100),
    
    stars: {
      price: discounted_stars,
      full_price: full_price_stars,
      savings: savings_stars,
      price_per_month: Math.round(discounted_stars / monthsNum)
    },
    
    kzt: {
      price: discounted_kzt,
      full_price: full_price_kzt,
      savings: savings_kzt,
      price_per_month: Math.round(discounted_kzt / monthsNum),
      currency: '₸'
    },
    
    rub: {
      price: discounted_rub,
      full_price: full_price_rub,
      savings: savings_rub,
      price_per_month: Math.round(discounted_rub / monthsNum),
      currency: '₽'
    },
    
    premium_until: premium_until.toISOString()
  });
}
```

---

## 🎨 3. UI компонент с ползунком (React)

```typescript
// components/PremiumSlider.tsx
import { useState, useEffect } from 'react';

export default function PremiumSlider({ telegramId, location = 'KZ' }) {
  const [months, setMonths] = useState(6);
  const [pricing, setPricing] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    fetchPricing();
  }, [months]);
  
  const fetchPricing = async () => {
    const res = await fetch(`/api/premium/calculate?months=${months}&location=${location}`);
    const data = await res.json();
    setPricing(data);
  };
  
  const handlePurchaseStars = async () => {
    // Открываем Telegram invoice через WebApp
    window.Telegram.WebApp.openInvoice(/* invoice URL */);
  };
  
  const handlePurchaseCurrency = async () => {
    // Открываем платежную систему (Stripe, Yookassa, etc)
  };
  
  if (!pricing) return <div>Loading...</div>;
  
  const currency = location === 'KZ' ? pricing.kzt : pricing.rub;
  
  return (
    <div className="premium-slider">
      <h2>💎 Купить PRO подписку</h2>
      
      {/* Ползунок */}
      <div className="slider-container">
        <label>🎚️ Выбери срок: {months} мес.</label>
        <input 
          type="range" 
          min="1" 
          max="12" 
          value={months}
          onChange={(e) => setMonths(parseInt(e.target.value))}
          className="slider"
        />
        <div className="months-labels">
          <span>1 мес</span>
          <span>6 мес</span>
          <span>12 мес</span>
        </div>
      </div>
      
      {/* Расчет цены */}
      <div className="pricing-display">
        <div className="price-option">
          <h3>⭐ Оплата Stars</h3>
          <div className="price-large">{pricing.stars.price} Stars</div>
          <div className="price-detail">${(pricing.stars.price * 0.02).toFixed(2)}</div>
          {pricing.stars.savings > 0 && (
            <div className="savings">💸 Экономия: {pricing.stars.savings} Stars</div>
          )}
        </div>
        
        <div className="divider">ИЛИ</div>
        
        <div className="price-option">
          <h3>💵 Оплата {currency.currency}</h3>
          <div className="price-large">{currency.price.toLocaleString()} {currency.currency}</div>
          <div className="price-detail">{currency.price_per_month}{currency.currency}/мес</div>
          {currency.savings > 0 && (
            <div className="savings">💸 Экономия: {currency.savings.toLocaleString()}{currency.currency}</div>
          )}
        </div>
      </div>
      
      {/* Инфо */}
      <div className="premium-info">
        {pricing.discount_percent > 0 && (
          <div className="discount-badge">🔥 Скидка {pricing.discount_percent}%</div>
        )}
        <div className="until-date">
          📅 PRO до: {new Date(pricing.premium_until).toLocaleDateString('ru-RU')}
        </div>
      </div>
      
      {/* Кнопки оплаты */}
      <div className="payment-buttons">
        <button onClick={handlePurchaseStars} className="btn-stars">
          💳 Оплатить {pricing.stars.price} Stars
        </button>
        <button onClick={handlePurchaseCurrency} className="btn-currency">
          💵 Оплатить {currency.price.toLocaleString()}{currency.currency}
        </button>
      </div>
    </div>
  );
}
```

---

## 🤖 4. Обновления в боте

### Команда `/referral` - получить реферальную ссылку

```python
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реферальная программа - получить ссылку"""
    user = update.effective_user
    
    # Получаем реферальный код из API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/user?telegram_id={user.id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    referral_code = data['user'].get('referral_code', 'unknown')
                    total_refs = data['user'].get('total_referrals', 0)
                    
                    ref_link = f"https://t.me/{context.bot.username}?start={referral_code}"
                    
                    text = (
                        f"🎁 <b>Пригласи друга - получи 30 дней PRO!</b>\n\n"
                        f"<b>Твоя реферальная ссылка:</b>\n"
                        f"<code>{ref_link}</code>\n\n"
                        f"<b>Как это работает:</b>\n"
                        f"1️⃣ Отправь ссылку другу\n"
                        f"2️⃣ Друг переходит и создает профиль\n"
                        f"3️⃣ Вы ОБА получаете 30 дней PRO! 🎉\n\n"
                        f"👥 Приглашено друзей: <b>{total_refs}</b>\n"
                        f"💎 Заработано PRO: <b>{total_refs * 30} дней</b>\n\n"
                        f"<i>Нет лимитов! Приглашай сколько хочешь!</i>"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("📤 Поделиться ссылкой", 
                                            url=f"https://t.me/share/url?url={ref_link}&text=Попробуй Anonimka - анонимные знакомства! Мы оба получим PRO на месяц 🎁")],
                        [InlineKeyboardButton("« Назад", callback_data="main_menu")]
                    ]
                    
                    await update.message.reply_text(
                        text,
                        parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
    except Exception as e:
        logger.error(f'Ошибка получения реферального кода: {e}')
        await update.message.reply_text('❌ Ошибка. Попробуйте позже')
```

---

## 📱 5. WebApp логика

### При создании профиля - проверить реферала

```typescript
// После успешного создания профиля
async function onProfileCreated(telegram_id: number) {
  // Проверяем есть ли реферал
  const response = await fetch('/api/referral/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ telegram_id })
  });
  
  const result = await response.json();
  
  if (result.success) {
    // Показываем уведомление
    showNotification('🎉 Ты и твой друг получили 30 дней PRO!');
    
    // Уведомляем бота
    window.Telegram.WebApp.sendData(JSON.stringify({
      action: 'referral_completed',
      telegram_id
    }));
  }
}
```

---

## 🎯 6. Итоговый чеклист реализации

### Backend (Next.js API):
- [ ] Создать `/api/premium/check`
- [ ] Создать `/api/premium/start-trial`
- [ ] Создать `/api/premium/calculate`
- [ ] Создать `/api/referral/register`
- [ ] Создать `/api/referral/complete`
- [ ] Обновить `/api/premium/activate`

### Database:
- [ ] Выполнить SQL миграцию (поля PRO + рефералы)
- [ ] Создать таблицу `referrals`
- [ ] Создать таблицу `premium_transactions`
- [ ] Создать триггеры для реферальных кодов

### Frontend (WebApp):
- [ ] Создать компонент `PremiumSlider`
- [ ] Интегрировать проверку Trial
- [ ] Добавить кнопки "Пригласить" / "Купить"
- [ ] Реализовать оплату Stars через WebApp API
- [ ] Реализовать оплату валютой (Stripe/Yookassa)

### Telegram Bot:
- [ ] Добавить команду `/referral`
- [ ] Обновить `/start` для обработки `ref_` параметров
- [ ] Добавить уведомления о завершении Trial
- [ ] Добавить уведомления о успешных рефералах

---

Хотите чтобы я начал реализацию? С чего начнем? 🚀
