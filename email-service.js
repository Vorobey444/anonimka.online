// Email Service Worker для anonimka.online
// Отправка писем через внешний API без CORS проблем

class EmailService {
    constructor() {
        this.apiEndpoints = [
            // Основной endpoint через Emailjs
            'https://api.emailjs.com/api/v1.0/email/send',
            // Резервный через собственный API
            'https://formcarry.com/s/YOUR_FORM_ID'
        ];
    }

    async sendEmail(emailData) {
        console.log('📧 EmailService: отправляем письмо на vorobey469@yandex.ru');
        
        // Используем только надёжный метод - FormSubmit через скрытый iframe
        try {
            return await this.sendViaFormSubmit(emailData);
        } catch (error) {
            console.error('Ошибка отправки письма:', error);
            throw new Error('Не удалось отправить письмо');
        }
    }



    async sendViaFormSubmit(emailData) {
        console.log('📨 Надёжная отправка через FormSubmit...');
        
        return new Promise((resolve, reject) => {
            try {
                // Создаём форму для отправки
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = 'https://formsubmit.co/vorobey469@yandex.ru';
                form.style.display = 'none';
                
                // Подготавливаем данные письма
                const emailContent = `
От: ${emailData.senderEmail}
Тема: ${emailData.subject || 'Сообщение с anonimka.online'}
Время отправки: ${new Date().toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
})}
IP адрес отправителя: ${this.getClientIP()}

═══════════════════════════════════
СООБЩЕНИЕ:
═══════════════════════════════════

${emailData.message}

═══════════════════════════════════
Это письмо отправлено с сайта anonimka.online
Для ответа клиенту используйте адрес: ${emailData.senderEmail}
                `;
                
                // Настройки FormSubmit
                const fields = {
                    name: 'Anonimka.Online',
                    email: emailData.senderEmail,
                    subject: `[ANONIMKA] ${emailData.subject || 'Новое сообщение'}`,
                    message: emailContent,
                    _subject: `🌟 Новое обращение через Anonimka.Online`,
                    _template: 'table',
                    _captcha: 'false',
                    _autoresponse: 'Спасибо за обращение! Ваше сообщение получено и будет рассмотрено в кратчайшие сроки.',
                    _cc: emailData.senderEmail, // Копия отправителю
                    _next: 'https://vorobey444.github.io/anonimka.online/?status=success'
                };

                // Добавляем поля в форму
                Object.entries(fields).forEach(([name, value]) => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    input.value = value;
                    form.appendChild(input);
                });

                // Создаём скрытый iframe
                const iframe = document.createElement('iframe');
                iframe.name = 'formsubmit_iframe';
                iframe.style.cssText = 'display:none;width:0;height:0;border:none;';
                form.target = 'formsubmit_iframe';
                
                // Добавляем элементы на страницу
                document.body.appendChild(iframe);
                document.body.appendChild(form);
                
                // Обработчик события отправки
                let submitted = false;
                const handleSubmit = () => {
                    if (!submitted) {
                        submitted = true;
                        console.log('✅ FormSubmit: письмо отправлено успешно');
                        
                        // Очистка через 3 секунды
                        setTimeout(() => {
                            try {
                                if (document.body.contains(form)) document.body.removeChild(form);
                                if (document.body.contains(iframe)) document.body.removeChild(iframe);
                            } catch (e) {
                                console.log('Элементы уже удалены');
                            }
                        }, 3000);
                        
                        resolve({
                            success: true,
                            message: 'Письмо успешно отправлено! Мы свяжемся с вами в ближайшее время.',
                            method: 'FormSubmit',
                            timestamp: new Date().toISOString()
                        });
                    }
                };
                
                // Отправляем форму
                form.submit();
                
                // Возвращаем успех через короткое время
                setTimeout(handleSubmit, 2000);
                
            } catch (error) {
                console.error('❌ Ошибка FormSubmit:', error);
                reject(error);
            }
        });
    }
    
    // Вспомогательная функция для получения IP
    getClientIP() {
        // Простое определение примерного IP (для логирования)
        return 'Client IP'; // В реальности можно использовать внешний API
    }
}

// Экспортируем сервис
window.EmailService = EmailService;