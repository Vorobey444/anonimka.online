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
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/anonimka_kz")]
    ]
    
    # Добавляем кнопку розыгрыша если он активен
    global giveaway_active
    if giveaway_active:
        keyboard.append([InlineKeyboardButton("🎁 Участвовать в розыгрыше", callback_data="participate_giveaway")])
    
    keyboard.extend([
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
        [
            InlineKeyboardButton("📋 Правила", url=f"{API_BASE_URL}/TERMS_OF_SERVICE.md"),
            InlineKeyboardButton("🔒 Политика", url=f"{API_BASE_URL}/PRIVACY_POLICY.md")
        ],
        [InlineKeyboardButton("💬 Тех.поддержка", url="https://t.me/Vorobey_444")],
        [InlineKeyboardButton("🤝 Реклама и сотрудничество", callback_data="advertising")]
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
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/anonimka_kz")]
    ]
    
    # Добавляем кнопку розыгрыша если он активен
    global giveaway_active
    if giveaway_active:
        keyboard.append([InlineKeyboardButton("🎁 Участвовать в розыгрыше", callback_data="participate_giveaway")])
    
    keyboard.extend([
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
        [
            InlineKeyboardButton("📋 Правила", url=f"{API_BASE_URL}/TERMS_OF_SERVICE.md"),
            InlineKeyboardButton("🔒 Политика", url=f"{API_BASE_URL}/PRIVACY_POLICY.md")
        ],
        [InlineKeyboardButton("💬 Тех.поддержка", url="https://t.me/Vorobey_444")],
        [InlineKeyboardButton("🤝 Реклама и сотрудничество", callback_data="advertising")]
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

async def advertising_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о рекламе и сотрудничестве"""
    query = update.callback_query
    await query.answer()
    
    advertising_text = (
        "📢 <b>Реклама и сотрудничество</b>\n\n"
        
        "Заинтересованы в размещении рекламы или сотрудничестве?\n"
        "Мы открыты к предложениям!\n\n"
        
        "🔹 <b>Контакты для связи:</b>\n"
        "📧 Email: aleksey@vorobey444.ru\n"
        "💬 Telegram: @Vorobey_444\n\n"
        
        "Свяжитесь с нами для обсуждения деталей и условий сотрудничества."
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=advertising_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
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
        '3️⃣ Написать боту команду /participate\n\n'
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
        "2️⃣ Создай анонимный профиль в боте\n"
        "3️⃣ Напиши боту команду /participate\n\n"
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
    
    # Обработчики callback
    application.add_handler(CallbackQueryHandler(menu_command, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(advertising_command, pattern="^advertising$"))
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
