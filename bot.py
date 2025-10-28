import sys
import traceback
from types import TracebackType

def global_excepthook(exc_type: type, exc_value: BaseException, exc_tb: TracebackType) -> None:
    traceback.print_exception(exc_type, exc_value, exc_tb)
    sys.exit(1)
sys.excepthook = global_excepthook

async def contact_author(update: 'Update', context: 'ContextTypes.DEFAULT_TYPE') -> None:
    query = update.callback_query
    if not query or not getattr(query, 'data', None) or not getattr(query, 'from_user', None):
        return
    await query.answer()
    try:
        idx = int(query.data.split('_')[1])
    except Exception:
        return
    ad = ads[idx]
    author_id = ad.get('user_id')
    user_id = query.from_user.id
    if str(author_id) == str(user_id):
        if getattr(query, 'message', None):
            await query.message.reply_text("Вы не можете написать себе.")
        return
    # Сохраняем пару для переписки
    if 'chats' not in context.bot_data:
        context.bot_data['chats'] = {}
    context.bot_data['chats'][(user_id, author_id)] = True
    if getattr(query, 'message', None):
        await query.message.reply_text("Вы можете отправить сообщение автору. Просто напишите его в чат, и бот передаст его анонимно.")
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# ...existing code...

async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.message.from_user.id if update.message.from_user else None
    chats = context.bot_data.get('chats', {})
    # Найти активную пару для переписки
    for (from_id, to_id), active in chats.items():
        if active and user_id == from_id:
            # Переслать сообщение автору объявления
            try:
                await context.bot.send_message(to_id, f"Анонимное сообщение: {update.message.text}")
                await update.message.reply_text("Сообщение отправлено автору объявления!")
            except Exception:
                await update.message.reply_text("Не удалось отправить сообщение.")
            return
        elif active and user_id == to_id:
            # Переслать сообщение откликнувшемуся
            try:
                await context.bot.send_message(from_id, f"Анонимное сообщение: {update.message.text}")
                await update.message.reply_text("Сообщение отправлено собеседнику!")
            except Exception:
                await update.message.reply_text("Не удалось отправить сообщение.")
            return
from telegram.ext import CallbackQueryHandler
# ...existing code...
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import requests

TOKEN = "8400755138:AAGG-yNvQknz60IXM7xVHeN-xNtzjHFTG1U"
API_BASE_URL = "https://anonimka.online"  # URL вашего сайта


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


ASK_CITY, ASK_GENDER, ASK_TARGET, ASK_GOAL, ASK_AGE, ASK_BODY, ASK_TEXT = range(7)
from typing import List, Dict
ads: List[Dict[str, str]] = []

import difflib
CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"]
GENDERS = ["Мужчина", "Женщина"]
TARGETS = ["Мужчину", "Женщину", "Пару"]
GOALS = ["Дружба", "Путешествия", "Общение", "Секс", "Другое"]
BODY_TYPES = ["Стройное", "Обычное", "Плотное", "Спортивное", "Другое"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"start: Получено сообщение: {getattr(update.message, 'text', None)}")
    
    # Проверяем наличие auth_token в /start параметре
    if context.args and len(context.args) > 0:
        auth_token = context.args[0]
        
        # Проверяем что это токен авторизации
        if auth_token.startswith('auth_'):
            user = update.message.from_user
            
            # Формируем данные пользователя
            user_data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name if user.last_name else '',
                'username': user.username if user.username else '',
                'auth_token': auth_token
            }
            
            logger.info(f"QR-авторизация: пользователь {user.id} сканировал QR-код с токеном {auth_token}")
            
            # Отправляем данные на API сайта
            try:
                api_url = f"{API_BASE_URL}/api/telegram-auth"
                payload = {
                    'auth_token': auth_token,
                    'user_data': {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name if user.last_name else '',
                        'username': user.username if user.username else ''
                    }
                }
                
                response = requests.post(api_url, json=payload, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"Данные авторизации отправлены на сайт для токена {auth_token}")
                else:
                    logger.error(f"Ошибка отправки данных на сайт: {response.status_code}")
            except Exception as e:
                logger.error(f"Ошибка отправки данных на API: {e}")
            
            # Уведомляем пользователя
            await update.message.reply_text(
                f"✅ Авторизация успешна!\n\n"
                f"Привет, {user.first_name}! 👋\n\n"
                f"Теперь вы можете вернуться на сайт anonimka.online и продолжить работу.\n\n"
                f"Ваш Telegram ID: {user.id}"
            )
            
            return
    
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
    
    # Обычное приветствие если нет auth_token
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



