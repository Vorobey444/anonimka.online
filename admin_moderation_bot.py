"""
Админ-бот для модерации жалоб
Обрабатывает callback от кнопок "Забанить" / "Отклонить"
"""

import os
import logging
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes
)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv('VERCEL_API_URL', 'https://anonimka.kz')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_TG_ID = 884253640

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не настроен!")
    exit(1)

# Команда /start для админа
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ У вас нет доступа к этому боту')
        return
    
    await update.message.reply_text(
        '🛡️ <b>Админ-панель Anonimka</b>\n\n'
        'Доступные команды:\n'
        '/reports - Список активных жалоб\n'
        '/bans - Список забаненных пользователей\n'
        '/stats - Статистика модерации\n\n'
        'Жалобы будут приходить автоматически с кнопками для модерации.',
        parse_mode='HTML'
    )

# Команда /reports - список жалоб
async def reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    for r in reports[:10]:  # Показываем только первые 10
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
        await update.message.reply_text('❌ Ошибка при загрузке жалоб')

# Обработка callback от кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_TG_ID:
        await query.edit_message_text('❌ Доступ запрещен')
        return
    
    data = query.data
    logger.info(f'Callback: {data}')
    
    try:
        if data.startswith('ban_'):
            # Формат: ban_{report_id}_{user_id}
            parts = data.split('_')
            report_id = int(parts[1])
            banned_user_id = int(parts[2])
            
            # Отправляем запрос на бан
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f'{API_BASE_URL}/api/reports',
                    json={
                        'reportId': report_id,
                        'action': 'approve',
                        'adminId': ADMIN_TG_ID,
                        'adminNotes': 'Забанен через админ-панель'
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Обновляем сообщение
                        new_text = query.message.text + f'\n\n✅ <b>ЗАБАНЕН</b> администратором'
                        await query.edit_message_text(
                            new_text,
                            parse_mode='HTML'
                        )
                        logger.info(f'✅ Пользователь {banned_user_id} забанен по жалобе #{report_id}')
                    else:
                        await query.edit_message_text('❌ Ошибка при бане пользователя')
        
        elif data.startswith('reject_'):
            # Формат: reject_{report_id}
            report_id = int(data.split('_')[1])
            
            # Отправляем запрос на отклонение
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
                        # Обновляем сообщение
                        new_text = query.message.text + f'\n\n❌ <b>ОТКЛОНЕНА</b> администратором'
                        await query.edit_message_text(
                            new_text,
                            parse_mode='HTML'
                        )
                        logger.info(f'❌ Жалоба #{report_id} отклонена')
                    else:
                        await query.edit_message_text('❌ Ошибка при отклонении жалобы')
    
    except Exception as e:
        logger.error(f'Ошибка обработки callback: {e}')
        await query.edit_message_text('❌ Ошибка при обработке')

# Команда /bans - список забаненных
async def bans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    await update.message.reply_text('📋 Список банов (функция в разработке)')

# Команда /stats - статистика
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TG_ID:
        await update.message.reply_text('❌ Доступ запрещен')
        return
    
    await update.message.reply_text('📊 Статистика модерации (функция в разработке)')

def main():
    logger.info('🤖 Запуск админ-бота для модерации...')
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('reports', reports_command))
    application.add_handler(CommandHandler('bans', bans_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Запускаем бота
    logger.info('✅ Админ-бот запущен и ожидает команд')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
