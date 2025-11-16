"""
Telegram бот для anonimka.kz с интеграцией Neon PostgreSQL
Обрабатывает сообщения и синхронизирует чаты с WebApp
"""

import os
import logging
import aiohttp
import asyncio
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.error import Forbidden
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Загружаем переменные из .env файла
load_dotenv()

# Настройка логирования - только важные события
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # Показываем только WARNING и ERROR
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Для нашего кода INFO, для библиотек WARNING

# Отключаем verbose логи от библиотек
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Константы из переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE_URL = os.getenv('VERCEL_API_URL', 'https://anonimka.kz')
ADMIN_TG_ID = int(os.getenv('ADMIN_TG_ID', '884253640'))
CHANNEL_USERNAME = '@anonimka_kz'

# Хранилище участников розыгрыша
giveaway_participants = set()  # Множество telegram_id участников
giveaway_active = False  # Статус розыгрыша

# Настройка Menu Button при запуске бота
async def setup_menu_button(application: Application):
    """Настраивает Menu Button для быстрого доступа к приложению и важным ссылкам"""
    try:
        from telegram import MenuButtonWebApp
        
        # Устанавливаем Menu Button с ссылкой на WebApp
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🚀 Открыть Anonimka",
                web_app=WebAppInfo(url=f"{API_BASE_URL}")
            )
        )
        logger.info("✅ Menu Button настроен успешно")
        
        # Устанавливаем начальное короткое описание
        await update_short_description(application)
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Menu Button: {e}")

async def update_short_description(application: Application):
    """Обновляет короткое описание бота (меняется каждый час)"""
    descriptions = [
        "Анонимные знакомства без фильтров. Найди кого-то рядом 🔥",
        "Анонимка для тех, кто не боится быть собой",
        "Знакомства без притворства. Прямо и анонимно",
        "Встречи без масок. Анонимно и честно",
        "Настоящие люди, настоящие желания. Анонимно"
    ]
    
    # Выбираем описание на основе текущего часа
    from datetime import datetime
    hour = datetime.now().hour
    description = descriptions[hour % len(descriptions)]
    
    try:
        # Устанавливаем для всех языков (по умолчанию)
        await application.bot.set_my_short_description(short_description=description)
        # Устанавливаем явно для русского языка
        await application.bot.set_my_short_description(short_description=description, language_code="ru")
        # Устанавливаем явно для английского языка
        await application.bot.set_my_short_description(short_description=description, language_code="en")
        logger.info(f"✅ Short Description обновлен: {description[:50]}...")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления Short Description: {e}")

