"""
Telegram бот для anonimka.kz с интеграцией Neon PostgreSQL
Обрабатывает сообщения и синхронизирует чаты с WebApp
"""

import os
import logging
import aiohttp
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
    
    # Обычное приветствие
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"🎭 **Анонимные знакомства без фильтров**\n\n"
        f"✨ Создай анкету за 30 секунд\n"
        f"💬 Общайся в Мир чате с людьми со всех городов\n"
        f"📍 Находи людей рядом в Город чате\n"
        f"❤️ Получай отклики и начинай диалог\n\n"
        f"🔥 Прямые слова. Без масок. Попробуй!\n\n"
        f"Жми кнопку ниже и начни знакомиться прямо сейчас 👇",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
        ])
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - информация о боте"""
    help_text = (
        "📖 **Справка по Anonimka.kz**\n\n"
        "🚀 **Запустить приложение** - открыть WebApp для создания анкет и общения\n\n"
        "❓ **Помощь** - показать эту справку\n\n"
        "💡 **Как пользоваться:**\n"
        "1. Нажмите 'Запустить приложение'\n"
        "2. Создайте анкету или просмотрите существующие\n"
        "3. Начните общение в чате\n"
        "4. Получайте уведомления о новых сообщениях здесь в боте\n\n"
        "🎯 Все анкеты анонимны и автоматически удаляются через 7 дней!"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Запустить приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
            ])
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Запустить приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp"))]
            ])
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
        return

    # По умолчанию логируем полную трассировку для дебага
    logger.exception(f"❌ Критическая ошибка: {err}")

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчики callback
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(open_chat_callback, pattern="^openchat_"))
    application.add_handler(CallbackQueryHandler(show_my_chats_callback, pattern="^show_my_chats$"))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Глобальный обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен и работает...")
    print("✅ Логируются только важные события")
    print("─" * 40)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
