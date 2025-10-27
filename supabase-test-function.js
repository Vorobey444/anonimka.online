// Упрощенная версия для диагностики
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

    console.log('✅ Валидация пройдена')

    // Пока просто возвращаем успех без отправки SMTP
    console.log('✅ Симуляция отправки письма успешна')

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Письмо успешно отправлено (тестовый режим)',
        data: { senderEmail, subject, message }
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