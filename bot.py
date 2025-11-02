"""
Бот для анонимной доски объявлений с системой приглашений в чат
- User A отправляет первое сообщение через WebApp
- User B получает приглашение и может принять/отклонить
- После принятия создается приватный анонимный чат
- Возможность блокировки собеседника с любой стороны
"""

import logging
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8105244538:AAFosyTcD8uPuwArnYgBO-IVeSThzuxbLhY"
API_BASE_URL = "https://anonimka.kz"
VERCEL_API_URL = "https://anonimka.online/api"
SUPABASE_URL = "https://vcxknlntcvcdowdohblr.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjeGtubG50Y3ZjZG93ZG9oYmxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAwMzExNTcsImV4cCI6MjA0NTYwNzE1N30.GfHTJ6d54L3c29D_FeQRJf2-5OlTATfO-QyQ9mGpbao"

# Хранилища данных
# sent_messages[sender_id][ad_id] = True - отслеживание отправленных сообщений
# chat_invites[invite_id] = {sender, recipient, ad_id, message, timestamp}
# active_chats[chat_id] = {user1, user2, ad_id, created_at, blocked_by: None/user_id}
# user_chats[user_id] = [chat_id1, chat_id2, ...]


# ===== ГЛАВНОЕ МЕНЮ =====

async def get_user_nickname(telegram_id: int) -> str:
    """Получает никнейм пользователя из Supabase"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            url = f"{SUPABASE_URL}/rest/v1/ads?telegram_id=eq.{telegram_id}&select=nickname&order=created_at.desc&limit=1"
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0 and data[0].get('nickname'):
                        nickname = data[0]['nickname']
                        logger.info(f"Получен никнейм для {telegram_id}: {nickname}")
                        return nickname
                    else:
                        logger.info(f"Никнейм не найден для {telegram_id}, используем 'Аноним'")
                        return "Аноним"
                else:
                    logger.warning(f"Ошибка получения никнейма: {response.status}")
                    return "Аноним"
    except Exception as e:
        logger.error(f"Ошибка получения никнейма для {telegram_id}: {e}")
        return "Аноним"


def get_main_menu_keyboard():
    """Возвращает основную клавиатуру меню"""
    keyboard = [
        [KeyboardButton("🚀 Открыть приложение"), KeyboardButton("💬 Мои чаты")],
        [KeyboardButton("📋 Мои объявления"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    menu_text = (
        "🌟 Главное меню\n\n"
        "🚀 Открыть приложение - просмотр объявлений\n"
        "💬 Мои чаты - список активных диалогов\n"
        "📋 Мои объявления - управление объявлениями\n"
        "❓ Помощь - инструкция по использованию"
    )
    
    await update.message.reply_text(
        menu_text,
        reply_markup=get_main_menu_keyboard()
    )


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок меню"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    user_id = update.message.from_user.id
    
    if text == "🚀 Открыть приложение":
        # Открываем WebApp через inline кнопку (передаёт initData автоматически)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))]
        ])
        await update.message.reply_text(
            "🌐 Нажмите кнопку для открытия приложения:",
            reply_markup=keyboard
        )
    
    elif text == "💬 Мои чаты":
        # Показываем список чатов
        await my_chats(update, context)
    
    elif text == "📋 Мои объявления":
        # Открываем раздел "Мои объявления" в WebApp
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Открыть мои объявления", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/#myads"))]
        ])
        await update.message.reply_text(
            "📋 Управляйте своими объявлениями:",
            reply_markup=keyboard
        )
    
    elif text == "❓ Помощь":
        help_text = (
            "❓ Помощь по использованию бота\n\n"
            "🌐 Сайт: anonimka.kz\n\n"
            "📝 Как создать объявление:\n"
            "1. Нажмите '🚀 Открыть приложение'\n"
            "2. Заполните форму с описанием\n"
            "3. Ваше объявление опубликовано!\n\n"
            "💬 Как написать автору:\n"
            "1. Откройте объявление\n"
            "2. Нажмите 'Написать автору'\n"
            "3. Отправьте сообщение\n"
            "4. Автор получит уведомление здесь\n"
            "5. Он может создать приватный чат\n\n"
            "🔒 Ваши чаты полностью анонимны\n"
            "🚫 Используйте /block чтобы заблокировать собеседника\n\n"
            "Команды:\n"
            "/start - Главное меню\n"
            "/mychats - Список чатов\n"
            "/block - Заблокировать текущий чат"
        )
        await update.message.reply_text(help_text)


# ===== КОМАНДА START =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - отображает приветствие и кнопку открытия приложения"""
    if not update.message or not update.message.from_user:
        return
        
    user_id = update.message.from_user.id
    user = update.message.from_user
    
    # Проверяем, есть ли параметр авторизации (для QR-кода)
    if context.args and len(context.args) > 0:
        auth_param = context.args[0]
        
        # Если это auth token из QR-кода
        if auth_param.startswith('auth_'):
            logger.info(f"QR-авторизация от пользователя {user_id}, token: {auth_param}")
            
            # Формируем данные пользователя
            user_data = {
                'id': user_id,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'username': user.username or '',
            }
            
            # Отправляем данные на сервер для синхронизации с браузером
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{API_BASE_URL}/api/auth",
                        json={'token': auth_param, 'user': user_data},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"✅ Данные отправлены на сервер для токена {auth_param}")
                        else:
                            logger.error(f"❌ Ошибка отправки на сервер: {response.status}")
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке данных на сервер: {e}")
            
            # Отправляем подтверждение пользователю
            await update.message.reply_text(
                f"✅ Авторизация успешна!\n\n"
                f"👤 {user.first_name}\n"
                f"💻 Окно авторизации на компьютере закроется автоматически\n"
                f"🌐 Вы также можете открыть сайт в Telegram\n\n"
                f"Теперь вы можете пользоваться сайтом как с компьютера, так и с телефона!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 Открыть сайт в Telegram", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))]
                ])
            )
            
            logger.info(f"QR-авторизация завершена для {user_id}, данные: {user_data}")
            return
    
    logger.info(f"Команда /start от пользователя {user_id}")
    
    # Инициализируем хранилища данных
    if 'sent_messages' not in context.bot_data:
        context.bot_data['sent_messages'] = {}
    if 'chat_invites' not in context.bot_data:
        context.bot_data['chat_invites'] = {}
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = {}
    if 'user_chats' not in context.bot_data:
        context.bot_data['user_chats'] = {}
    
    # Приветственное сообщение с меню
    welcome_message = (
        "🌟 Добро пожаловать в анонимную доску объявлений!\n\n"
        "🌍 Сайт: anonimka.kz\n\n"
        "Используйте кнопки меню ниже для навигации 👇"
    )
    
    try:
        await update.message.reply_text(
            welcome_message,
            reply_markup=get_main_menu_keyboard()
        )
        logger.info("Приветственное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")


