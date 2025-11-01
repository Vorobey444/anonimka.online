"""
Бот для анонимной доски объявлений с системой приглашений в чат
- User A отправляет первое сообщение через WebApp
- User B получает приглашение и может принять/отклонить
- После принятия создается приватный анонимный чат
- Возможность блокировки собеседника с любой стороны
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
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

# Хранилища данных
# sent_messages[sender_id][ad_id] = True - отслеживание отправленных сообщений
# chat_invites[invite_id] = {sender, recipient, ad_id, message, timestamp}
# active_chats[chat_id] = {user1, user2, ad_id, created_at, blocked_by: None/user_id}
# user_chats[user_id] = [chat_id1, chat_id2, ...]


# ===== КОМАНДА START =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - отображает приветствие и кнопку открытия приложения"""
    if not update.message or not update.message.from_user:
        return
        
    user_id = update.message.from_user.id
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
    
    # Приветственное сообщение
    welcome_message = (
        "🌟 Добро пожаловать в анонимную доску объявлений!\n\n"
        "🌍 Сайт: anonimka.kz\n\n"
        "Откройте приложение для работы с объявлениями 👇"
    )
    
    # Кнопка открытия WebApp
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))]
    ])
    
    try:
        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboard
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
    
    try:
        await context.bot.send_message(
            author_tg_id,
            f"💬 Новое сообщение по вашему объявлению #{ad_id}!\n\n"
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
    """Показывает список активных чатов пользователя"""
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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url=f"{API_BASE_URL}/webapp/"))]
            ])
        )
        return
    
    # Формируем список чатов
    message = f"💬 Ваши активные чаты ({len(active_chats)}):\n\n"
    
    for chat_id, chat in active_chats:
        ad_id = chat.get('ad_id', 'N/A')
        message += f"📋 Объявление #{ad_id}\n"
        message += f"   Чат ID: `{chat_id}`\n\n"
    
    message += "\n💡 Просто отправьте сообщение для общения."
    
    await update.message.reply_text(message, parse_mode='Markdown')


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
    """Обработчик текстовых сообщений - пересылает их в активные чаты"""
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
    
    # Если один активный чат - отправляем сразу
    if len(available_chats) == 1:
        chat_id, chat = available_chats[0]
        await _send_message_to_chat(context, user_id, chat_id, chat, message_text)
        await update.message.reply_text("✅ Сообщение отправлено!")
        return
    
    # Если несколько чатов - предлагаем выбрать получателя
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
    
    await update.message.reply_text(
        "💬 Кому отправить сообщение?",
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
    
    try:
        # Отправляем анонимное сообщение получателю
        await context.bot.send_message(
            recipient_id,
            f"💬 Анонимное сообщение (объявление #{ad_id}):\n\n{message_text}"
        )
        
        logger.info(f"Сообщение отправлено от {sender_id} к {recipient_id} в чате {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        raise  # Пробрасываем ошибку выше для обработки



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
    app.add_handler(CallbackQueryHandler(accept_invite, pattern=r"^accept_"))
    app.add_handler(CallbackQueryHandler(decline_invite, pattern=r"^decline_"))
    app.add_handler(CallbackQueryHandler(block_callback, pattern=r"^block_"))
    app.add_handler(CallbackQueryHandler(send_to_chat_callback, pattern=r"^sendto_"))
    
    # Обработчик WebApp данных (для отправки первого сообщения)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, send_first_message))
    
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
