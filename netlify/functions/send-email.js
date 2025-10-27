const nodemailer = require('nodemailer');

exports.handler = async (event, context) => {
  // Разрешаем CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
  };

  // Обработка preflight запроса
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: 'OK'
    };
  }

  // Только POST запросы
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const data = JSON.parse(event.body);
    
    // Валидация
    if (!data.senderEmail || !data.message) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Missing required fields' })
      };
    }

    // Настройка SMTP транспорта
    const transporter = nodemailer.createTransporter({
      host: 'smtp.yandex.ru',
      port: 587,
      secure: false, // TLS
      auth: {
        user: 'wish.online@yandex.kz',
        pass: process.env.YANDEX_APP_PASSWORD || 'aitmytqacblwvpjc'
      }
    });

    // Создание письма
    const mailOptions = {
      from: 'Anonimka.Online <wish.online@yandex.kz>',
      to: 'vorobey469@yandex.ru',
      replyTo: data.senderEmail,
      subject: data.subject || 'Сообщение с anonimka.online',
      html: `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }
                .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                .message { background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
                .info { color: #666; font-size: 14px; margin-bottom: 20px; }
                .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🌟 Новое сообщение с anonimka.online</h2>
                </div>
                <div class="content">
                    <div class="info">
                        <strong>От:</strong> ${data.senderEmail}<br>
                        <strong>Тема:</strong> ${data.subject || 'Сообщение с anonimka.online'}<br>
                        <strong>Время:</strong> ${new Date().toLocaleString('ru-RU')}<br>
                    </div>
                    <div class="message">
                        <strong>Сообщение:</strong><br><br>
                        ${data.message.replace(/\n/g, '<br>')}
                    </div>
                    <div class="footer">
                        Письмо отправлено с сайта <strong>anonimka.online</strong><br>
                        Для ответа используйте адрес: <strong>${data.senderEmail}</strong>
                    </div>
                </div>
            </div>
        </body>
        </html>
      `,
      text: `
        Новое сообщение с сайта anonimka.online
        
        От: ${data.senderEmail}
        Тема: ${data.subject || 'Сообщение с anonimka.online'}
        Время: ${new Date().toLocaleString('ru-RU')}
        
        Сообщение:
        ${data.message}
        
        ---
        Это письмо отправлено с сайта anonimka.online
        Для ответа используйте адрес: ${data.senderEmail}
      `
    };

    // Отправка письма
    await transporter.sendMail(mailOptions);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ 
        success: true, 
        message: 'Письмо отправлено с вашего технического адреса!' 
      })
    };

  } catch (error) {
    console.error('Email error:', error);
    
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: 'Ошибка отправки письма',
        details: error.message 
      })
    };
  }
};