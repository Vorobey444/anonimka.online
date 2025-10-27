// Исправленная Edge Function для Supabase
// Замените код в вашей функции resend-email на этот код

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
    
    console.log('Получен запрос:', { senderEmail, subject, message })
    
    // Валидация данных
    if (!senderEmail || !subject || !message) {
      return new Response(
        JSON.stringify({ 
          error: 'Отсутствуют обязательные поля: senderEmail, subject, message' 
        }), 
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Настройки для отправки через Resend
    const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY')
    
    if (!RESEND_API_KEY) {
      console.error('RESEND_API_KEY не найден в переменных окружения')
      return new Response(
        JSON.stringify({ error: 'Сервис временно недоступен' }), 
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Отправляем письмо через Resend API
    const resendResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'Anonimka Support <noreply@yourdomain.com>', // Замените на ваш домен
        to: ['vorobey444@ya.ru'], // Ваш email для получения писем
        subject: subject,
        html: `
          <h3>Новое сообщение с anonimka.online</h3>
          <p><strong>От:</strong> ${senderEmail}</p>
          <p><strong>Тема:</strong> ${subject}</p>
          <p><strong>Сообщение:</strong></p>
          <p>${message}</p>
          <hr>
          <small>Отправлено с сайта anonimka.online</small>
        `,
      }),
    })

    if (!resendResponse.ok) {
      const errorData = await resendResponse.text()
      console.error('Ошибка Resend API:', errorData)
      return new Response(
        JSON.stringify({ error: 'Ошибка при отправке письма' }), 
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    const result = await resendResponse.json()
    console.log('Письмо отправлено успешно:', result)

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Письмо успешно отправлено',
        id: result.id 
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Ошибка в функции:', error)
    return new Response(
      JSON.stringify({ error: 'Внутренняя ошибка сервера' }), 
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})