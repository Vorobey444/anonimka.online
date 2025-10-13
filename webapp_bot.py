import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
from typing import List, Dict

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8400755138:AAGG-yNvQknz60IXM7xVHeN-xNtzjHFTG1U"
WEBAPP_URL = "https://whish.online/"  # Mini App на вашем домене

# Хранилище объявлений (в реальном проекте используйте базу данных)
ads: List[Dict[str, str]] = []
chats: Dict[tuple, bool] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартовая команда с кнопкой запуска веб-приложения"""
    logger.info(f"start: Пользователь {update.effective_user.id} запустил бота")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🚀 Открыть приложение", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ])
    
    welcome_text = """
🌟 <b>Добро пожаловать в анонимную доску объявлений!</b>

🎭 Здесь вы можете:
• Создавать анонимные объявления для знакомств
• Искать интересных людей в вашем городе  
• Общаться полностью анонимно

🚀 Нажмите "Открыть приложение" чтобы начать!
    """
    
    try:
        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logger.info("start: Приветственное сообщение отправлено")
    except Exception as e:
        logger.error(f"start: Ошибка отправки сообщения: {e}")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных от веб-приложения"""
    logger.info(f"web_app_data: Получены данные от пользователя {update.effective_user.id}")
    
    try:
        # Парсим данные от веб-приложения
        web_app_data = json.loads(update.effective_message.web_app_data.data)
        action = web_app_data.get('action')
        
        logger.info(f"web_app_data: Действие - {action}")
        
        if action == 'createAd':
            await handle_create_ad(update, context, web_app_data['data'])
        elif action == 'getAds':
            await handle_get_ads(update, context)
        elif action == 'getAdsByCity':
            await handle_get_ads_by_city(update, context, web_app_data['city'])
        else:
            logger.warning(f"web_app_data: Неизвестное действие - {action}")
            
    except Exception as e:
        logger.error(f"web_app_data: Ошибка обработки данных: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке данных")

async def handle_create_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_data: dict):
    """Создание нового объявления"""
    logger.info(f"create_ad: Создание объявления от пользователя {update.effective_user.id}")
    
    try:
        # Добавляем ID пользователя
        ad_data['user_id'] = update.effective_user.id
        
        # Сохраняем объявление
        ads.append(ad_data)
        
        logger.info(f"create_ad: Объявление сохранено: {ad_data}")
        
        # Отправляем подтверждение
        confirmation_text = f"""
✅ <b>Ваше объявление опубликовано!</b>

🏙 <b>Город:</b> {ad_data['city']}
👤 <b>Пол:</b> {ad_data['gender']}
🔍 <b>Ищете:</b> {ad_data['target']}
🎯 <b>Цель:</b> {ad_data['goal']}

📊 Всего объявлений в системе: {len(ads)}
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "👀 Смотреть объявления", 
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?screen=browse")
            )],
            [InlineKeyboardButton(
                "📝 Создать еще одно", 
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?screen=create")
            )]
        ])
        
        await update.message.reply_text(
            confirmation_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"create_ad: Ошибка создания объявления: {e}")
        await update.message.reply_text("❌ Ошибка при создании объявления")

async def handle_get_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение всех объявлений"""
    logger.info(f"get_ads: Запрос всех объявлений от пользователя {update.effective_user.id}")
    
    try:
        if not ads:
            await update.message.reply_text("""
😔 <b>Пока нет объявлений</b>

Будьте первым, кто разместит объявление!
            """, parse_mode='HTML')
            return
        
        # Отправляем информацию о количестве объявлений
        stats_text = f"""
📊 <b>Статистика объявлений:</b>

📝 Всего объявлений: {len(ads)}
🏙 Городов: {len(set(ad['city'] for ad in ads))}
👥 Активных пользователей: {len(set(ad['user_id'] for ad in ads))}

Выберите город для просмотра объявлений в приложении.
        """
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"get_ads: Ошибка получения объявлений: {e}")

async def handle_get_ads_by_city(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str):
    """Получение объявлений по городу"""
    logger.info(f"get_ads_by_city: Запрос объявлений для города {city}")
    
    try:
        city_ads = [ad for ad in ads if ad['city'] == city]
        
        if not city_ads:
            await update.message.reply_text(f"""
😔 <b>В городе {city} пока нет объявлений</b>

Станьте первым, кто разместит объявление в этом городе!
            """, parse_mode='HTML')
            return
        
        # Отправляем краткую статистику по городу
        stats_text = f"""
🏙 <b>Объявления в городе {city}:</b>

📝 Найдено: {len(city_ads)}
👨 Мужчин: {len([ad for ad in city_ads if ad['gender'] == 'Мужчина'])}
👩 Женщин: {len([ad for ad in city_ads if ad['gender'] == 'Женщина'])}

Просматривайте объявления в приложении выше.
        """
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"get_ads_by_city: Ошибка получения объявлений по городу: {e}")

