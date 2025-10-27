// Edge Function для Supabase с вашими Yandex настройками
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { SMTPClient } from "https://deno.land/x/denomailer@1.6.0/mod.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, prefer',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
}

serve(async (req) => {
  // Обработка preflight CORS запроса
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Получаем данные из запроса
    const { senderEmail, subject, message } = await req.json()
    
    console.log('Получен запрос:', { senderEmail, subject, message })
    
    // Валидация данных
    if (!senderEmail || !message) {
      return new Response(
        JSON.stringify({ 
          success: false,
          error: 'Отсутствуют обязательные поля: senderEmail, message' 
        }), 
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    if (message.length < 10) {
      return new Response(
        JSON.stringify({ 
          success: false,
          error: 'Сообщение слишком короткое' 
        }), 
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Настройки Yandex SMTP (ваши же настройки)
    const client = new SMTPClient({
      connection: {
        hostname: "smtp.yandex.kz",
        port: 587,
        tls: true,
        auth: {
          username: "wish.online@yandex.kz",
          password: "Fjeiekd469!@#", // ваш пароль из Node.js версии
        },
      },
    })

    // Отправляем письмо
    await client.send({
      from: "Anonimka.online <wish.online@yandex.kz>",
      to: "aleksey@vorobey444.ru", // ваш email из Node.js версии
      replyTo: senderEmail,
      subject: subject || 'Сообщение с anonimka.online',
      content: `От: ${senderEmail}
Тема: ${subject || 'Без темы'}
Время: ${new Date().toLocaleString('ru-RU')}

Сообщение:
${message}

---
Это письмо отправлено автоматически с сайта anonimka.online
Для ответа используйте адрес: ${senderEmail}`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h3 style="color: #333;">Новое сообщение с anonimka.online</h3>
          
          <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr>
              <td style="padding: 8px; background: #f5f5f5; border: 1px solid #ddd; font-weight: bold;">От:</td>
              <td style="padding: 8px; border: 1px solid #ddd;">${senderEmail}</td>
            </tr>
            <tr>
              <td style="padding: 8px; background: #f5f5f5; border: 1px solid #ddd; font-weight: bold;">Тема:</td>
              <td style="padding: 8px; border: 1px solid #ddd;">${subject || 'Без темы'}</td>
            </tr>
            <tr>
              <td style="padding: 8px; background: #f5f5f5; border: 1px solid #ddd; font-weight: bold;">Время:</td>
              <td style="padding: 8px; border: 1px solid #ddd;">${new Date().toLocaleString('ru-RU')}</td>
            </tr>
          </table>
          
          <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h4 style="margin-top: 0;">Сообщение:</h4>
            <p style="white-space: pre-wrap; line-height: 1.6;">${message}</p>
          </div>
          
          <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
          <small style="color: #666;">
            Это письмо отправлено автоматически с сайта <strong>anonimka.online</strong><br>
            Для ответа используйте адрес: <a href="mailto:${senderEmail}">${senderEmail}</a>
          </small>
        </div>
      `,
    })

    await client.close()

    console.log('Письмо отправлено успешно')

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Письмо успешно отправлено'
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Ошибка в функции:', error)
    return new Response(
      JSON.stringify({ 
        success: false,
        error: 'Внутренняя ошибка сервера' 
      }), 
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})