# Базовые команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - приветствие и открытие WebApp"""
    user = update.effective_user
    
    logger.info(f"👤 /start от user {user.id} (@{user.username or 'no_username'})")
    
    # Проверяем параметр start (для авторизации через Deep Link или реферальной ссылки)
    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        
        # Если это покупка PRO с указанием срока (buy_premium_3m, buy_premium_6m и т.д.)
        if start_param.startswith('buy_premium'):
            logger.info(f"💳 Запрос покупки PRO от user {user.id}: {start_param}")
            
            # Извлекаем количество месяцев из параметра (buy_premium_3m -> 3)
            if '_' in start_param and start_param.endswith('m'):
                months_str = start_param.split('_')[-1].replace('m', '')
                try:
                    months = int(months_str)
                    # Сохраняем в context для использования в premium_command
                    context.user_data['requested_months'] = months
                except ValueError:
                    pass
            
            await premium_command(update, context)
            return
        
        # Если это реферальная ссылка
        if start_param.startswith('ref_'):
            referrer_token = start_param.replace('ref_', '')
            logger.info(f"🔗 Реферал: user {user.id} -> {referrer_token[:8]}...")
            
            # Сохраняем реферальную информацию (будет обработана при создании анкеты в WebApp)
            webapp_url = f"{API_BASE_URL}/webapp?ref={referrer_token}"
            
            await update.message.reply_text(
                f"Ты зашёл не туда. Или туда, куда давно хотел.\n\n"
                f"Анонимные анкеты. Прямые слова. Без фильтров.\n\n"
                f"Попробуй написать первым — пока не написал кто-то другой.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Создать анкету", web_app=WebAppInfo(url=webapp_url))]
                ])
            )
            return
        
        # Если это токен авторизации
        if start_param.startswith('auth_'):
            # Отправляем данные пользователя на сервер
            try:
                async with aiohttp.ClientSession() as session:
                    user_data = {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name or '',
                        'username': user.username or '',
                    }
                    
                    async with session.post(
                        f"{API_BASE_URL}/api/auth",
                        json={
                            "token": start_param,
                            "user": user_data
                        }
                    ) as response:
                        result = await response.json()
                        
                        if result.get('success'):
                            logger.info(f"✅ Авторизация: user {user.id}")
                            
                            # Автоматически открываем WebApp с параметром успешной авторизации
                            webapp_url = f"{API_BASE_URL}/webapp?authorized=true&user_id={user.id}"
                            
                            await update.message.reply_text(
                                f"✅ Авторизация успешна!\n\n"
                                f"🎉 Добро пожаловать, {user.first_name}!\n\n"
                                f"Приложение откроется автоматически 👇",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=webapp_url))]
                                ])
                            )
                            return
            except Exception as e:
                logger.error(f"❌ Ошибка авторизации: {e}")
    
    # Обычное приветствие - рандомный выбор из трёх вариантов
    greetings = [
        # Вариант 1 - загадочный
        (
            f"👋 Привет, {user.first_name}!\n"
            f"Если ты ищешь смыслы — не сюда.\n"
            f"Если ты ищешь приколы, флирт и анонимные признания — добро пожаловать 😏\n\n"
            f"💬 Люди тут срывают маски,\n"
            f"🤫 Делятся мыслями, которые стыдно сказать вслух,\n"
            f"и делают это прямо в лоб.\n\n"
            f"❤️ Создай анкету и проверь,\n"
            f"насколько странные люди живут в твоём городе 👇"
        ),
        # Вариант 2 - дерзкий
        (
            f"Ну что, {user.first_name}...\n"
            f"Опять ищешь кого-то \"не как все\"?\n"
            f"А может, просто скучно и хочешь внимания? 😏\n\n"
            f"🎭 Тут никто не строит ангелов.\n"
            f"Просто пиши — как думаешь.\n"
            f"Читай — как есть.\n"
            f"Флиртуй — если не страшно.\n\n"
            f"🔥 Создай анкету.\n"
            f"Будет неловко. Будет весело.\n"
            f"Будет по-настоящему 👇"
        ),
        # Вариант 3 - прямолинейный
        (
            f"🎭 Тут не Tinder, не Badoo и не мамин чат.\n"
            f"Тут пишут как есть — без фотошопа и понтов.\n\n"
            f"❤️ Хочешь — флиртуй.\n"
            f"💬 Хочешь — молчи и читай чужие кринжи.\n"
            f"📍 Хочешь — найди кого-то в своём городе.\n\n"
            f"🚀 Создай анкету, и посмотрим, кто рискнёт написать тебе первым �"
        )
    ]
    
    selected_greeting = random.choice(greetings)
    
    keyboard = [
        [InlineKeyboardButton("🚀 Создать анкету", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))],
        [
            InlineKeyboardButton("⭐ Купить PRO", callback_data="premium"),
            InlineKeyboardButton("🎁 Пригласи друга", callback_data="referral")
        ],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/anonimka_kz")]
    ]
    
    # Добавляем кнопку розыгрыша если он активен
    global giveaway_active
    if giveaway_active:
        keyboard.append([InlineKeyboardButton("🎉 Я выполнил условия розыгрыша", callback_data="participate_giveaway")])
    
    keyboard.extend([
        [
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
            InlineKeyboardButton("ℹ️ О проекте", callback_data="about")
        ],
        [InlineKeyboardButton("💬 Поддержка и реклама", callback_data="contacts")]
    ])
    
    await update.message.reply_text(
        selected_greeting,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu - главное меню с полезными ссылками"""
    menu_text = (
        "📱 <b>Главное меню Anonimka</b>\n\n"
        "Выберите действие из меню ниже:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}"))],
        [
            InlineKeyboardButton("⭐ Купить PRO", callback_data="premium"),
            InlineKeyboardButton("🎁 Пригласи друга", callback_data="referral")
        ],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/anonimka_kz")]
    ]
    
    # Добавляем кнопку розыгрыша если он активен
    global giveaway_active
    if giveaway_active:
        keyboard.append([InlineKeyboardButton("🎉 Я выполнил условия розыгрыша", callback_data="participate_giveaway")])
    
    keyboard.extend([
        [
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
            InlineKeyboardButton("ℹ️ О проекте", callback_data="about")
        ],
        [InlineKeyboardButton("💬 Поддержка и реклама", callback_data="contacts")]
    ])
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            menu_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            menu_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - информация о боте"""
    help_text = (
        "📖 <b>Справка по Anonimka.kz</b>\n\n"
        "🚀 <b>Запустить приложение</b> - открыть WebApp для создания анкет и общения\n\n"
        "❓ <b>Помощь</b> - показать эту справку\n\n"
        "💡 <b>Как пользоваться:</b>\n"
        "1. Нажмите 'Запустить приложение'\n"
        "2. Создайте анкету или просмотрите существующие\n"
        "3. Начните общение в чате\n"
        "4. Получайте уведомления о новых сообщениях здесь в боте\n\n"
        "🎯 Все анкеты анонимны и автоматически удаляются через 7 дней!\n\n"
        "📋 <b>Полезные ссылки:</b>\n"
        f"• <a href='{API_BASE_URL}/TERMS_OF_SERVICE.md'>Правила использования</a>\n"
        f"• <a href='{API_BASE_URL}/PRIVACY_POLICY.md'>Политика конфиденциальности</a>\n"
        "• Тех.поддержка: @Vorobey_444"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Запустить приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))],
        [InlineKeyboardButton("📱 Главное меню", callback_data="main_menu")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            help_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о проекте"""
    about_text = (
        "ℹ️ <b>О проекте Anonimka.kz</b>\n\n"
        "Анонимная платформа знакомств без регистрации и личных данных.\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Полная анонимность\n"
        "• Автоудаление анкет через 7 дней\n"
        "• Защищенные чаты\n"
        "• Быстрый поиск собеседников\n\n"
        f"📋 <a href='{API_BASE_URL}/TERMS_OF_SERVICE.md'>Правила</a> | "
        f"<a href='{API_BASE_URL}/PRIVACY_POLICY.md'>Политика</a>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Создать анкету", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            about_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            about_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )

async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать контакты: поддержка и реклама"""
    query = update.callback_query
    await query.answer()
    
    contacts_text = (
        "💬 <b>Контакты и реклама</b>\n\n"
        
        "<b>Техническая поддержка:</b>\n"
        "@Vorobey_444\n\n"
        
        "<b>Реклама и сотрудничество:</b>\n"
        "📧 Email: aleksey@vorobey444.ru\n"
        "💬 Telegram: @Vorobey_444\n\n"
        
        "Мы открыты к предложениям!"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=contacts_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def referral_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler для кнопки реферальной программы"""
    user = update.effective_user
    query = update.callback_query
    await query.answer()
    
    logger.info(f"🔗 /referral callback от user {user.id}")
    
    try:
        # Получаем статистику из API
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{API_BASE_URL}/api/referrals?userId={user.id}',
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    total = data.get('total', 0)
                    rewarded = data.get('rewarded', 0)
                    pending = data.get('pending', 0)
                    
                    # Генерируем реферальную ссылку
                    bot_username = (await context.bot.get_me()).username
                    ref_link = f"https://t.me/{bot_username}?startapp=ref_{user.id}"
                    
                    text = (
                        f"🎁 <b>Пригласи друга - получи 30 дней PRO!</b>\n\n"
                        f"<b>Твоя реферальная ссылка:</b>\n"
                        f"<code>{ref_link}</code>\n\n"
                        f"<b>Как это работает:</b>\n"
                        f"1️⃣ Отправь ссылку другу\n"
                        f"2️⃣ Друг переходит и <b>создаёт анкету</b>\n"
                        f"3️⃣ Ты получаешь 30 дней PRO! 🎉\n\n"
                        f"👥 Приглашено: <b>{total}</b> друзей\n"
                        f"✅ Награда получена: <b>{rewarded}</b> раз\n"
                        f"⏳ В ожидании: <b>{pending}</b>\n\n"
                        f"⚠️ <i>Акция действует ОДИН РАЗ для новых пользователей</i>\n"
                        f"💡 <i>Если ты уже получал PRO ранее, новые рефералы не дадут награду</i>"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton(
                            "📤 Поделиться ссылкой", 
                            url=f"https://t.me/share/url?url={ref_link}&text=Попробуй Anonimka - анонимные знакомства! Мы оба получим PRO на месяц 🎁"
                        )],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                    ]
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                else:
                    logger.error(f'❌ API /referrals вернул статус {resp.status}')
                    await query.edit_message_text(
                        '❌ Ошибка получения статистики\nПопробуйте позже',
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]])
                    )
    except Exception as e:
        logger.error(f"❌ Ошибка /referral callback: {e}")
        await query.edit_message_text(
            '❌ Ошибка обработки команды\nПопробуйте позже или обратитесь в поддержку',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]])
        )

async def my_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /my_chats - показать мои чаты"""
    user_id = update.effective_user.id
    
    try:
        # Получаем активные чаты через API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/neon-chats",
                json={
                    "action": "get-active",
                    "params": {"userId": str(user_id)}
                }
            ) as response:
                result = await response.json()
                
                if result.get('error'):
                    await update.message.reply_text(
                        "❌ Ошибка загрузки чатов\n\n"
                        "Попробуйте позже или откройте приложение:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
                        ])
                    )
                    return
                
                chats = result.get('data', [])
                
                if not chats:
                    await update.message.reply_text(
                        "📭 У вас пока нет активных чатов\n\n"
                        "Откройте приложение для поиска объявлений:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
                        ])
                    )
                    return
                
                # Формируем кнопки с чатами
                keyboard = []
                for chat in chats[:10]:  # Показываем максимум 10 чатов
                    keyboard.append([
                        InlineKeyboardButton(
                            f"💬 Чат по объявлению #{chat['ad_id']}",
                            callback_data=f"openchat_{chat['id']}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton("📱 Открыть в приложении", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))
                ])
                
                await update.message.reply_text(
                    f"💬 **Ваши активные чаты** ({len(chats)}):\n\n"
                    f"Выберите чат для просмотра:",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    
    except Exception as e:
        logger.error(f"Ошибка в my_chats: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка\n\n"
            "Попробуйте позже"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений - отправка в активный чат"""
    # Игнорируем сообщения из каналов и без пользователя
    if not update.effective_user or not update.message:
        return
    
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Игнорируем команды (на всякий случай)
    if message_text.startswith('/'):
        return
    
    # Игнорируем короткие сообщения и кнопки (меньше 3 символов или эмодзи)
    # Это могут быть случайные нажатия или системные кнопки
    if len(message_text.strip()) < 3:
        return
    
    logger.info(f"📝 Сообщение от user {user_id}: {message_text[:30]}...")
    
    # Проверяем есть ли активный чат в контексте
    active_chat_id = context.user_data.get('active_chat_id') if context.user_data else None
    
    if active_chat_id:
        # Отправляем сообщение в активный чат
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE_URL}/api/neon-messages",
                    json={
                        "action": "send-message",
                        "params": {
                            "chatId": active_chat_id,
                            "senderId": str(user_id),
                            "messageText": message_text,
                            "skipNotification": False  # Отправляем уведомление
                        }
                    }
                ) as response:
                    result = await response.json()
                    
                    if result.get('error'):
                        logger.warning(f"❌ Ошибка отправки: {result.get('error')}")
                        await update.message.reply_text(
                            "❌ Ошибка отправки сообщения\n\n"
                            "Возможно чат был закрыт или заблокирован."
                        )
                        # Сбрасываем активный чат
                        if context.user_data:
                            context.user_data.pop('active_chat_id', None)
                    else:
                        logger.info(f"✅ Сообщение отправлено в чат {active_chat_id}")
                        await update.message.reply_text("✅ Сообщение отправлено!")
        
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            await update.message.reply_text("❌ Ошибка отправки сообщения")
    else:
        # Нет активного чата - предлагаем выбрать
        await update.message.reply_text(
            "💬 У вас нет активного чата\n\n"
            "Используйте /my_chats чтобы выбрать чат\n"
            "или откройте приложение:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Мои чаты", callback_data="show_my_chats")],
                [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
            ])
        )

async def open_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки открытия чата"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.data.replace("openchat_", "")
    user_id = query.from_user.id
    
    logger.info(f"💬 Открытие чата {chat_id} от user {user_id}")
    
    try:
        # Получаем информацию о чате
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/neon-chats",
                json={
                    "action": "get-active",
                    "params": {"userId": str(user_id)}
                }
            ) as response:
                result = await response.json()
                
                if result.get('error'):
                    await query.edit_message_text("❌ Ошибка загрузки чата")
                    return
                
                chats = result.get('data', [])
                chat = next((c for c in chats if str(c['id']) == chat_id), None)
                
                if not chat:
                    await query.edit_message_text("❌ Чат не найден")
                    return
                
                # Устанавливаем активный чат
                if context.user_data is not None:
                    context.user_data['active_chat_id'] = int(chat_id)
                
                # Получаем последние сообщения
                async with session.post(
                    f"{API_BASE_URL}/api/neon-messages",
                    json={
                        "action": "get-messages",
                        "params": {"chatId": int(chat_id)}
                    }
                ) as msg_response:
                    msg_result = await msg_response.json()
                    messages = msg_result.get('data', [])
                    
                    # Помечаем сообщения как прочитанные
                    await session.post(
                        f"{API_BASE_URL}/api/neon-messages",
                        json={
                            "action": "mark-read",
                            "params": {"chatId": int(chat_id), "userId": str(user_id)}
                        }
                    )
                    
                    # Формируем текст с последними сообщениями
                    chat_text = f"💬 **Чат по объявлению #{chat['ad_id']}**\n\n"
                    
                    if messages:
                        # Показываем последние 5 сообщений
                        recent = messages[-5:]
                        for msg in recent:
                            sender_label = "Вы" if str(msg['sender_id']) == str(user_id) else "Собеседник"
                            chat_text += f"**{sender_label}:** {msg['message']}\n\n"
                    else:
                        chat_text += "_Нет сообщений. Начните диалог!_\n\n"
                    
                    chat_text += "✍️ Напишите сообщение в этот чат:"
                    
                    await query.edit_message_text(
                        chat_text,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📋 Вернуться к списку", callback_data="show_my_chats")],
                            [InlineKeyboardButton("📱 Открыть в приложении", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
                        ])
                    )
    
    except Exception as e:
        logger.error(f"Ошибка в open_chat_callback: {e}")
        await query.edit_message_text("❌ Произошла ошибка")

async def show_my_chats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки "Мои чаты" """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    logger.info(f"📋 Запрос списка чатов от user {user_id}")
    
    try:
        # Получаем чаты пользователя
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/neon-chats",
                json={
                    "action": "get-active",
                    "params": {"userId": str(user_id)}
                }
            ) as response:
                result = await response.json()
                
                if result.get('error'):
                    await query.edit_message_text(
                        "❌ Ошибка загрузки чатов\n\n"
                        "Попробуйте позже или откройте приложение:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
                        ])
                    )
                    return
                
                chats = result.get('data', [])
                
                if not chats:
                    logger.info(f"📭 У user {user_id} нет активных чатов")
                    await query.edit_message_text(
                        "📭 У вас пока нет активных чатов\n\n"
                        "Откройте приложение для поиска объявлений:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
                        ])
                    )
                    return
                
                logger.info(f"✅ Загружено {len(chats)} чатов для user {user_id}")
                
                # Формируем кнопки с чатами
                keyboard = []
                for chat in chats[:10]:  # Показываем максимум 10 чатов
                    keyboard.append([
                        InlineKeyboardButton(
                            f"💬 Чат по объявлению #{chat['ad_id']}",
                            callback_data=f"openchat_{chat['id']}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton("📱 Открыть в приложении", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))
                ])
                
                await query.edit_message_text(
                    f"💬 **Ваши активные чаты** ({len(chats)}):\n\n"
                    f"Выберите чат для просмотра:",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    
    except Exception as e:
        logger.error(f"Ошибка в show_my_chats_callback: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка\n\n"
            "Попробуйте позже"
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок"""
    err = context.error
    logger.info(f"Обработка ошибки: {err}")

    # Если конфликт getUpdates - останавливаем бота (запущен в другом месте)
    if 'conflict' in str(err).lower() and 'getupdates' in str(err).lower():
        logger.error(f"❌ Критическая ошибка: {err}")
        logger.error("🚨 ОСТАНОВКА БОТА: Обнаружена другая активная копия бота!")
        # Не возвращаем, чтобы ошибка прошла дальше и остановила polling
        raise err

    # Если бот был заблокирован пользователем — игнорируем (обычная ситуация)
    try:
        if isinstance(err, Forbidden) or 'bot was blocked' in str(err).lower() or 'forbidden' in str(err).lower():
            logger.warning(f"⚠️ Бот заблокирован пользователем или доступ запрещён: {err}")
            return
    except Exception:
        # На случай, если err не является классом Exception с ожидаемыми свойствами
        pass

    # Логируем только критические ошибки; сетевые — предупреждение
    if "NetworkError" in str(err) or "ReadError" in str(err) or 'connecterror' in str(err).lower():
        logger.warning("🔄 Временная сетевая ошибка, переподключение...")
        # После автоматического переподключения логируем успех
        asyncio.create_task(log_reconnect_success())
        return

    # По умолчанию логируем полную трассировку для дебага
    logger.exception(f"❌ Критическая ошибка: {err}")

async def log_reconnect_success():
    """Логирует успешное переподключение после сетевой ошибки"""
    await asyncio.sleep(2)  # Ждем 2 секунды для завершения переподключения
    logger.info("✅ Переподключение успешно! Бот работает нормально.")

# ============= МОДЕРАЦИЯ =============

ADMIN_TG_ID = 884253640

# Обработчик кнопки "Забанить"
async def moderate_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Забанить' в жалобе"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_TG_ID:
        await query.edit_message_text('❌ Доступ запрещен')
        return
    
    data = query.data
    parts = data.split('_')
    report_id = int(parts[1])
    banned_user_id = int(parts[2])
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f'{API_BASE_URL}/api/reports',
                json={
                    'reportId': report_id,
                    'action': 'approve',
                    'adminId': ADMIN_TG_ID,
                    'adminNotes': 'Забанен через бота'
                }
            ) as response:
                if response.status == 200:
                    new_text = query.message.text + f'\n\n✅ <b>ЗАБАНЕН</b> администратором'
                    await query.edit_message_text(new_text, parse_mode='HTML')
                    logger.info(f'✅ Пользователь {banned_user_id} забанен по жалобе #{report_id}')
                else:
                    await query.edit_message_text('❌ Ошибка при бане')
    except Exception as e:
        logger.error(f'Ошибка бана: {e}')
        await query.edit_message_text('❌ Ошибка при бане')

# Обработчик кнопки "Отклонить"
async def moderate_reject_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Отклонить' в жалобе"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_TG_ID:
        await query.edit_message_text('❌ Доступ запрещен')
        return
    
    data = query.data
    report_id = int(data.split('_')[1])
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f'{API_BASE_URL}/api/reports',
                json={
                    'reportId': report_id,
                    'action': 'reject',
                    'adminId': ADMIN_TG_ID,
                    'adminNotes': 'Жалоба отклонена'
                }
            ) as response:
                if response.status == 200:
                    new_text = query.message.text + f'\n\n❌ <b>ОТКЛОНЕНА</b> администратором'
                    await query.edit_message_text(new_text, parse_mode='HTML')
                    logger.info(f'❌ Жалоба #{report_id} отклонена')
                else:
                    await query.edit_message_text('❌ Ошибка при отклонении')
    except Exception as e:
        logger.error(f'Ошибка отклонения: {e}')
        await query.edit_message_text('❌ Ошибка')

# Команда /reports - список жалоб
async def reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список активных жалоб"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{API_BASE_URL}/api/reports?userId={user_id}&status=pending'
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    reports = data.get('reports', [])
                    
                    if not reports:
                        await update.message.reply_text('📭 Активных жалоб нет')
                        return
                    
                    text = f'📋 <b>Активные жалобы ({len(reports)}):</b>\n\n'
                    for r in reports[:10]:
                        text += (
                            f'🆔 #{r["id"]} | {r["reason"]}\n'
                            f'От: {r["reporter_nickname"]} → На: {r["reported_nickname"]}\n'
                            f'Дата: {r["created_at"][:10]}\n\n'
                        )
                    
                    await update.message.reply_text(text, parse_mode='HTML')
                else:
                    await update.message.reply_text('❌ Ошибка загрузки жалоб')
    except Exception as e:
        logger.error(f'Ошибка получения жалоб: {e}')
        await update.message.reply_text('❌ Ошибка')

# ============================================
# КОМАНДЫ ДЛЯ РОЗЫГРЫША TELEGRAM STARS
# ============================================

async def start_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать новый розыгрыш Stars (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    global giveaway_active, giveaway_participants
    
    if giveaway_active:
        await update.message.reply_text(
            f'⚠️ Розыгрыш уже активен!\n'
            f'Участников: {len(giveaway_participants)}\n\n'
            f'Используйте /end_giveaway чтобы завершить'
        )
        return
    
    # Очищаем список и активируем розыгрыш
    giveaway_participants.clear()
    giveaway_active = True
    
    await update.message.reply_text(
        '✅ Розыгрыш ЗАПУЩЕН!\n\n'
        '📝 Теперь опубликуйте анонс в канале @anonimka_kz:\n\n'
        '━━━━━━━━━━━━━━━━\n'
        '🎁 <b>РОЗЫГРЫШ 500 TELEGRAM STARS!</b>\n\n'
        '🎯 <b>Условия:</b>\n'
        '1️⃣ Подписаться на канал @anonimka_kz\n'
        '2️⃣ Создать анонимный профиль в боте @anonimka_kz_bot\n'
        '3️⃣ Нажать в боте кнопку <b>✅ Я выполнил условия розыгрыша</b>\n\n'
        '⏰ Розыгрыш через 48 часов!\n'
        '🎲 Победитель - случайный участник\n\n'
        '💡 Создай профиль → Найди кого-то рядом 🔥\n'
        '━━━━━━━━━━━━━━━━',
        parse_mode='HTML'
    )

async def participate_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Участие в розыгрыше"""
    global giveaway_active, giveaway_participants
    
    if not giveaway_active:
        await update.message.reply_text(
            '❌ Сейчас нет активного розыгрыша\n\n'
            'Следите за новостями в @anonimka_kz'
        )
        return
    
    user = update.effective_user
    user_id = user.id
    
    # Проверяем, уже участвует ли
    if user_id in giveaway_participants:
        await update.message.reply_text(
            '✅ Вы уже участвуете в розыгрыше!\n\n'
            f'Всего участников: {len(giveaway_participants)}'
        )
        return
    
    # Проверяем подписку на канал
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(
                '❌ Сначала подпишитесь на канал @anonimka_kz\n\n'
                'После подписки попробуйте снова: /participate'
            )
            return
    except Exception as e:
        logger.warning(f'Не удалось проверить подписку для {user_id}: {e}')
    
    # Проверяем наличие профиля через API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/user?telegram_id={user_id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if not data.get('user'):
                        await update.message.reply_text(
                            '❌ Сначала создайте анонимный профиль!\n\n'
                            'Нажмите кнопку ниже чтобы начать 👇',
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🚀 Создать профиль", web_app=WebAppInfo(url=API_BASE_URL))
                            ]])
                        )
                        return
    except Exception as e:
        logger.error(f'Ошибка проверки профиля: {e}')
    
    # Добавляем участника
    giveaway_participants.add(user_id)
    
    await update.message.reply_text(
        f'🎉 Отлично! Вы участвуете в розыгрыше!\n\n'
        f'👥 Всего участников: {len(giveaway_participants)}\n\n'
        f'🍀 Желаем удачи!\n'
        f'Следите за результатами в @anonimka_kz'
    )
    
    logger.info(f'✅ Новый участник розыгрыша: {user_id} (@{user.username or "no_username"})')

