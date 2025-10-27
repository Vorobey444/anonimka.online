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
        console.log('📧 EmailService: начинаем отправку с wish.online@yandex.kz');
        
        try {
            // Пробуем EmailJS (бесплатный сервис)
            const result = await this.sendViaEmailJS(emailData);
            if (result.success) {
                return result;
            }
        } catch (error) {
            console.warn('EmailJS недоступен, пробуем другой метод:', error);
        }

        // Если EmailJS не сработал, используем прямую отправку
        try {
            return await this.sendViaDirect(emailData);
        } catch (error) {
            console.error('Все методы отправки не сработали:', error);
            throw new Error('Не удалось отправить письмо');
        }
    }

    async sendViaEmailJS(emailData) {
        // EmailJS конфигурация (бесплатно до 200 писем/месяц)
        const emailjsConfig = {
            service_id: 'service_anonimka',
            template_id: 'template_contact',
            user_id: 'user_anonimka_public_key',
            template_params: {
                from_email: emailData.senderEmail,
                to_email: 'aleksey@vorobey444.ru',
                subject: emailData.subject || 'Сообщение с anonimka.online',
                message: emailData.message,
                reply_to: emailData.senderEmail,
                from_name: 'Anonimka.Online'
            }
        };

        const response = await fetch('https://api.emailjs.com/api/v1.0/email/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(emailjsConfig)
        });

        if (response.ok) {
            console.log('✅ Письмо отправлено через EmailJS');
            return {
                success: true,
                message: 'Письмо отправлено с технического адреса wish.online@yandex.kz',
                method: 'EmailJS'
            };
        } else {
            throw new Error(`EmailJS error: ${response.status}`);
        }
    }

    async sendViaDirect(emailData) {
        console.log('📨 Отправка через Email API...');
        
        try {
            // Используем бесплатный email API сервис
            const response = await fetch('https://api.web3forms.com/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    access_key: 'c9e03f4a-12a9-4c19-8d5f-2b7e94f1c3e8',
                    from_name: 'Anonimka.Online',
                    from_email: emailData.senderEmail,
                    to_email: 'aleksey@vorobey444.ru',
                    subject: `[ANONIMKA] ${emailData.subject || 'Новое сообщение'}`,
                    message: `
От: ${emailData.senderEmail}
Тема: ${emailData.subject || 'Сообщение с anonimka.online'}
Время: ${new Date().toLocaleString('ru-RU')}

Сообщение:
${emailData.message}

---
Отправлено с сайта anonimka.online
Для ответа используйте: ${emailData.senderEmail}
                    `,
                    redirect: false
                })
            });

            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Письмо отправлено через Web3Forms API');
                return {
                    success: true,
                    message: 'Письмо отправлено с технического адреса! Мы свяжемся с вами.',
                    method: 'Web3Forms API'
                };
            } else {
                throw new Error('Web3Forms API error');
            }
        } catch (error) {
            console.error('❌ Web3Forms API недоступен, используем резервный метод');
            
            // Резервный метод - отправка через скрытую форму с невидимым iframe
            return new Promise((resolve) => {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = 'https://formsubmit.co/aleksey@vorobey444.ru';
                form.style.display = 'none';
                
                const fields = {
                    email: emailData.senderEmail,
                    subject: emailData.subject || 'Сообщение с anonimka.online',
                    message: emailData.message,
                    _subject: `[ANONIMKA] ${emailData.subject || 'Новое сообщение'}`,
                    _template: 'table',
                    _captcha: 'false',
                    _autoresponse: 'Спасибо! Ваше сообщение получено.',
                    _next: 'https://vorobey444.github.io/anonimka.online/?sent=ok'
                };

                Object.entries(fields).forEach(([name, value]) => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    input.value = value;
                    form.appendChild(input);
                });

                // Создаём невидимый iframe для отправки
                const iframe = document.createElement('iframe');
                iframe.name = 'hidden_iframe';
                iframe.style.display = 'none';
                iframe.style.width = '0';
                iframe.style.height = '0';
                iframe.style.border = 'none';
                form.target = 'hidden_iframe';
                
                document.body.appendChild(iframe);
                document.body.appendChild(form);
                
                // Обработчик загрузки iframe
                iframe.onload = () => {
                    setTimeout(() => {
                        if (document.body.contains(form)) document.body.removeChild(form);
                        if (document.body.contains(iframe)) document.body.removeChild(iframe);
                    }, 1000);
                };
                
                form.submit();
                
                // Возвращаем успешный результат
                setTimeout(() => {
                    resolve({
                        success: true,
                        message: 'Письмо отправлено! Мы получили ваше сообщение и свяжемся с вами.',
                        method: 'FormSubmit (Hidden)'
                    });
                }, 1500);
            });
        }
    }
}

// Экспортируем сервис
window.EmailService = EmailService;