# ===== ОТПРАВКА ПЕРВОГО СООБЩЕНИЯ =====

async def send_first_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает первое сообщение от User A к User B через WebApp
    Формат callback: first_msg_{ad_id}_{author_tg_id}_{message_text}
    Или принимает JSON через WebApp.data
    """
    query = update.callback_query
    if query:
        await query.answer()
        # Обработка через callback
        try:
            parts = query.data.split('_', 3)
            if len(parts) < 4:
                await context.bot.send_message(query.from_user.id, "❌ Неверный формат запроса")
                return
            
            ad_id = parts[1]
            author_tg_id = int(parts[2])
            message_text = parts[3]
            sender_tg_id = query.from_user.id
            
        except Exception as e:
            logger.error(f"Ошибка парсинга callback: {e}")
            return
    else:
        # Обработка через WebApp data
        if not update.message or not update.message.web_app_data:
            return
        
        import json
        try:
            data = json.loads(update.message.web_app_data.data)
            ad_id = data.get('ad_id')
            author_tg_id = int(data.get('author_tg_id'))
            message_text = data.get('message')
            sender_tg_id = update.message.from_user.id
        except Exception as e:
            logger.error(f"Ошибка парсинга WebApp data: {e}")
            await update.message.reply_text("❌ Ошибка обработки данных")
            return
    
    # Проверка: нельзя писать самому себе
    if sender_tg_id == author_tg_id:
        msg = "❌ Вы не можете написать сами себе"
        if query:
            await context.bot.send_message(sender_tg_id, msg)
        else:
            await update.message.reply_text(msg)
        return
    
    # Инициализация хранилищ
    if 'sent_messages' not in context.bot_data:
        context.bot_data['sent_messages'] = {}
    
    # Проверка: можно отправить только одно сообщение на объявление
    if sender_tg_id not in context.bot_data['sent_messages']:
        context.bot_data['sent_messages'][sender_tg_id] = {}
    
    if ad_id in context.bot_data['sent_messages'][sender_tg_id]:
        msg = "⚠️ Вы уже отправили сообщение на это объявление. Ожидайте ответа."
        if query:
            await context.bot.send_message(sender_tg_id, msg)
        else:
            await update.message.reply_text(msg)
        return
    
    # Сохраняем, что сообщение отправлено
    context.bot_data['sent_messages'][sender_tg_id][ad_id] = True
    
    # Создаем уникальный ID приглашения
    invite_id = f"invite_{sender_tg_id}_{author_tg_id}_{ad_id}_{datetime.now().timestamp()}"
    
    # Сохраняем приглашение
    if 'chat_invites' not in context.bot_data:
        context.bot_data['chat_invites'] = {}
    
    context.bot_data['chat_invites'][invite_id] = {
        'sender': sender_tg_id,
        'recipient': author_tg_id,
        'ad_id': ad_id,
        'message': message_text,
        'timestamp': datetime.now().isoformat()
    }
    
    # Отправляем приглашение автору объявления
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{invite_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{invite_id}")
        ]
    ])
    
    # Получаем никнейм отправителя
    sender_nickname = await get_user_nickname(sender_tg_id)
    
    try:
        await context.bot.send_message(
            author_tg_id,
            f"� Новое сообщение на ваше объявление #{ad_id}!\n\n"
            f"От: {sender_nickname}\n\n"
            f"📩 Сообщение:\n{message_text}\n\n"
            f"Принять запрос на анонимный чат?",
            reply_markup=keyboard
        )
        
        # Уведомляем отправителя
        confirmation = (
            "✅ Сообщение отправлено!\n\n"
            "Ожидайте, пока автор объявления примет запрос на чат."
        )
        if query:
            await context.bot.send_message(sender_tg_id, confirmation)
        else:
            await update.message.reply_text(confirmation)
        
        logger.info(f"Приглашение {invite_id} отправлено от {sender_tg_id} к {author_tg_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки приглашения: {e}")
        msg = "⚠️ Не удалось отправить сообщение. Возможно, пользователь заблокировал бота."
        if query:
            await context.bot.send_message(sender_tg_id, msg)
        else:
            await update.message.reply_text(msg)


# ===== ПРИНЯТИЕ/ОТКЛОНЕНИЕ ПРИГЛАШЕНИЯ =====

async def accept_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принимает приглашение в чат"""
    query = update.callback_query
    if not query or not query.data:
        return
    
    await query.answer()
    
    invite_id = query.data.replace("accept_", "")
    chat_invites = context.bot_data.get('chat_invites', {})
    
    if invite_id not in chat_invites:
        await context.bot.send_message(query.from_user.id, "❌ Приглашение не найдено или уже обработано")
        return
    
    invite = chat_invites[invite_id]
    sender_id = invite['sender']
    recipient_id = invite['recipient']
    ad_id = invite['ad_id']
    first_message = invite['message']
    
    # Создаем чат
    chat_id = f"{min(sender_id, recipient_id)}_{max(sender_id, recipient_id)}_{ad_id}"
    
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = {}
    if 'user_chats' not in context.bot_data:
        context.bot_data['user_chats'] = {}
    
    context.bot_data['active_chats'][chat_id] = {
        'user1': sender_id,
        'user2': recipient_id,
        'ad_id': ad_id,
        'created_at': datetime.now().isoformat(),
        'blocked_by': None
    }
    
    # Добавляем чат в список чатов пользователей
    for user_id in [sender_id, recipient_id]:
        if user_id not in context.bot_data['user_chats']:
            context.bot_data['user_chats'][user_id] = []
        if chat_id not in context.bot_data['user_chats'][user_id]:
            context.bot_data['user_chats'][user_id].append(chat_id)
    
    # Удаляем приглашение
    del chat_invites[invite_id]
    
    # Уведомляем получателя (автора объявления)
    await context.bot.send_message(
        recipient_id,
        f"✅ Анонимный чат создан!\n\n"
        f"📋 Объявление: #{ad_id}\n"
        f"� Первое сообщение: {first_message}\n\n"
        f"💬 Теперь вы можете отправлять сообщения.\n\n"
        f"Команды:\n"
        f"/mychats - список активных чатов\n"
        f"/block - заблокировать собеседника"
    )
    
    # Уведомляем отправителя
    try:
        await context.bot.send_message(
            sender_id,
            f"✅ Ваш запрос на чат принят!\n\n"
            f"📋 Объявление: #{ad_id}\n\n"
            f"💬 Теперь вы можете общаться анонимно.\n\n"
            f"Команды:\n"
            f"/mychats - список активных чатов\n"
            f"/block - заблокировать собеседника"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить отправителя: {e}")
    
    logger.info(f"Чат {chat_id} создан между {sender_id} и {recipient_id}")


async def create_chat_from_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Создает приватный чат из уведомления (callback от API)
    Формат: create_chat_{ad_id}_{sender_tg_id}
    """
    query = update.callback_query
    if not query or not query.data:
        return
    
    await query.answer()
    
    try:
        # Парсим callback data: create_chat_{ad_id}_{sender_tg_id}_{receiver_tg_id}
        parts = query.data.split('_')
        if len(parts) < 5:
            await context.bot.send_message(query.from_user.id, "❌ Неверный формат запроса")
            return
        
        ad_id = parts[2]
        sender_id = int(parts[3])
        recipient_id = int(parts[4])  # ID получателя из callback data
        current_user = query.from_user.id  # Кто нажал кнопку
        
        # Проверка: кнопку должен нажать получатель
        if current_user != recipient_id:
            await context.bot.send_message(current_user, "❌ Эта кнопка предназначена для другого пользователя")
            return
        
        # Проверка: нельзя создать чат с самим собой
        if sender_id == recipient_id:
            await context.bot.send_message(recipient_id, "❌ Ошибка: нельзя создать чат с самим собой")
            return
        
        # Создаем уникальный ID чата
        chat_id = f"{min(sender_id, recipient_id)}_{max(sender_id, recipient_id)}_{ad_id}"
        
        # Инициализация хранилищ
        if 'active_chats' not in context.bot_data:
            context.bot_data['active_chats'] = {}
        if 'user_chats' not in context.bot_data:
            context.bot_data['user_chats'] = {}
        
        # Проверяем, не существует ли уже чат
        if chat_id in context.bot_data['active_chats']:
            existing_chat = context.bot_data['active_chats'][chat_id]
            if existing_chat.get('blocked_by'):
                await context.bot.send_message(
                    recipient_id, 
                    "❌ Этот чат был заблокирован. Невозможно возобновить общение."
                )
                return
            else:
                await context.bot.send_message(
                    recipient_id,
                    f"✅ Чат уже существует!\n\n"
                    f"📋 Объявление: #{ad_id}\n\n"
                    f"💬 Можете продолжить общение.\n\n"
                    f"Команды:\n"
                    f"/mychats - список активных чатов\n"
                    f"/block - заблокировать собеседника"
                )
                return
        
        # Создаем новый чат
        context.bot_data['active_chats'][chat_id] = {
            'user1': sender_id,
            'user2': recipient_id,
            'ad_id': ad_id,
            'created_at': datetime.now().isoformat(),
            'blocked_by': None
        }
        
        # Добавляем чат в список чатов пользователей
        for user_id in [sender_id, recipient_id]:
            if user_id not in context.bot_data['user_chats']:
                context.bot_data['user_chats'][user_id] = []
            if chat_id not in context.bot_data['user_chats'][user_id]:
                context.bot_data['user_chats'][user_id].append(chat_id)
        
        # Уведомляем автора объявления (получателя)
        await context.bot.send_message(
            recipient_id,
            f"✅ Приватный чат создан!\n\n"
            f"📋 Объявление: #{ad_id}\n\n"
            f"💬 Теперь вы можете отправлять сообщения анонимно.\n"
            f"Просто напишите сообщение, и оно будет доставлено собеседнику.\n\n"
            f"Команды:\n"
            f"/mychats - список активных чатов\n"
            f"/block - заблокировать собеседника"
        )
        
        # Уведомляем отправителя
        try:
            await context.bot.send_message(
                sender_id,
                f"✅ Автор объявления #{ad_id} принял ваш запрос!\n\n"
                f"💬 Приватный чат создан. Можете начать общение.\n"
                f"Просто напишите сообщение.\n\n"
                f"Команды:\n"
                f"/mychats - список активных чатов\n"
                f"/block - заблокировать собеседника"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить отправителя {sender_id}: {e}")
        
        logger.info(f"Чат {chat_id} создан из уведомления между {sender_id} и {recipient_id}")
    
    except Exception as e:
        logger.error(f"Ошибка создания чата из уведомления: {e}")
        if query and query.from_user:
            await context.bot.send_message(query.from_user.id, "❌ Ошибка при создании чата. Попробуйте позже.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий - пересылает их в активный чат"""
    if not update.message or not update.message.photo or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]  # Берём самое большое фото
    caption = update.message.caption or ""
    
    # Получаем активные чаты пользователя
    user_chat_ids = context.bot_data.get('user_chats', {}).get(user_id, [])
    active_chats_data = context.bot_data.get('active_chats', {})
    
    # Фильтруем активные и незаблокированные чаты
    available_chats = []
    for chat_id in user_chat_ids:
        if chat_id in active_chats_data:
            chat = active_chats_data[chat_id]
            if not chat.get('blocked_by'):
                available_chats.append((chat_id, chat))
    
    if not available_chats:
        # Нет активных чатов
        await update.message.reply_text(
            "📭 У вас нет активных чатов\n\n"
            "Откройте приложение для поиска объявлений 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))]
            ])
        )
        return
    
    # Проверяем, есть ли активный выбранный чат
    active_chat_id = context.user_data.get('active_chat_id') if context.user_data else None
    
    # Если есть активный чат и он доступен - отправляем туда
    if active_chat_id and active_chat_id in active_chats_data:
        chat = active_chats_data[active_chat_id]
        if not chat.get('blocked_by') and active_chat_id in [c[0] for c in available_chats]:
            await _send_photo_to_chat(context, user_id, active_chat_id, chat, photo.file_id, caption)
            await update.message.reply_text("✅ Фото отправлено в активный чат")
            return
    
    # Если один активный чат - отправляем сразу и делаем его активным
    if len(available_chats) == 1:
        chat_id, chat = available_chats[0]
        if context.user_data is not None:
            context.user_data['active_chat_id'] = chat_id
        await _send_photo_to_chat(context, user_id, chat_id, chat, photo.file_id, caption)
        await update.message.reply_text("✅ Фото отправлено!")
        return
    
    # Если несколько чатов и нет активного - сохраняем фото и предлагаем выбрать
    if 'pending_photos' not in context.bot_data:
        context.bot_data['pending_photos'] = {}
    
    context.bot_data['pending_photos'][user_id] = {
        'file_id': photo.file_id,
        'caption': caption
    }
    
    # Создаем кнопки выбора чата
    keyboard = []
    for chat_id, chat in available_chats:
        ad_id = chat.get('ad_id', 'N/A')
        keyboard.append([
            InlineKeyboardButton(
                f"Отправить в чат по объявлению #{ad_id}",
                callback_data=f"sendphoto_{chat_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("📋 Мои чаты", callback_data="show_my_chats")
    ])
    
    await update.message.reply_text(
        "📷 Выберите чат для отправки фото:\n\n"
        "💡 Совет: используйте /my_chats чтобы выбрать активный чат,\n"
        "тогда все фото будут автоматически отправляться туда.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_photo_to_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для отправки фото в выбранный чат"""
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.data.replace("sendphoto_", "")
    
    # Получаем сохранённое фото
    pending_photos = context.bot_data.get('pending_photos', {})
    photo_data = pending_photos.get(user_id)
    
    if not photo_data:
        await context.bot.send_message(user_id, "❌ Фото не найдено. Отправьте заново.")
        return
    
    # Получаем информацию о чате
    active_chats = context.bot_data.get('active_chats', {})
    
    if chat_id not in active_chats:
        await context.bot.send_message(user_id, "❌ Чат не найден")
        return
    
    chat = active_chats[chat_id]
    
    # Проверяем, не заблокирован ли чат
    if chat.get('blocked_by'):
        await context.bot.send_message(user_id, "❌ Этот чат заблокирован")
        return
    
    # Отправляем фото
    await _send_photo_to_chat(
        context, user_id, chat_id, chat, 
        photo_data['file_id'], photo_data['caption']
    )
    await context.bot.send_message(user_id, "✅ Фото отправлено!")
    
    # Удаляем сохранённое фото
    del pending_photos[user_id]


async def open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Открывает приватный чат (показывает информацию о чате)
    Формат callback: open_chat_{chat_id}
    """
    query = update.callback_query
    if not query or not query.data:
        return
    
    await query.answer()
    
    try:
        # Парсим callback data: open_chat_{chat_id}
        chat_id = query.data.replace("open_chat_", "")
        user_id = query.from_user.id
        
        # Загружаем чат из API (Supabase)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{VERCEL_API_URL}/create-chat?chat_id={chat_id}") as response:
                if response.status != 200:
                    await context.bot.send_message(
                        user_id,
                        "❌ Ошибка загрузки чата. Попробуйте позже."
                    )
                    return
                
                result = await response.json()
                
                if not result.get('success') or not result.get('data'):
                    await context.bot.send_message(
                        user_id,
                        "❌ Чат не найден в базе данных."
                    )
                    return
                
                chats = result['data']
                if not chats or len(chats) == 0:
                    await context.bot.send_message(
                        user_id,
                        "❌ Чат не найден. Возможно он был удален."
                    )
                    return
                
                chat = chats[0]
        
        # Проверяем, что пользователь участник чата
        user1_id = chat.get('user1_tg_id')
        user2_id = chat.get('user2_tg_id')
        
        if user_id not in [user1_id, user2_id]:
            await context.bot.send_message(
                user_id,
                "❌ У вас нет доступа к этому чату"
            )
            return
        
        # Проверяем, не заблокирован ли чат
        if not chat.get('is_active'):
            await context.bot.send_message(
                user_id,
                "❌ Этот чат заблокирован"
            )
            return
        
        # Определяем собеседника
        other_user_id = user2_id if user_id == user1_id else user1_id
        ad_id = chat.get('ad_id', 'неизвестно')
        
        # Сохраняем чат в bot_data для отправки сообщений
        if 'active_chats' not in context.bot_data:
            context.bot_data['active_chats'] = {}
        if 'user_chats' not in context.bot_data:
            context.bot_data['user_chats'] = {}
        
        # Добавляем в память бота если еще нет
        if chat_id not in context.bot_data['active_chats']:
            context.bot_data['active_chats'][chat_id] = {
                'user1': user1_id,
                'user2': user2_id,
                'ad_id': ad_id,
                'created_at': chat.get('created_at'),
                'blocked_by': chat.get('blocked_by')
            }
            
            # Добавляем в списки чатов пользователей
            for uid in [user1_id, user2_id]:
                if uid not in context.bot_data['user_chats']:
                    context.bot_data['user_chats'][uid] = []
                if chat_id not in context.bot_data['user_chats'][uid]:
                    context.bot_data['user_chats'][uid].append(chat_id)
        
        # Отправляем информацию о чате
        message = (
            f"💬 <b>Приватный чат открыт</b>\n\n"
            f"📋 Объявление: #{ad_id}\n"
            f"👤 Собеседник: ID {other_user_id}\n\n"
            f"✍️ Напишите сообщение, и оно будет доставлено собеседнику.\n\n"
            f"<b>Команды:</b>\n"
            f"/mychats - список активных чатов\n"
            f"/block - заблокировать этот чат"
        )
        
        # Кнопки для быстрых действий
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))],
            [InlineKeyboardButton("🚫 Заблокировать чат", callback_data=f"block_{chat_id}")]
        ])
        
        await context.bot.send_message(
            user_id,
            message,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        logger.info(f"Пользователь {user_id} открыл чат {chat_id} из Supabase")
        
    except Exception as e:
        logger.error(f"Ошибка открытия чата: {e}")
        await context.bot.send_message(
            query.from_user.id,
            "❌ Ошибка при открытии чата. Попробуйте позже."
        )


async def decline_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отклоняет приглашение в чат"""
    query = update.callback_query
    if not query or not query.data:
        return
    
    await query.answer()
    
    invite_id = query.data.replace("decline_", "")
    chat_invites = context.bot_data.get('chat_invites', {})
    
    if invite_id not in chat_invites:
        await context.bot.send_message(query.from_user.id, "❌ Приглашение не найдено или уже обработано")
        return
    
    invite = chat_invites[invite_id]
    sender_id = invite['sender']
    ad_id = invite['ad_id']
    
    # Удаляем приглашение
    del chat_invites[invite_id]
    
    # Возвращаем возможность отправить сообщение еще раз
    if sender_id in context.bot_data.get('sent_messages', {}):
        if ad_id in context.bot_data['sent_messages'][sender_id]:
            del context.bot_data['sent_messages'][sender_id][ad_id]
    
    # Уведомляем получателя
    await context.bot.send_message(
        query.from_user.id,
        f"❌ Запрос на чат отклонен"
    )
    
    # НЕ уведомляем отправителя об отклонении (для анонимности)
    logger.info(f"Приглашение {invite_id} отклонено")




# ===== УПРАВЛЕНИЕ ЧАТАМИ =====

async def my_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список активных чатов пользователя с возможностью переключения"""
    if not update.message or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    user_chat_ids = context.bot_data.get('user_chats', {}).get(user_id, [])
    active_chats_data = context.bot_data.get('active_chats', {})
    
    # Фильтруем активные и незаблокированные чаты
    active_chats = []
    for chat_id in user_chat_ids:
        if chat_id in active_chats_data:
            chat = active_chats_data[chat_id]
            if not chat.get('blocked_by'):
                active_chats.append((chat_id, chat))
    
    if not active_chats:
        await update.message.reply_text(
            "📭 У вас нет активных чатов\n\n"
            "Откройте приложение для поиска объявлений 👇",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Получаем текущий активный чат
    current_chat_id = context.user_data.get('active_chat_id')
    
    # Формируем список чатов с кнопками
    message = f"💬 Ваши активные чаты ({len(active_chats)}):\n\n"
    keyboard = []
    
    for chat_id, chat in active_chats:
        ad_id = chat.get('ad_id', 'N/A')
        
        # Показываем индикатор активного чата
        if chat_id == current_chat_id:
            message += f"✅ Объявление #{ad_id} (активный)\n"
            button_text = f"✅ Чат #{ad_id} (активный)"
        else:
            message += f"📋 Объявление #{ad_id}\n"
            button_text = f"💬 Открыть чат #{ad_id}"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"openchat_{chat_id}")
        ])
    
    message += "\n💡 Выберите чат для общения.\n"
    message += "Ваши сообщения будут отправляться в активный чат."
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Блокирует собеседника в чате"""
    if not update.message or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    user_chat_ids = context.bot_data.get('user_chats', {}).get(user_id, [])
    active_chats_data = context.bot_data.get('active_chats', {})
    
    # Находим активные незаблокированные чаты
    available_chats = []
    for chat_id in user_chat_ids:
        if chat_id in active_chats_data:
            chat = active_chats_data[chat_id]
            if not chat.get('blocked_by'):
                available_chats.append((chat_id, chat))
    
    if not available_chats:
        await update.message.reply_text("ℹ️ У вас нет активных чатов для блокировки")
        return
    
    # Если один чат - блокируем сразу
    if len(available_chats) == 1:
        chat_id, chat = available_chats[0]
        await _block_chat(update, context, user_id, chat_id, chat)
        return
    
    # Если несколько - предлагаем выбрать
    keyboard = []
    for chat_id, chat in available_chats:
        ad_id = chat.get('ad_id', 'N/A')
        keyboard.append([
            InlineKeyboardButton(
                f"Заблокировать чат по объявлению #{ad_id}",
                callback_data=f"block_{chat_id}"
            )
        ])
    
    await update.message.reply_text(
        "Какой чат заблокировать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def block_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для блокировки чата"""
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    
    await query.answer()
    
    chat_id = query.data.replace("block_", "")
    user_id = query.from_user.id
    
    active_chats = context.bot_data.get('active_chats', {})
    
    if chat_id not in active_chats:
        await context.bot.send_message(user_id, "❌ Чат не найден")
        return
    
    chat = active_chats[chat_id]
    await _block_chat(update, context, user_id, chat_id, chat, is_callback=True)


async def open_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для открытия/переключения чата"""
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    
    await query.answer()
    
    chat_id = query.data.replace("openchat_", "")
    user_id = query.from_user.id
    
    active_chats = context.bot_data.get('active_chats', {})
    
    if chat_id not in active_chats:
        await context.bot.send_message(user_id, "❌ Чат не найден")
        return
    
    chat = active_chats[chat_id]
    ad_id = chat.get('ad_id', 'N/A')
    
    # Сохраняем активный чат
    context.user_data['active_chat_id'] = chat_id
    
    # Уведомляем пользователя
    await context.bot.send_message(
        user_id,
        f"✅ Чат по объявлению #{ad_id} активирован\n\n"
        f"💬 Теперь все ваши сообщения и фото будут отправляться в этот чат.\n"
        f"Используйте /my_chats для переключения на другой чат."
    )



async def _block_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: str, chat: dict, is_callback: bool = False):
    """Вспомогательная функция для блокировки чата"""
    # Помечаем чат как заблокированный
    chat['blocked_by'] = user_id
    
    # Определяем собеседника
    other_user_id = chat['user2'] if user_id == chat['user1'] else chat['user1']
    ad_id = chat.get('ad_id', 'N/A')
    
    # Уведомляем инициатора блокировки
    message = f"🚫 Вы заблокировали чат по объявлению #{ad_id}"
    
    if is_callback and update.callback_query:
        await context.bot.send_message(user_id, message)
    elif update.message:
        await update.message.reply_text(message)
    
    # Уведомляем собеседника
    try:
        await context.bot.send_message(
            other_user_id,
            f"� Чат по объявлению #{ad_id} был завершен собеседником"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить собеседника о блокировке: {e}")
    
    logger.info(f"Чат {chat_id} заблокирован пользователем {user_id}")


# ===== ОБМЕН СООБЩЕНИЯМИ =====

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений - пересылает их в активный чат"""
    if not update.message or not update.message.text or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    message_text = update.message.text
    
    # Получаем активные чаты пользователя
    user_chat_ids = context.bot_data.get('user_chats', {}).get(user_id, [])
    active_chats_data = context.bot_data.get('active_chats', {})
    
    # Фильтруем активные и незаблокированные чаты
    available_chats = []
    for chat_id in user_chat_ids:
        if chat_id in active_chats_data:
            chat = active_chats_data[chat_id]
            if not chat.get('blocked_by'):
                available_chats.append((chat_id, chat))
    
    if not available_chats:
        # Нет активных чатов
        await update.message.reply_text(
            "📭 У вас нет активных чатов\n\n"
            "Откройте приложение для поиска объявлений 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))]
            ])
        )
        return
    
    # Проверяем, есть ли активный выбранный чат
    active_chat_id = context.user_data.get('active_chat_id') if context.user_data else None
    
    # Если есть активный чат и он доступен - отправляем туда
    if active_chat_id and active_chat_id in active_chats_data:
        chat = active_chats_data[active_chat_id]
        if not chat.get('blocked_by') and active_chat_id in [c[0] for c in available_chats]:
            await _send_message_to_chat(context, user_id, active_chat_id, chat, message_text)
            await update.message.reply_text("✅ Сообщение отправлено в активный чат")
            return
    
    # Если один активный чат - отправляем сразу и делаем его активным
    if len(available_chats) == 1:
        chat_id, chat = available_chats[0]
        if context.user_data is not None:
            context.user_data['active_chat_id'] = chat_id
        await _send_message_to_chat(context, user_id, chat_id, chat, message_text)
        await update.message.reply_text("✅ Сообщение отправлено!")
        return
    
    # Если несколько чатов и нет активного - предлагаем выбрать
    if 'pending_messages' not in context.bot_data:
        context.bot_data['pending_messages'] = {}
    
    context.bot_data['pending_messages'][user_id] = message_text
    
    # Создаем кнопки выбора чата
    keyboard = []
    for chat_id, chat in available_chats:
        ad_id = chat.get('ad_id', 'N/A')
        keyboard.append([
            InlineKeyboardButton(
                f"Отправить в чат по объявлению #{ad_id}",
                callback_data=f"sendto_{chat_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("📋 Мои чаты", callback_data="show_my_chats")
    ])
    
    await update.message.reply_text(
        "💬 Выберите чат для отправки:\n\n"
        "💡 Совет: используйте /my_chats чтобы выбрать активный чат,\n"
        "тогда все сообщения будут автоматически отправляться туда.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_to_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для выбора чата-получателя"""
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.data.replace("sendto_", "")
    
    # Получаем сохраненное сообщение
    pending_messages = context.bot_data.get('pending_messages', {})
    message_text = pending_messages.get(user_id)
    
    if not message_text:
        await context.bot.send_message(user_id, "❌ Сообщение не найдено. Отправьте заново.")
        return
    
    # Получаем информацию о чате
    active_chats = context.bot_data.get('active_chats', {})
    
    if chat_id not in active_chats:
        await context.bot.send_message(user_id, "❌ Чат не найден")
        return
    
    chat = active_chats[chat_id]
    
    # Проверяем, не заблокирован ли чат
    if chat.get('blocked_by'):
        await context.bot.send_message(user_id, "❌ Этот чат заблокирован")
        return
    
    # Отправляем сообщение
    await _send_message_to_chat(context, user_id, chat_id, chat, message_text)
    await context.bot.send_message(user_id, "✅ Сообщение отправлено!")
    
    # Удаляем сохраненное сообщение
    del pending_messages[user_id]


async def _send_message_to_chat(context: ContextTypes.DEFAULT_TYPE, sender_id: int, chat_id: str, chat: dict, message_text: str):
    """Вспомогательная функция для отправки сообщения в чат"""
    # Определяем получателя
    recipient_id = chat['user2'] if sender_id == chat['user1'] else chat['user1']
    ad_id = chat.get('ad_id', 'N/A')
    
    # Получаем никнейм отправителя
    sender_nickname = await get_user_nickname(sender_id)
    
    try:
        # Отправляем сообщение с никнеймом отправителя
        await context.bot.send_message(
            recipient_id,
            f"💬 Сообщение от {sender_nickname} (объявление #{ad_id}):\n\n{message_text}"
        )
        
        logger.info(f"Сообщение отправлено от {sender_id} ({sender_nickname}) к {recipient_id} в чате {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        raise  # Пробрасываем ошибку выше для обработки


async def _send_photo_to_chat(context: ContextTypes.DEFAULT_TYPE, sender_id: int, chat_id: str, chat: dict, photo_file_id: str, caption: str = ""):
    """Вспомогательная функция для отправки фото в чат"""
    # Определяем получателя
    recipient_id = chat['user2'] if sender_id == chat['user1'] else chat['user1']
    ad_id = chat.get('ad_id', 'N/A')
    
    # Получаем никнейм отправителя
    sender_nickname = await get_user_nickname(sender_id)
    
    try:
        # Формируем caption с никнеймом отправителя
        full_caption = f"📷 Фото от {sender_nickname} (объявление #{ad_id})"
        if caption:
            full_caption += f"\n\n{caption}"
        
        # Отправляем фото получателю
        await context.bot.send_photo(
            chat_id=recipient_id,
            photo=photo_file_id,
            caption=full_caption
        )
        
        logger.info(f"Фото отправлено от {sender_id} ({sender_nickname}) к {recipient_id} в чате {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")
        raise



# ===== ГЛАВНАЯ ФУНКЦИЯ =====

def main():
    """Запуск бота"""
    logger.info("Запуск бота с системой приглашений в чат...")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mychats", my_chats))
    app.add_handler(CommandHandler("block", block_user))
    
    # Callback обработчики
    app.add_handler(CallbackQueryHandler(create_chat_from_notification, pattern=r"^create_chat_"))
    app.add_handler(CallbackQueryHandler(open_chat, pattern=r"^open_chat_"))
    app.add_handler(CallbackQueryHandler(open_chat_callback, pattern=r"^openchat_"))
    app.add_handler(CallbackQueryHandler(accept_invite, pattern=r"^accept_"))
    app.add_handler(CallbackQueryHandler(decline_invite, pattern=r"^decline_"))
    app.add_handler(CallbackQueryHandler(block_callback, pattern=r"^block_"))
    app.add_handler(CallbackQueryHandler(send_to_chat_callback, pattern=r"^sendto_"))
    app.add_handler(CallbackQueryHandler(send_photo_to_chat_callback, pattern=r"^sendphoto_"))
    
    # Обработчик WebApp данных (для отправки первого сообщения)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, send_first_message))
    
    # Обработчик кнопок меню
    app.add_handler(MessageHandler(
        filters.Regex(r"^(🚀 Открыть приложение|💬 Мои чаты|📋 Мои объявления|❓ Помощь)$"), 
        handle_menu_buttons
    ))
    
    # Обработчик фото (для приватных чатов)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Обработчик текстовых сообщений (для чатов)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Бот готов к работе!")
    logger.info("Доступные команды:")
    logger.info("  /start - Главное меню")
    logger.info("  /mychats - Список активных чатов")
    logger.info("  /block - Заблокировать собеседника")
    
    # Запускаем бота
    app.run_polling()


if __name__ == "__main__":
    main()
