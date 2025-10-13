import { Context } from 'telegraf';
import { InlineKeyboardMarkup } from 'telegraf/typings/core/types/typegram';

export class MenuHandler {
    private ctx: Context;

    constructor(ctx: Context) {
        this.ctx = ctx;
    }

    public async displayMainMenu(): Promise<void> {
        const keyboard: InlineKeyboardMarkup = {
            inline_keyboard: [
                [
                    { text: 'Подать объявление', callback_data: 'submit_ad' },
                    { text: 'Просмотреть объявления', callback_data: 'view_ads' }
                ],
                [
                    { text: 'Помощь', callback_data: 'help' }
                ]
            ]
        };

        await this.ctx.reply('Добро пожаловать! Выберите действие:', { reply_markup: keyboard });
    }

    public async handleMenuSelection(callbackData: string): Promise<void> {
        switch (callbackData) {
            case 'submit_ad':
                await this.ctx.reply('Пожалуйста, введите текст вашего объявления:');
                break;
            case 'view_ads':
                // Logic to retrieve and display ads will go here
                await this.ctx.reply('Вот ваши объявления:');
                break;
            case 'help':
                await this.ctx.reply('Если вам нужна помощь, обратитесь к администратору.');
                break;
            default:
                await this.ctx.reply('Неизвестный выбор. Пожалуйста, попробуйте снова.');
        }
    }
}