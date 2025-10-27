// Простая отправка писем как в whish.online
// Без лишних сервисов и сложностей - просто работает!

function sendEmailWhishStyle(emailData) {
    console.log('📧 Отправляем как в whish.online - просто и работает');
    
    // Создаём простую форму как в whish.online
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = 'https://formsubmit.co/vorobey469@yandex.ru';
    form.style.display = 'none';
    
    // Простые поля как в whish.online
    const fields = {
        name: 'Пользователь Anonimka',
        email: emailData.senderEmail,
        subject: emailData.subject || 'Сообщение с anonimka.online',
        message: emailData.message,
        _captcha: 'false',
        _next: window.location.origin + window.location.pathname + '?sent=ok'
    };
    
    // Добавляем поля в форму
    for (const [name, value] of Object.entries(fields)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        form.appendChild(input);
    }
    
    // Отправляем
    document.body.appendChild(form);
    form.submit();
    
    // Убираем форму
    setTimeout(() => {
        if (form.parentNode) {
            form.parentNode.removeChild(form);
        }
    }, 1000);
    
    console.log('✅ Отправлено просто и надёжно!');
    
    return {
        success: true,
        message: 'Сообщение отправлено! Мы свяжемся с вами по email.'
    };
}

// Экспортируем в глобальную область
window.sendEmailWhishStyle = sendEmailWhishStyle;


