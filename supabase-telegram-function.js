// Рабочая Edge Function без внешних SMTP библиотек
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

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
    
    console.log('✅ Получен запрос:', { senderEmail, subject, message })
    
    // Валидация данных
    if (!senderEmail || !message) {
      console.log('❌ Валидация не пройдена')
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

    console.log('✅ Валидация пройдена')

    // Отправляем письмо через Telegram Bot API
    const telegramBotToken = "7185550869:AAHlXLfAIzKgH4I7bHAvqwHsa4K-nc9y8x4"
    const telegramChatId = "1296477754" // ваш chat_id
    
    const telegramMessage = `🔥 Новое сообщение с anonimka.online

📧 От: ${senderEmail}
📝 Тема: ${subject || 'Без темы'}
⏰ Время: ${new Date().toLocaleString('ru-RU')}

💬 Сообщение:
${message}

---
Отправлено с сайта anonimka.online
Для ответа используйте: ${senderEmail}`

    const telegramUrl = `https://api.telegram.org/bot${telegramBotToken}/sendMessage`
    
    const telegramResponse = await fetch(telegramUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        chat_id: telegramChatId,
        text: telegramMessage,
        parse_mode: 'HTML'
      })
    })

    if (!telegramResponse.ok) {
      const errorData = await telegramResponse.text()
      console.error('❌ Ошибка Telegram API:', errorData)
      throw new Error('Ошибка отправки через Telegram')
    }

    const result = await telegramResponse.json()
    console.log('✅ Письмо отправлено через Telegram:', result)

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Письмо успешно отправлено через Telegram',
        id: result.message_id
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('❌ Ошибка в функции:', error)
    return new Response(
      JSON.stringify({ 
        success: false,
        error: `Внутренняя ошибка: ${error.message}` 
      }), 
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})