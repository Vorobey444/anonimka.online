"""
Упрощенный бот для анонимной доски объявлений
Только команды /start, /stats и /endchat + обмен сообщениями
"""

import logging
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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
TOKEN = "8400755138:AAGG-yNvQknz60IXM7xVHeN-xNtzjHFTG1U"
API_BASE_URL = "https://anonimka.online"


# ===== КОМАНДЫ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"start: Получено сообщение: {update.message.text if update.message else 'unknown'}")
    
    # Получаем статистику для отображения
    total_users = 0
    total_ads = 0
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/ads", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                ads_list = data.get('ads', [])
                total_ads = len(ads_list)
                
                # Считаем уникальных пользователей
                unique_users = set()
                for ad in ads_list:
                    if ad.get('tg_id'):
                        unique_users.add(ad.get('tg_id'))
                total_users = len(unique_users)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
    
    # Формируем приветственное сообщение со статистикой
    welcome_message = "🌟 Добро пожаловать в анонимную доску объявлений!\n\n"
    
    if total_users > 0:
        welcome_message += f"👥 {total_users:,} пользователей\n"
        welcome_message += f"📋 {total_ads:,} объявлений\n\n"
    
    welcome_message += "🌍 Сайт: anonimka.online\n\n"
    welcome_message += "Откройте приложение для работы с объявлениями 👇"
    
    # Кнопка открытия WebApp
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть приложение", web_app={"url": f"{API_BASE_URL}/webapp/"})]
    ])
    
    try:
        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboard
        )
        logger.info("start: Главное меню отправлено")
    except Exception as e:
        logger.error(f"start: Ошибка отправки главного меню: {e}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику платформы"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/ads", timeout=10)
        
        if response.status_code != 200:
            await update.message.reply_text("⚠️ Не удалось получить статистику. Попробуйте позже.")
            return
        
        data = response.json()
        if not data.get('success'):
            await update.message.reply_text("⚠️ Ошибка получения данных.")
            return
        
        ads_list = data.get('ads', [])
        total_ads = len(ads_list)
        
        # Считаем уникальных пользователей
        unique_users = set()
        for ad in ads_list:
            if ad.get('tg_id'):
                unique_users.add(ad.get('tg_id'))
        
        total_users = len(unique_users)
        
        stats_message = f"""
📊 **Статистика платформы**

👥 Пользователей: **{total_users:,}**
📋 Объявлений: **{total_ads:,}**

🌍 Сайт: anonimka.online
"""
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        logger.info("stats: Статистика отправлена")
        
    except Exception as e:
        logger.error(f"stats: Ошибка: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при получении статистики.")


async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершает активный чат"""
    if not update.message or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    chats = context.bot_data.get('chats', {})
    
    # Ищем активные чаты пользователя
    ended = False
    for (from_id, to_id), active in list(chats.items()):
        if active and (user_id == from_id or user_id == to_id):
            chats[(from_id, to_id)] = False
            ended = True
            
            # Уведомляем обоих участников
            try:
                await context.bot.send_message(
                    from_id,
                    "💔 Чат завершен. Спасибо за использование платформы!"
                )
                await context.bot.send_message(
                    to_id,
                    "💔 Чат завершен. Спасибо за использование платформы!"
                )
            except Exception as e:
                logger.error(f"end_chat: Ошибка отправки уведомления: {e}")
    
    if ended:
        await update.message.reply_text("✅ Чат успешно завершен.")
    else:
        await update.message.reply_text("ℹ️ У вас нет активных чатов.")
    
    logger.info(f"end_chat: Пользователь {user_id} завершил чат")


# ===== ОБРАБОТЧИКИ СООБЩЕНИЙ =====

async def handle_create_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создает приватный чат между пользователями"""
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    
    await query.answer()
    
    try:
        # Формат: create_chat_AD_ID_AUTHOR_TG_ID
        parts = query.data.split('_')
        if len(parts) < 5:
            return
        
        ad_id = parts[2]
        author_tg_id = int(parts[3])
        sender_tg_id = query.from_user.id
        
        if sender_tg_id == author_tg_id:
            await query.message.reply_text("❌ Вы не можете написать сами себе.")
            return
        
        # Создаем пару для переписки
        if 'chats' not in context.bot_data:
            context.bot_data['chats'] = {}
        
        context.bot_data['chats'][(sender_tg_id, author_tg_id)] = True
        context.bot_data['chats'][(author_tg_id, sender_tg_id)] = True
        
        await query.message.reply_text(
            "✅ Чат создан!\n\n"
            "Теперь вы можете отправлять сообщения. Просто напишите текст в чат.\n"
            "Для завершения чата используйте команду /endchat"
        )
        
        await context.bot.send_message(
            author_tg_id,
            f"💬 Новое сообщение по вашему объявлению #{ad_id}!\n"
            f"Отправьте сообщение в этот чат для ответа."
        )
        
        logger.info(f"handle_create_chat: Создан чат между {sender_tg_id} и {author_tg_id}")
        
    except Exception as e:
        logger.error(f"handle_create_chat: Ошибка: {e}")
        await query.message.reply_text("⚠️ Ошибка создания чата. Попробуйте позже.")


async def relay_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает сообщения между пользователями в приватном чате"""
    if not update.message or not update.message.text or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    message_text = update.message.text
    
    # Проверяем активные чаты
    chats = context.bot_data.get('chats', {})
    
    for (from_id, to_id), active in chats.items():
        if active and user_id == from_id:
            try:
                await context.bot.send_message(
                    to_id,
                    f"💬 Анонимное сообщение:\n\n{message_text}"
                )
                await update.message.reply_text("✅ Сообщение отправлено!")
                logger.info(f"relay_private_message: Сообщение от {from_id} к {to_id}")
                return
            except Exception as e:
                logger.error(f"relay_private_message: Ошибка отправки: {e}")
                await update.message.reply_text("⚠️ Не удалось отправить сообщение.")
                return
    
    # Если активного чата нет, ничего не делаем
    logger.debug(f"relay_private_message: Нет активного чата для пользователя {user_id}")


# ===== ГЛАВНАЯ ФУНКЦИЯ =====

def main():
    """Запуск бота"""
    logger.info("Запуск бота...")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("endchat", end_chat))
    
    # Обработчики для переписки
    app.add_handler(CallbackQueryHandler(handle_create_chat, pattern=r"^create_chat_"))
    
    # Обработчик текстовых сообщений (для переписки)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_private_message))
    
    logger.info("Бот готов к работе!")
    
    # Запускаем бота
    app.run_polling()


if __name__ == "__main__":
    main()
