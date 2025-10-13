import { UserService } from './services/user';
import { Telegraf, Context, Markup } from 'telegraf';
import process from 'process';
import { MenuHandler } from './handlers/menu';
import { AdsService } from './services/ads';
import { ChatService } from './services/chat';

const userService = new UserService();
const adsService = new AdsService();
const chatService = new ChatService();

const BOT_TOKEN = process.env.BOT_TOKEN || '8400755138:AAGG-yNvQknz60IXM7xVHeN-xNtzjHFTG1U';
const bot = new Telegraf<Context>(BOT_TOKEN);

// Проверка ника при старте
bot.use(async (ctx, next) => {
    const tg_id = String(ctx.from?.id || 'unknown');
    const nickname = await userService.getNickname(tg_id);
    if (!nickname) {
        await ctx.reply('Привет! Придумайте уникальный Ник для общения на доске:');
        ctx.session = ctx.session || {};
        ctx.session.awaitingNickname = true;
        return;
    }
    await next();
});

bot.start(async (ctx: Context) => {
    const menu = new MenuHandler(ctx);
    await menu.displayMainMenu();
});

bot.command('my_chats', async (ctx: Context) => {
    const tg_id = String(ctx.from?.id || 'unknown');
    const chats = await chatService.getChatsForUser(tg_id);
    if (chats.length === 0) {
        await ctx.reply('У вас нет активных приватных чатов.');
        return;
    }
    const buttons = chats.map(chat => [{ text: `Чат с ${chat.user1 === tg_id ? chat.user2 : chat.user1}`, callback_data: `chat_${chat.chatId}` }]);
    await ctx.reply('Ваши приватные чаты:', {
        reply_markup: { inline_keyboard: buttons }
    });
});

bot.on('callback_query', async (ctx: Context) => {
    const data = ctx.callbackQuery?.data;
    if (data && data.startsWith('respond_')) {
        const adId = data.replace('respond_', '');
        ctx.session = ctx.session || {};
        ctx.session.respondingAdId = adId;
        await ctx.reply('Напишите короткое сообщение-отклик для автора объявления:');
        return;
    }
    if (data && data.startsWith('chat_')) {
        const chatId = data.replace('chat_', '');
        ctx.session = ctx.session || {};
        ctx.session.activeChatId = chatId;
        const messages = await chatService.getMessages(chatId);
        if (messages.length === 0) {
            await ctx.reply('В чате пока нет сообщений.');
        } else {
            for (const msg of messages.slice(-10)) {
                await ctx.reply(`${msg.from}: ${msg.text}`);
            }
        }
        await ctx.reply('Вы можете отправить сообщение в этот чат. Просто напишите его в ответ.');
        return;
    }
    const menu = new MenuHandler(ctx);
    await menu.handleMenuSelection(data);
});

bot.on('text', async (ctx: Context) => {
    const text = ctx.message?.text;
    if (!text) return;
    ctx.session = ctx.session || {};
    const tg_id = String(ctx.from?.id || 'unknown');

    if (ctx.session.awaitingNickname) {
        // Проверяем уникальность ника
        const taken = await userService.isNicknameTaken(text);
        if (taken) {
            await ctx.reply('Этот Ник уже занят. Попробуйте другой:');
        } else {
            await userService.registerNickname(tg_id, text);
            await ctx.reply(`Ваш Ник зарегистрирован: ${text}`);
            ctx.session.awaitingNickname = false;
        }
        return;
    }

    if (ctx.session.activeChatId) {
        await chatService.addMessage(ctx.session.activeChatId, tg_id, text);
        await ctx.reply('Сообщение отправлено в приватный чат!');
        return;
    }

    if (text === 'Подать объявление') {
        await ctx.reply('Пожалуйста, отправьте текст вашего объявления. Оно будет опубликовано анонимно.');
        ctx.session.awaitingAd = true;
    } else if (text === 'Смотреть объявления') {
        const ads = await adsService.getAds();
        if (ads.length === 0) {
            await ctx.reply('Объявлений пока нет.');
        } else {
            for (const ad of ads.slice(-10)) {
                const date = new Date(ad.createdAt);
                const dateStr = date.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
                const authorNickname = await userService.getNickname(ad.userId);
                await ctx.reply(`Заголовок: ${ad.title}\nОписание: ${ad.description}\nАвтор: ${authorNickname || 'Неизвестно'}\nДата: ${dateStr}`);
            }
        }
    } else if (ctx.session.awaitingAd) {
        // Сохраняем объявление
        await adsService.createAd('Анонимное объявление', text, tg_id);
        await ctx.reply('Ваше объявление опубликовано!');
        ctx.session.awaitingAd = false;
    } else if (ctx.session.respondingAdId) {
        // Сохраняем отклик и уведомляем автора
        const ad = await adsService.getAdById(ctx.session.respondingAdId);
        if (!ad) {
            await ctx.reply('Объявление не найдено.');
            ctx.session.respondingAdId = null;
            return;
        }
        // Сохраняем отклик в базе (можно создать отдельную коллекцию responses)
        // Для простоты — отправляем автору
        const authorNickname = await userService.getNickname(ad.userId);
        const responderNickname = await userService.getNickname(tg_id);
        // Найти автора по tg_id и отправить ему сообщение через бот
        await ctx.telegram.sendMessage(
            Number(ad.userId),
            `Вам откликнулись на объявление!\nОт: ${responderNickname}\nТекст: ${ctx.message?.text}\nЕсли хотите начать приватный чат, нажмите кнопку ниже.`,
            {
                reply_markup: {
                    inline_keyboard: [[{ text: 'Начать чат', callback_data: `startchat_${tg_id}_${ad.id}` }]]
                }
            }
        );
        await ctx.reply('Ваш отклик отправлен автору объявления!');
        ctx.session.respondingAdId = null;
        return;
    }
});

// Автор подтверждает чат
bot.on('callback_query', async (ctx: Context) => {
    const data = ctx.callbackQuery?.data;
    if (data && data.startsWith('startchat_')) {
        const [_, responderId, adId] = data.split('_');
        const authorId = String(ctx.from?.id || 'unknown');
        const chatId = await chatService.createChat(authorId, responderId);
        // Оповещаем обе стороны
        await ctx.telegram.sendMessage(
            Number(responderId),
            'Автор объявления заинтересовался вашим откликом! Приватный чат открыт. Можете писать ему через /my_chats.'
        );
        await ctx.reply('Приватный чат создан! Теперь вы можете общаться через /my_chats.');
        return;
    }
    const menu = new MenuHandler(ctx);
    await menu.handleMenuSelection(data);
});

bot.launch().then(() => {
    console.log('Bot is running...');
}).catch((error: any) => {
    console.error('Error launching bot:', error);
});

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));