async def giveaway_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика текущего розыгрыша (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    global giveaway_active, giveaway_participants
    
    status = "🟢 АКТИВЕН" if giveaway_active else "⚫️ НЕ АКТИВЕН"
    
    await update.message.reply_text(
        f'📊 <b>СТАТИСТИКА РОЗЫГРЫША</b>\n\n'
        f'Статус: {status}\n'
        f'👥 Участников: {len(giveaway_participants)}\n\n'
        f'Команды:\n'
        f'/start_giveaway - запустить новый\n'
        f'/pick_winner - выбрать победителя\n'
        f'/end_giveaway - завершить без победителя',
        parse_mode='HTML'
    )

async def pick_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрать случайного победителя (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    global giveaway_active, giveaway_participants
    
    if not giveaway_active:
        await update.message.reply_text('❌ Нет активного розыгрыша')
        return
    
    if len(giveaway_participants) == 0:
        await update.message.reply_text('❌ Нет участников!')
        return
    
    # Выбираем случайного победителя
    winner_id = random.choice(list(giveaway_participants))
    
    try:
        # Получаем информацию о победителе
        winner = await context.bot.get_chat(winner_id)
        winner_name = winner.username or winner.first_name or str(winner_id)
        
        # Завершаем розыгрыш
        giveaway_active = False
        
        await update.message.reply_text(
            f'🎊 <b>ПОБЕДИТЕЛЬ ВЫБРАН!</b>\n\n'
            f'👤 @{winner_name} (ID: {winner_id})\n'
            f'👥 Всего участвовало: {len(giveaway_participants)}\n\n'
            f'📢 Опубликуйте результат в канале!\n\n'
            f'💬 Отправьте победителю:\n'
            f'<code>Поздравляем! Вы выиграли 500 Stars! 🎉</code>',
            parse_mode='HTML'
        )
        
        # Пытаемся отправить сообщение победителю
        try:
            await context.bot.send_message(
                chat_id=winner_id,
                text=(
                    '🎊 <b>ПОЗДРАВЛЯЕМ!</b>\n\n'
                    'Вы выиграли в розыгрыше 500 Telegram Stars! 🎁\n\n'
                    'Администратор свяжется с вами для передачи приза.\n\n'
                    'Спасибо что с нами! ❤️'
                ),
                parse_mode='HTML'
            )
        except Forbidden:
            await update.message.reply_text(
                f'⚠️ Не удалось отправить сообщение победителю\n'
                f'(бот заблокирован пользователем)'
            )
        
        logger.info(f'🎊 Победитель розыгрыша: {winner_id} (@{winner_name})')
        
    except Exception as e:
        logger.error(f'Ошибка выбора победителя: {e}')
        await update.message.reply_text(f'❌ Ошибка: {str(e)}')

async def participate_giveaway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки участия в розыгрыше"""
    query = update.callback_query
    await query.answer()
    
    global giveaway_active, giveaway_participants
    
    if not giveaway_active:
        await query.message.reply_text(
            '❌ Сейчас нет активного розыгрыша\n\n'
            'Следите за новостями в @anonimka_kz'
        )
        return
    
    user = update.effective_user
    user_id = user.id
    
    # Проверяем, уже участвует ли
    if user_id in giveaway_participants:
        await query.message.reply_text(
            '✅ Вы уже участвуете в розыгрыше!\n\n'
            f'Всего участников: {len(giveaway_participants)}'
        )
        return
    
    # Проверяем подписку на канал
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await query.message.reply_text(
                '❌ Сначала подпишитесь на канал @anonimka_kz\n\n'
                'После подписки нажмите кнопку снова',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 Подписаться", url="https://t.me/anonimka_kz")
                ]])
            )
            return
    except Exception as e:
        logger.warning(f'Не удалось проверить подписку для {user_id}: {e}')
    
    # Проверяем наличие профиля через API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/user?telegram_id={user_id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if not data.get('user'):
                        await query.message.reply_text(
                            '❌ Сначала создайте анонимный профиль!\n\n'
                            'Нажмите кнопку ниже чтобы начать 👇',
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🚀 Создать профиль", web_app=WebAppInfo(url=API_BASE_URL))
                            ]])
                        )
                        return
    except Exception as e:
        logger.error(f'Ошибка проверки профиля: {e}')
    
    # Добавляем участника
    giveaway_participants.add(user_id)
    
    await query.message.reply_text(
        f'🎉 Отлично! Вы участвуете в розыгрыше!\n\n'
        f'👥 Всего участников: {len(giveaway_participants)}\n\n'
        f'🍀 Желаем удачи!\n'
        f'Следите за результатами в @anonimka_kz'
    )
    
    logger.info(f'✅ Новый участник розыгрыша: {user_id} (@{user.username or "no_username"})')

async def end_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить розыгрыш без выбора победителя (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    global giveaway_active, giveaway_participants
    
    if not giveaway_active:
        await update.message.reply_text('❌ Нет активного розыгрыша')
        return
    
    participants_count = len(giveaway_participants)
    giveaway_active = False
    
    await update.message.reply_text(
        f'✅ Розыгрыш завершен\n'
        f'Участвовало: {participants_count}\n\n'
        f'Данные сохранены. Используйте /start_giveaway для нового розыгрыша'
    )

async def post_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Опубликовать анонс розыгрыша в канале (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    global giveaway_active
    
    if not giveaway_active:
        await update.message.reply_text(
            '⚠️ Сначала запустите розыгрыш командой /start_giveaway'
        )
        return
    
    giveaway_text = (
        "🎁 <b>РОЗЫГРЫШ 500 TELEGRAM STARS!</b>\n\n"
        "Мы дарим 500 Telegram Stars случайному участнику! 🎊\n\n"
        "🎯 <b>Как участвовать?</b>\n\n"
        "1️⃣ Подпишись на @anonimka_kz\n"
        "2️⃣ Открой бота и создай анонимный профиль\n"
        "3️⃣ После создания профиля нажми в боте кнопку:\n"
        "    <b>✅ Я выполнил условия розыгрыша</b>\n\n"
        "⏰ <b>Итоги через 48 часов!</b>\n\n"
        "🎲 Победитель определится случайным образом\n"
        "💰 Приз: 500 Stars сразу на твой аккаунт\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Что такое Anonimka?</b>\n\n"
        "Это не Tinder. Тут пишут как думают.\n"
        "Анонимные знакомства без фильтров.\n"
        "Найди кого-то рядом 🔥\n\n"
        "Без понтов. Только правда.\n"
        "━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [[
        InlineKeyboardButton("🚀 Участвовать в розыгрыше", url="https://t.me/anonimka_kz_bot?start=giveaway")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        message = await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=giveaway_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        await update.message.reply_text(
            f'✅ Анонс розыгрыша опубликован!\n'
            f'ID поста: {message.message_id}\n\n'
            f'Теперь ждем участников 🎉'
        )
        logger.info(f'✅ Анонс розыгрыша опубликован в {CHANNEL_USERNAME}')
    except Exception as e:
        logger.error(f'❌ Ошибка публикации анонса: {e}')
        await update.message.reply_text(
            f'❌ Ошибка публикации:\n{str(e)}\n\n'
            f'Проверьте права бота в канале'
        )

# ============================================
# КОМАНДЫ ДЛЯ ПОКУПКИ PRO ЗА TELEGRAM STARS
# ============================================

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /premium или callback - показ тарифов PRO"""
    
    # Проверяем, был ли указан конкретный срок подписки (из WebApp slider)
    requested_months = context.user_data.get('requested_months')
    
    if requested_months and requested_months in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        # Создаём invoice напрямую без фейкового callback
        logger.info(f"🎯 Автоматическая покупка {requested_months} месяцев от user {update.effective_user.id}")
        
        # Очищаем requested_months чтобы не зациклиться
        context.user_data.pop('requested_months', None)
        
        # Запрашиваем цену с API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{API_BASE_URL}/api/premium/calculate?months={requested_months}',
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f'❌ API calculate вернул {resp.status}')
                        await update.message.reply_text('❌ Ошибка расчёта цены. Попробуйте позже.')
                        return
                    
                    data = await resp.json()
                    if data.get('error'):
                        logger.error(f"❌ API calculate error: {data['error']}")
                        await update.message.reply_text('❌ Ошибка расчёта цены')
                        return
                    
                    # Формируем plan из данных API
                    plan = {
                        'months': data['months'],
                        'price': data['stars'],
                        'discount': data.get('discount', 0)
                    }
                    
        except Exception as e:
            logger.error(f'❌ Ошибка запроса к API calculate: {e}')
            await update.message.reply_text('❌ Ошибка соединения с сервером')
            return
        
        # Отправляем счет для оплаты Stars
        from telegram import LabeledPrice
        
        month_word = "месяц" if requested_months == 1 else ("месяца" if 2 <= requested_months <= 4 else "месяцев")
        
        title = f"⭐ Anonimka PRO - {requested_months} {month_word}"
        
        discount_text = ""
        if plan['discount'] > 0:
            discount_text = f" 🔥 Скидка {plan['discount']}%!\n"
        
        description = (
            f"Подписка Anonimka PRO на {requested_months} {month_word}\n"
            f"{discount_text}\n"
            "✅ Безлимитные сообщения\n"
            "✅ Приоритет в поиске\n"
            "✅ Расширенные фильтры\n"
            "✅ Видно кто лайкнул\n"
            "✅ Без рекламы\n"
            "✅ Эксклюзивный бейдж"
        )
        
        prices = [LabeledPrice(label=f"{requested_months} {month_word}", amount=plan['price'])]
        
        payload = f"premium_{requested_months}_{update.effective_user.id}_{int(asyncio.get_event_loop().time())}"
        
        try:
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=title,
                description=description,
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=prices
            )
            logger.info(f'💳 Invoice отправлен user {update.effective_user.id} для тарифа {requested_months} мес.')
        except Exception as e:
            logger.error(f'❌ Ошибка отправки invoice: {e}')
            await update.message.reply_text('❌ Ошибка создания счета\nПопробуйте позже или обратитесь в поддержку')
        
        return
    
    # Запрашиваем цены для всех месяцев через API
    prices_data = {}
    try:
        async with aiohttp.ClientSession() as session:
            for months in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
                async with session.get(
                    f'{API_BASE_URL}/api/premium/calculate?months={months}',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        prices_data[months] = {
                            'stars': data['stars'],
                            'discount': data.get('discount', 0)
                        }
    except Exception as e:
        logger.error(f'❌ Ошибка загрузки цен: {e}')
        # Фоллбэк к базовым ценам
        prices_data = {
            1: {'stars': 50, 'discount': 0},
            2: {'stars': 90, 'discount': 10},
            3: {'stars': 130, 'discount': 17},
            4: {'stars': 170, 'discount': 23},
            5: {'stars': 205, 'discount': 28},
            6: {'stars': 215, 'discount': 30},
            7: {'stars': 250, 'discount': 33},
            8: {'stars': 275, 'discount': 35},
            9: {'stars': 300, 'discount': 37},
            10: {'stars': 325, 'discount': 38},
            11: {'stars': 345, 'discount': 39},
            12: {'stars': 360, 'discount': 41}
        }
    
    premium_text = (
        "⭐ <b>Anonimka PRO</b>\n\n"
        "Получи максимум от анонимных знакомств!\n\n"
        "<b>Что входит в PRO:</b>\n"
        "✅ Безлимитные сообщения\n"
        "✅ Приоритет в поиске\n"
        "✅ Расширенные фильтры\n"
        "✅ Видно кто лайкнул профиль\n"
        "✅ Без рекламы\n"
        "✅ Эксклюзивный бейдж PRO\n\n"
        "<b>Выбери срок подписки:</b>"
    )
    
    # Формируем кнопки для всех 12 месяцев
    keyboard = []
    for months in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        price_info = prices_data.get(months, {'stars': 50, 'discount': 0})
        month_word = "месяц" if months == 1 else ("месяца" if 2 <= months <= 4 else "месяцев")
        
        discount_text = f" (-{price_info['discount']}%)" if price_info['discount'] > 0 else ""
        emoji = "🔥" if months == 1 else "⭐" if months == 3 else "💎" if months == 6 else "👑" if months == 12 else "📅"
        
        button_text = f"{emoji} {months} {month_word} - {price_info['stars']} Stars{discount_text}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"buy_pro_{months}")])
    
    keyboard.append([InlineKeyboardButton("❓ Как купить Stars", url="https://t.me/PremiumBot")])
    keyboard.append([InlineKeyboardButton("« Назад в меню", callback_data="main_menu")])
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            premium_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            premium_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def buy_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки PRO за Stars"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем количество месяцев из callback_data (buy_pro_3 -> 3)
    try:
        months = int(query.data.replace('buy_pro_', ''))
        if months < 1 or months > 12:
            await query.message.reply_text('❌ Неверный тариф. Выберите от 1 до 12 месяцев.')
            return
    except ValueError:
        await query.message.reply_text('❌ Ошибка определения тарифа')
        return
    
    # Запрашиваем цену с API /api/premium/calculate
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{API_BASE_URL}/api/premium/calculate?months={months}',
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.error(f'❌ API calculate вернул {resp.status}')
                    await query.message.reply_text('❌ Ошибка расчёта цены. Попробуйте позже.')
                    return
                
                data = await resp.json()
                if data.get('error'):
                    logger.error(f"❌ API calculate error: {data['error']}")
                    await query.message.reply_text('❌ Ошибка расчёта цены')
                    return
                
                # Формируем plan из данных API
                plan = {
                    'months': data['months'],
                    'price': data['stars'],
                    'title': f"{months} мес." if months != 1 else "1 месяц",
                    'discount': data.get('discount', 0),
                    'kzt': round(data.get('kzt_equivalent', 0))
                }
                
    except Exception as e:
        logger.error(f'❌ Ошибка запроса к API calculate: {e}')
        await query.message.reply_text('❌ Ошибка соединения с сервером')
        return
    
    # Отправляем счет для оплаты Stars
    from telegram import LabeledPrice
    
    # Склонение слова "месяц"
    month_word = "месяц" if months == 1 else ("месяца" if 2 <= months <= 4 else "месяцев")
    
    title = f"⭐ Anonimka PRO - {months} {month_word}"
    
    # Добавляем информацию о скидке в description
    discount_text = ""
    if plan['discount'] > 0:
        discount_text = f" 🔥 Скидка {plan['discount']}%!\n"
    
    description = (
        f"Подписка Anonimka PRO на {months} {month_word}\n"
        f"{discount_text}\n"
        "✅ Безлимитные сообщения\n"
        "✅ Приоритет в поиске\n"
        "✅ Расширенные фильтры\n"
        "✅ Видно кто лайкнул\n"
        "✅ Без рекламы\n"
        "✅ Эксклюзивный бейдж"
    )
    
    prices = [LabeledPrice(label=plan['title'], amount=plan['price'])]
    
    # Payload для идентификации платежа
    payload = f"premium_{plan['months']}_{query.from_user.id}_{int(asyncio.get_event_loop().time())}"
    
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Пустая строка для Stars
            currency="XTR",  # Валюта Telegram Stars
            prices=prices
        )
        logger.info(f'💳 Invoice отправлен user {query.from_user.id} для тарифа {plan["months"]} мес.')
    except Exception as e:
        logger.error(f'❌ Ошибка отправки invoice: {e}')
        await query.message.reply_text(
            '❌ Ошибка создания счета\n'
            'Попробуйте позже или обратитесь в поддержку'
        )

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реферальная программа - получить ссылку и статистику"""
    user = update.effective_user
    
    logger.info(f"🔗 /referral от user {user.id}")
    
    try:
        # Получаем статистику из API
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{API_BASE_URL}/api/referrals?userId={user.id}',
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    total = data.get('total', 0)
                    rewarded = data.get('rewarded', 0)
                    pending = data.get('pending', 0)
                    
                    # Генерируем реферальную ссылку
                    bot_username = (await context.bot.get_me()).username
                    ref_link = f"https://t.me/{bot_username}?startapp=ref_{user.id}"
                    
                    text = (
                        f"🎁 <b>Пригласи друга - получи 30 дней PRO!</b>\n\n"
                        f"<b>Твоя реферальная ссылка:</b>\n"
                        f"<code>{ref_link}</code>\n\n"
                        f"<b>Как это работает:</b>\n"
                        f"1️⃣ Отправь ссылку другу\n"
                        f"2️⃣ Друг переходит и <b>создаёт анкету</b>\n"
                        f"3️⃣ Ты получаешь 30 дней PRO! 🎉\n\n"
                        f"👥 Приглашено: <b>{total}</b> друзей\n"
                        f"✅ Награда получена: <b>{rewarded}</b> раз\n"
                        f"⏳ В ожидании: <b>{pending}</b>\n\n"
                        f"⚠️ <i>Акция действует ОДИН РАЗ для новых пользователей</i>\n"
                        f"💡 <i>Если ты уже получал PRO ранее, новые рефералы не дадут награду</i>"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton(
                            "📤 Поделиться ссылкой", 
                            url=f"https://t.me/share/url?url={ref_link}&text=Попробуй Anonimka - анонимные знакомства! Мы оба получим PRO на месяц 🎁"
                        )],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                    ]
                    
                    await update.message.reply_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                else:
                    logger.error(f'❌ API /referrals вернул статус {resp.status}')
                    await update.message.reply_text(
                        '❌ Ошибка получения статистики\n'
                        'Попробуйте позже'
                    )
    except Exception as e:
        logger.error(f"❌ Ошибка /referral: {e}")
        await update.message.reply_text(
            '❌ Ошибка обработки команды\n'
            'Попробуйте позже или обратитесь в поддержку'
        )

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик успешного платежа Stars"""
    payment = update.message.successful_payment
    user = update.effective_user
    
    # Парсим payload
    try:
        payload_parts = payment.invoice_payload.split('_')
        months = int(payload_parts[1])
    except:
        months = 1
    
    logger.info(f'💰 Успешный платеж: {user.id} ({user.username}) купил PRO на {months} мес.')
    
    # Активируем PRO через API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/premium/activate',
                json={
                    'telegram_id': user.id,
                    'months': months,
                    'transaction_id': payment.telegram_payment_charge_id,
                    'amount': payment.total_amount
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    await update.message.reply_text(
                        f'🎉 <b>Поздравляем, {user.first_name}!</b>\n\n'
                        f'⭐ PRO подписка активирована на <b>{months} мес.</b>\n\n'
                        f'✨ Все функции уже доступны в приложении!\n\n'
                        f'💡 <i>Хочешь заработать? Стань партнером и получай 40% с покупок друзей! '
                        f'Команда /affiliate</i>\n\n'
                        f'Спасибо что с нами! ❤️',
                        parse_mode='HTML'
                    )
                    logger.info(f'✅ PRO активирован для {user.id} на {months} мес.')
                else:
                    error_text = await resp.text()
                    logger.error(f'❌ API вернул {resp.status}: {error_text}')
                    await update.message.reply_text(
                        '❌ Ошибка активации PRO\n\n'
                        'Платеж получен, но возникла техническая ошибка.\n'
                        'Напишите в поддержку: @Vorobey_444\n\n'
                        f'ID транзакции: {payment.telegram_payment_charge_id}'
                    )
    except asyncio.TimeoutError:
        logger.error(f'❌ Timeout активации PRO для {user.id}')
        await update.message.reply_text(
            '⏱️ Превышено время ожидания\n\n'
            'Платеж получен, PRO будет активирован в течение 5 минут.\n'
            'Если этого не произошло - напишите @Vorobey_444\n\n'
            f'ID транзакции: {payment.telegram_payment_charge_id}'
        )
    except Exception as e:
        logger.error(f'❌ Ошибка активации PRO: {e}')
        await update.message.reply_text(
            '❌ Техническая ошибка активации\n\n'
            'Платеж получен успешно!\n'
            'Напишите в поддержку для активации: @Vorobey_444\n\n'
            f'ID транзакции: {payment.telegram_payment_charge_id}'
        )

# Команда публикации приветственного поста в канал
async def post_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Опубликовать приветственный пост в канале (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    channel_username = "@anonimka_kz"
    
    welcome_text = (
        "👋 Добро пожаловать в Anonimka!\n\n"
        "Тут не Tinder и не Badoo.\n"
        "Тут пишут как думают. Без масок.\n\n"
        "🎭 Анонимность гарантирована\n"
        "📍 Знакомства в твоем городе\n"
        "🔥 Никаких понтов\n\n"
        "Готов попробовать? 👇"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать знакомства", url="https://t.me/anonimka_kz_bot")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        message = await context.bot.send_message(
            chat_id=channel_username,
            text=welcome_text,
            reply_markup=reply_markup
        )
        await update.message.reply_text(
            f'✅ Приветственный пост опубликован в канале!\n'
            f'ID поста: {message.message_id}'
        )
        logger.info(f'✅ Приветственный пост опубликован в {channel_username}')
    except Exception as e:
        logger.error(f'❌ Ошибка публикации в канал: {e}')
        await update.message.reply_text(
            f'❌ Ошибка публикации в канал:\n{str(e)}\n\n'
            f'Убедитесь что:\n'
            f'1. Бот добавлен в администраторы канала\n'
            f'2. У бота есть право "Публикация сообщений"'
        )

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем периодическое обновление описания (каждый час)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            lambda context: update_short_description(context.application),
            interval=3600,  # 3600 секунд = 1 час
            first=3600  # Первый запуск через час после старта
        )
        logger.info("✅ Запланировано обновление описания каждый час")
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("post_welcome", post_welcome))
    
    # Команды розыгрыша
    application.add_handler(CommandHandler("start_giveaway", start_giveaway))
    application.add_handler(CommandHandler("participate", participate_giveaway))
    application.add_handler(CommandHandler("giveaway_stats", giveaway_stats))
    application.add_handler(CommandHandler("pick_winner", pick_winner))
    application.add_handler(CommandHandler("end_giveaway", end_giveaway))
    application.add_handler(CommandHandler("post_giveaway", post_giveaway))
    
    # Команды PRO подписки
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("referral", referral_command))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Обработчики callback
    application.add_handler(CallbackQueryHandler(menu_command, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(about_command, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(contacts_command, pattern="^contacts$"))
    application.add_handler(CallbackQueryHandler(referral_command_callback, pattern="^referral$"))
    application.add_handler(CallbackQueryHandler(premium_command, pattern="^premium$"))
    application.add_handler(CallbackQueryHandler(buy_premium_callback, pattern="^buy_pro_"))
    application.add_handler(CallbackQueryHandler(participate_giveaway_callback, pattern="^participate_giveaway$"))
    application.add_handler(CallbackQueryHandler(open_chat_callback, pattern="^openchat_"))
    application.add_handler(CallbackQueryHandler(show_my_chats_callback, pattern="^show_my_chats$"))
    
    # Обработчики модерации (только для админа)
    application.add_handler(CallbackQueryHandler(moderate_ban_user, pattern="^ban_"))
    application.add_handler(CallbackQueryHandler(moderate_reject_report, pattern="^reject_"))
    application.add_handler(CommandHandler("reports", reports_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Глобальный обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Настраиваем Menu Button перед запуском
    import asyncio
    asyncio.get_event_loop().run_until_complete(setup_menu_button(application))
    
    # Запускаем бота
    print("🤖 Бот запущен и работает...")
    print("✅ Menu Button настроен")
    print("✅ Логируются только важные события")
    print("─" * 40)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
