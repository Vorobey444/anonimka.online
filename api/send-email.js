// Vercel/Netlify function для отправки email
const nodemailer = require('nodemailer');

module.exports = async (req, res) => {
  // Только POST запросы
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { senderEmail, subject, message } = req.body;

    // Валидация
    if (!senderEmail || !message) {
      return res.status(400).json({ 
        success: false, 
        error: 'Отсутствуют обязательные поля' 
      });
    }

    if (message.length < 10) {
      return res.status(400).json({ 
        success: false, 
        error: 'Сообщение слишком короткое' 
      });
    }

    // Настройка транспорта
    const transporter = nodemailer.createTransporter({
      host: 'smtp.yandex.kz',
      port: 587,
      secure: false,
      auth: {
        user: 'wish.online@yandex.kz',
        pass: 'Fjeiekd469!@#'
      }
    });

    // Отправка письма
    const mailOptions = {
      from: '"Anonimka.online" <wish.online@yandex.kz>',
      to: 'aleksey@vorobey444.ru',
      subject: subject || 'Сообщение с anonimka.online',
      replyTo: senderEmail,
      text: `От: ${senderEmail}\nТема: ${subject || 'Без темы'}\nВремя: ${new Date().toLocaleString('ru-RU')}\n\nСообщение:\n${message}\n\n---\nЭто письмо отправлено автоматически с сайта anonimka.online\nДля ответа используйте адрес: ${senderEmail}`
    };

    await transporter.sendMail(mailOptions);

    res.status(200).json({
      success: true,
      message: 'Письмо успешно отправлено'
    });

  } catch (error) {
    console.error('Email error:', error);
    res.status(500).json({
      success: false,
      error: 'Внутренняя ошибка сервера'
    });
  }
};