async def ask_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"ask_city: Получено сообщение: {getattr(update.message, 'text', None)}")
    if update.message is None or update.message.text is None:
        logger.warning("ask_city: update.message или text отсутствует")
        return ConversationHandler.END
    try:
        keyboard = [[city] for city in CITIES] + [["Добавить город"], ["Назад в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите город или начните вводить название:", reply_markup=reply_markup)
        logger.info("ask_city: Клавиатура городов отправлена")
        return ASK_CITY
    except Exception as e:
        logger.error(f"ask_city: Ошибка отправки клавиатуры городов: {e}")
        return ConversationHandler.END
        return ASK_CITY
    else:
        return ConversationHandler.END

async def city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"city_input: Получено сообщение: {getattr(update.message, 'text', None)}")
    if not update.message or not update.message.text:
        logger.warning("city_input: update.message или text отсутствует")
        if update.message:
            try:
                await update.message.reply_text("Пожалуйста, введите название города.")
                logger.info("city_input: Запрошен ввод города")
            except Exception as e:
                logger.error(f"city_input: Ошибка отправки запроса города: {e}")
        return ASK_CITY
    text = update.message.text.strip()
    if text == "Добавить город":
        await update.message.reply_text("Введите название нового города:")
        return ASK_CITY
    matches = difflib.get_close_matches(text, CITIES, n=5, cutoff=0.3)
    if matches and text not in CITIES:
        keyboard = [[m] for m in matches] + [["Добавить город"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Возможно, вы имели в виду:", reply_markup=reply_markup)
        return ASK_CITY
    if text not in CITIES:
        CITIES.append(text)
        await update.message.reply_text(f"Город {text} добавлен! Продолжаем анкету.")
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data["city"] = text
    return await ask_gender(update, context)


# Анкета: город -> пол -> кого ищет -> цель -> возраст -> телосложение -> текст объявления
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"ask_gender: Получено сообщение: {getattr(update.message, 'text', None)}")
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        try:
            keyboard = [[g] for g in GENDERS] + [["Назад в меню"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Ваш пол:", reply_markup=reply_markup)
            logger.info("ask_gender: Клавиатура полов отправлена")
            return ASK_GENDER
        except Exception as e:
            logger.error(f"ask_gender: Ошибка отправки клавиатуры полов: {e}")
            return ConversationHandler.END
    else:
        logger.warning("ask_gender: update.message или text отсутствует")
        return ConversationHandler.END

async def ask_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"ask_target: Получено сообщение: {getattr(update.message, 'text', None)}")
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        try:
            context.user_data["gender"] = update.message.text
            logger.info(f"ask_target: Сохранен пол: {update.message.text}")
            keyboard = [[t] for t in TARGETS] + [["Назад в меню"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Кого ищете:", reply_markup=reply_markup)
            logger.info("ask_target: Клавиатура целей поиска отправлена")
            return ASK_TARGET
        except Exception as e:
            logger.error(f"ask_target: Ошибка отправки клавиатуры целей: {e}")
            return ConversationHandler.END
    else:
        logger.warning("ask_target: update.message или text отсутствует")
        return ConversationHandler.END

async def ask_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"ask_goal: Получено сообщение: {getattr(update.message, 'text', None)}")
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        try:
            context.user_data["target"] = update.message.text
            logger.info(f"ask_goal: Сохранена цель поиска: {update.message.text}")
            keyboard = [[g] for g in GOALS] + [["Назад в меню"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Цель знакомства:", reply_markup=reply_markup)
            logger.info("ask_goal: Клавиатура целей знакомства отправлена")
            return ASK_GOAL
        except Exception as e:
            logger.error(f"ask_goal: Ошибка отправки клавиатуры целей знакомства: {e}")
            return ConversationHandler.END
    else:
        logger.warning("ask_goal: update.message или text отсутствует")
        return ConversationHandler.END

async def ask_age_target_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        context.user_data["goal"] = update.message.text
        keyboard = [["Назад в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Возраст кого ищете (от):", reply_markup=reply_markup)
        return 100  # Custom state for age_target_from
    else:
        return ConversationHandler.END

async def ask_age_target_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        context.user_data["age_target_from"] = update.message.text
        keyboard = [["Назад в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Возраст кого ищете (до):", reply_markup=reply_markup)
        return 101  # Custom state for age_target_to
    else:
        return ConversationHandler.END

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        context.user_data["age_target_to"] = update.message.text
        keyboard = [["Назад в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваш возраст:", reply_markup=reply_markup)
        return ASK_AGE
    else:
        return ConversationHandler.END

async def ask_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        context.user_data["age"] = update.message.text
        keyboard = [[b] for b in BODY_TYPES] + [["Назад в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваше телосложение:", reply_markup=reply_markup)
        return ASK_BODY
    else:
        return ConversationHandler.END

async def ask_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        context.user_data["body"] = update.message.text
        keyboard = [["Назад в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Введите текст объявления:", reply_markup=reply_markup)
        return ASK_TEXT
    else:
        return ConversationHandler.END

async def save_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"save_ad: Получено сообщение: {getattr(update.message, 'text', None)}")
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text:
        try:
            context.user_data["text"] = update.message.text
            if update.message.from_user:
                context.user_data["user_id"] = update.message.from_user.id
            ads.append(dict(context.user_data))
            logger.info(f"save_ad: Объявление сохранено: {dict(context.user_data)}")
            await update.message.reply_text("Ваше объявление опубликовано!")
            keyboard = [["Подать объявление"], ["Смотреть объявления"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Главное меню:", reply_markup=reply_markup)
            logger.info("save_ad: Объявление сохранено, главное меню отправлено")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"save_ad: Ошибка сохранения объявления: {e}")
            return ConversationHandler.END
    else:
        logger.warning("save_ad: update.message или text отсутствует")
        return ConversationHandler.END


async def show_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"show_ads: Получено сообщение: {getattr(update.message, 'text', None)}")
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message:
        logger.warning("show_ads: update.message отсутствует")
        return
    try:
        keyboard = [[city] for city in CITIES] + [["Назад в меню"]]
        await update.message.reply_text("Выберите город для поиска объявлений:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        context.user_data['filter_step'] = 'city'
        logger.info("show_ads: Клавиатура городов для фильтра отправлена")
    except Exception as e:
        logger.error(f"show_ads: Ошибка отправки клавиатуры городов: {e}")

async def filter_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global logger
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message or not update.message.text:
        logger.warning("filter_ads: Пустое сообщение или текст отсутствует")
        return
    text = update.message.text
    logger.info(f"filter_ads: Получен текст фильтрации: {text}")

    if text == "Назад в меню":
        keyboard = [["Подать объявление"], ["Смотреть объявления"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Главное меню:", reply_markup=reply_markup)
        logger.info("filter_ads: Пользователь вернулся в главное меню")
        return

    if text == "Подать объявление":
        logger.info("filter_ads: Запуск анкеты по кнопке 'Подать объявление'")
        await ask_city(update, context)
        return

    if text == "Смотреть объявления":
        logger.info("filter_ads: Запуск просмотра объявлений по кнопке 'Смотреть объявления'")
        await show_ads(update, context)
        return

    if text in CITIES:
        context.user_data['filter_city'] = text
        logger.info(f"filter_ads: Установлен фильтр город: {text}")
        # Показываем ВСЕ объявления из выбранного города, игнорируя остальные фильтры
        await show_city_ads(update, context)
        return

async def show_city_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать ВСЕ объявления из выбранного города"""
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    logger.info(f"show_city_ads: Показ объявлений для города {context.user_data.get('filter_city')}")
    if not update.message:
        return
    
    city = context.user_data.get('filter_city')
    city_ads = [ad for ad in ads if ad.get('city') == city]
    
    if city_ads:
        logger.info(f"show_city_ads: Найдено {len(city_ads)} объявлений в городе {city}")
        for idx, ad in enumerate(city_ads):
            ad_text = (
                f"🏙 Город: {ad.get('city', '')}\n"
                f"👤 Пол: {ad.get('gender', '')}\n" 
                f"🔍 Ищу: {ad.get('target', '')}\n"
                f"🎯 Цель: {ad.get('goal', '')}\n"
                f"🎂 Возраст: {ad.get('age', '')}\n"
                f"💪 Телосложение: {ad.get('body', '')}\n"
                f"📅 Возраст партнера: {ad.get('age_target_from', '')}-{ad.get('age_target_to', '')}\n"
                f"💬 Текст: {ad.get('text', '')}"
            )
            try:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✉️ Написать автору", callback_data=f"contact_{ads.index(ad)}")]
                ])
                await update.message.reply_text(ad_text, reply_markup=keyboard)
                logger.info(f"show_city_ads: Отправлено объявление {idx+1}")
            except Exception as e:
                logger.error(f"show_city_ads: Ошибка отправки объявления {idx+1}: {e}")
    else:
        await update.message.reply_text(f"В городе {city} пока нет объявлений.")
        logger.info(f"show_city_ads: Объявлений в городе {city} не найдено")
    
    # Показать главное меню
    keyboard = [["Подать объявление"], ["Смотреть объявления"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Главное меню:", reply_markup=reply_markup)

# --- ВНЕ filter_ads ---
async def show_filtered_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def safe_int(val: str, default: int) -> int:
        try:
            return int(val)
        except Exception:
            return default
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message:
        return
    user_data = context.user_data
    filtered: List[Dict[str, str]] = [ad for ad in ads if
        ad.get('city') == user_data.get('filter_city') and
        ad.get('gender') == user_data.get('filter_gender') and
        ad.get('target') == user_data.get('filter_target') and
        ad.get('goal') == user_data.get('filter_goal') and
        ad.get('age') == user_data.get('filter_age') and
        ad.get('body') == user_data.get('filter_body') and
        (
            user_data.get('filter_age_target_from', '') == '' or
            ad.get('age_target_from', '') == '' or
            safe_int(ad.get('age_target_from', '0'), 0) <= safe_int(user_data.get('filter_age_target_from', '0'), 0)
        ) and
        (
            user_data.get('filter_age_target_to', '') == '' or
            ad.get('age_target_to', '') == '' or
            safe_int(ad.get('age_target_to', '999'), 999) >= safe_int(user_data.get('filter_age_target_to', '999'), 999)
        )
    ]
    if filtered:
        for idx, ad in enumerate(filtered[-10:]):  # type: ignore
            ad_text = (
                f"Город: {ad.get('city', '')}\n"
                f"Пол: {ad.get('gender', '')}\n"
                f"Ищу: {ad.get('target', '')}\n"
                f"Цель: {ad.get('goal', '')}\n"
                f"Возраст: {ad.get('age', '')}\n"
                f"Телосложение: {ad.get('body', '')}\n"
                f"Возраст кого ищу: {ad.get('age_target_from', '')}-{ad.get('age_target_to', '')}\n"
                f"Текст: {ad.get('text', '')}\n"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Написать автору", callback_data=f"contact_{ads.index(ad)}")]
            ])
            await update.message.reply_text(ad_text, reply_markup=keyboard)
    else:
        await update.message.reply_text("Нет объявлений по выбранным критериям.")
    user_data['filter_step'] = None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

# Обработчик создания приватного чата
async def handle_create_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создание приватного чата между пользователями"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    try:
        # Парсим callback_data: create_chat_{ad_id}_{sender_tg_id}
        parts = query.data.split('_')
        ad_id = parts[2]
        sender_tg_id = parts[3]
        receiver_tg_id = query.from_user.id
        
        # Сохраняем активный чат
        if 'active_chats' not in context.bot_data:
            context.bot_data['active_chats'] = {}
        
        # Создаем двусторонний чат
        chat_key = f"{sender_tg_id}_{receiver_tg_id}"
        reverse_chat_key = f"{receiver_tg_id}_{sender_tg_id}"
        
        context.bot_data['active_chats'][chat_key] = {
            'sender': sender_tg_id,
            'receiver': receiver_tg_id,
            'ad_id': ad_id,
            'active': True
        }
        
        context.bot_data['active_chats'][reverse_chat_key] = {
            'sender': receiver_tg_id,
            'receiver': sender_tg_id,
            'ad_id': ad_id,
            'active': True
        }
        
        # Уведомляем получателя (автора объявления)
        await query.message.edit_text(
            "✅ Приватный чат создан!\n\n"
            "Теперь вы можете общаться напрямую. "
            "Все сообщения, которые вы отправите боту, будут переданы собеседнику.\n\n"
            "Для завершения чата используйте команду /endchat"
        )
        
        # Уведомляем отправителя
        try:
            await context.bot.send_message(
                chat_id=sender_tg_id,
                text="✅ Автор объявления принял ваш запрос!\n\n"
                     "Приватный чат создан. Все сообщения, которые вы отправите боту, "
                     "будут переданы собеседнику.\n\n"
                     "Для завершения чата используйте команду /endchat"
            )
        except Exception as e:
            logging.error(f"Error notifying sender: {e}")
        
        logging.info(f"Private chat created between {sender_tg_id} and {receiver_tg_id}")
        
    except Exception as e:
        logging.error(f"Error creating private chat: {e}")
        await query.message.reply_text("❌ Ошибка при создании чата. Попробуйте позже.")

# Обработчик просмотра объявления
async def handle_view_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать детали объявления"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    try:
        # Парсим callback_data: view_ad_{ad_id}
        ad_id = query.data.split('_')[2]
        
        # Здесь нужно загрузить объявление из Supabase
        # Пока просто сообщаем что функция в разработке
        await query.message.reply_text(
            f"📋 Просмотр объявления #{ad_id}\n\n"
            "Функция в разработке. Скоро вы сможете видеть полную информацию об объявлении."
        )
        
    except Exception as e:
        logging.error(f"Error viewing ad: {e}")
        await query.message.reply_text("❌ Ошибка при загрузке объявления.")

# Обработчик завершения чата
async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершить приватный чат"""
    if not update.message:
        return
    
    user_id = update.message.from_user.id
    
    if 'active_chats' not in context.bot_data:
        await update.message.reply_text("У вас нет активных чатов.")
        return
    
    # Ищем активный чат пользователя
    ended = False
    for chat_key in list(context.bot_data['active_chats'].keys()):
        chat = context.bot_data['active_chats'][chat_key]
        if str(chat['sender']) == str(user_id) and chat['active']:
            # Завершаем чат
            chat['active'] = False
            other_user = chat['receiver']
            
            # Уведомляем собеседника
            try:
                await context.bot.send_message(
                    chat_id=other_user,
                    text="❌ Собеседник завершил приватный чат."
                )
            except Exception as e:
                logging.error(f"Error notifying other user: {e}")
            
            ended = True
    
    if ended:
        await update.message.reply_text("✅ Приватный чат завершён.")
    else:
        await update.message.reply_text("У вас нет активных чатов.")

# Пересылка сообщений в приватном чате
async def relay_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылка сообщений между пользователями в приватном чате"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    
    # Проверяем наличие активных чатов
    if 'active_chats' not in context.bot_data:
        return
    
    # Ищем активный чат для этого пользователя
    for chat_key, chat in context.bot_data['active_chats'].items():
        if str(chat['sender']) == str(user_id) and chat.get('active', False):
            receiver_id = chat['receiver']
            
            # Пересылаем сообщение
            try:
                await context.bot.send_message(
                    chat_id=receiver_id,
                    text=f"💬 Сообщение от собеседника:\n\n{update.message.text}"
                )
                await update.message.reply_text("✅ Сообщение отправлено")
                logging.info(f"Message relayed from {user_id} to {receiver_id}")
                return
            except Exception as e:
                logging.error(f"Error relaying message: {e}")
                await update.message.reply_text("❌ Ошибка при отправке сообщения")
                return

# Статистика пользователей
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику: количество объявлений и пользователей"""
    try:
        # Получаем все объявления из API
        response = requests.get(f"{API_BASE_URL}/api/ads")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                ads = data.get('ads', [])
                total_ads = len(ads)
                
                # Считаем уникальных пользователей
                unique_users = set()
                for ad in ads:
                    if ad.get('tg_id'):
                        unique_users.add(ad.get('tg_id'))
                
                total_users = len(unique_users)
                
                # Формируем сообщение
                stats_message = f"""
📊 **Статистика платформы**

👥 Пользователей: **{total_users:,}**
📋 Объявлений: **{total_ads:,}**

🌍 Сайт: anonimka.online
"""
                
                await update.message.reply_text(
                    stats_message,
                    parse_mode='Markdown'
                )
                logging.info(f"Stats requested by {update.message.from_user.id}: {total_users} users, {total_ads} ads")
            else:
                await update.message.reply_text("❌ Не удалось получить статистику")
        else:
            await update.message.reply_text("❌ Ошибка при получении данных")
            
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    # Основные команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))  # Команда статистики
    app.add_handler(CommandHandler("endchat", end_chat))
    
    # Обработчики для переписки между пользователями
    app.add_handler(CallbackQueryHandler(contact_author, pattern=r"^contact_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_create_chat, pattern=r"^create_chat_"))
    app.add_handler(CallbackQueryHandler(handle_view_ad, pattern=r"^view_ad_"))
    
    # Обработчики сообщений для переписки
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_private_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_message))

    app.run_polling()