async def handle_contact_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка запросов на связь с авторами"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Парсим callback_data (например, "contact_123")
        _, ad_index = query.data.split('_')
        ad_index = int(ad_index)
        
        if ad_index >= len(ads):
            await query.message.reply_text("❌ Объявление не найдено")
            return
        
        ad = ads[ad_index]
        user_id = query.from_user.id
        author_id = ad['user_id']
        
        # Проверяем, что пользователь не пытается связаться сам с собой
        if user_id == author_id:
            await query.message.reply_text("❌ Вы не можете связаться с собой")
            return
        
        # Создаем чат между пользователями
        chat_key = (user_id, author_id)
        chats[chat_key] = True
        
        logger.info(f"contact_request: Создан чат между {user_id} и {author_id}")
        
        # Уведомляем обоих пользователей
        await context.bot.send_message(
            user_id,
            f"""
✅ <b>Связь установлена!</b>

Теперь вы можете отправлять анонимные сообщения автору объявления.
Просто напишите сообщение в этот чат, и я передам его анонимно.

🏙 Объявление из города: {ad['city']}
            """,
            parse_mode='HTML'
        )
        
        await context.bot.send_message(
            author_id,
            f"""
📬 <b>Кто-то заинтересовался вашим объявлением!</b>

Вы можете получать и отправлять анонимные сообщения.
Просто пишите в этот чат, и я передам сообщения.

🏙 Ваше объявление в городе: {ad['city']}
            """,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"contact_request: Ошибка обработки запроса связи: {e}")
        await query.message.reply_text("❌ Ошибка при установлении связи")

async def handle_message_relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылка анонимных сообщений"""
    if not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    message_text = update.message.text
    
    logger.info(f"message_relay: Сообщение от пользователя {user_id}")
    
    # Ищем активные чаты для этого пользователя
    for (from_id, to_id), active in chats.items():
        if not active:
            continue
            
        if user_id == from_id:
            # Отправляем сообщение получателю
            try:
                await context.bot.send_message(
                    to_id,
                    f"💭 <b>Анонимное сообщение:</b>\n\n{message_text}",
                    parse_mode='HTML'
                )
                await update.message.reply_text("✅ Сообщение доставлено!")
                logger.info(f"message_relay: Сообщение доставлено от {from_id} к {to_id}")
                return
            except Exception as e:
                logger.error(f"message_relay: Ошибка доставки сообщения: {e}")
                await update.message.reply_text("❌ Ошибка доставки сообщения")
                return
                
        elif user_id == to_id:
            # Отправляем ответ отправителю
            try:
                await context.bot.send_message(
                    from_id,
                    f"💭 <b>Анонимный ответ:</b>\n\n{message_text}",
                    parse_mode='HTML'
                )
                await update.message.reply_text("✅ Ответ отправлен!")
                logger.info(f"message_relay: Ответ отправлен от {to_id} к {from_id}")
                return
            except Exception as e:
                logger.error(f"message_relay: Ошибка отправки ответа: {e}")
                await update.message.reply_text("❌ Ошибка отправки ответа")
                return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    help_text = """
🆘 <b>Помощь по боту</b>

🎭 <b>Анонимная доска объявлений</b> - это место для безопасных знакомств.

🔹 <b>Как это работает:</b>
1. Создайте анонимное объявление
2. Укажите ваши предпочтения
3. Другие пользователи могут связаться с вами
4. Общайтесь анонимно через бота

🔹 <b>Команды:</b>
/start - Запустить приложение
/help - Показать эту справку
/stats - Статистика объявлений

🔒 <b>Конфиденциальность:</b>
• Ваши данные не передаются третьим лицам
• Общение полностью анонимно
• Вы можете прекратить общение в любой момент

⚠️ <b>Правила:</b>
• Будьте вежливы и уважительны
• Не публикуйте контактные данные в объявлениях
• Соблюдайте законы вашей страны
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🚀 Открыть приложение", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика объявлений"""
    stats_text = f"""
📊 <b>Статистика системы:</b>

📝 Всего объявлений: {len(ads)}
🏙 Городов: {len(set(ad['city'] for ad in ads)) if ads else 0}
👥 Пользователей: {len(set(ad['user_id'] for ad in ads)) if ads else 0}
💬 Активных чатов: {sum(1 for active in chats.values() if active)}

🔥 <b>Популярные города:</b>
{get_popular_cities()}

🎯 <b>Популярные цели знакомств:</b>
{get_popular_goals()}
    """
    
    await update.message.reply_text(stats_text, parse_mode='HTML')

def get_popular_cities():
    """Получить список популярных городов"""
    if not ads:
        return "Пока нет данных"
        
    city_counts = {}
    for ad in ads:
        city = ad['city']
        city_counts[city] = city_counts.get(city, 0) + 1
    
    sorted_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return '\n'.join([f"• {city}: {count} объявлений" for city, count in sorted_cities])

def get_popular_goals():
    """Получить список популярных целей"""
    if not ads:
        return "Пока нет данных"
        
    goal_counts = {}
    for ad in ads:
        goal = ad['goal']
        goal_counts[goal] = goal_counts.get(goal, 0) + 1
    
    sorted_goals = sorted(goal_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    return '\n'.join([f"• {goal}: {count}" for goal, count in sorted_goals])

def main():
    """Запуск бота"""
    logger.info("Запуск бота с Web App...")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчик данных от веб-приложения
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    # Обработчик callback запросов (для кнопок)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(handle_contact_request, pattern=r"^contact_"))
    
    # Обработчик текстовых сообщений (для анонимного чата)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_relay))
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()