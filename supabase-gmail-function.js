// Альтернативная Edge Function с Gmail SMTP
// Если Resend не подходит, можно использовать Gmail

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { SMTPClient } from "https://deno.land/x/denomailer@1.6.0/mod.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, prefer',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { senderEmail, subject, message } = await req.json()
    
    if (!senderEmail || !subject || !message) {
      return new Response(
        JSON.stringify({ error: 'Отсутствуют обязательные поля' }), 
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Настройки Gmail SMTP
    const client = new SMTPClient({
      connection: {
        hostname: "smtp.gmail.com",
        port: 587,
        tls: true,
        auth: {
          username: Deno.env.get('GMAIL_USER'), // ваш Gmail
          password: Deno.env.get('GMAIL_APP_PASSWORD'), // пароль приложения
        },
      },
    })

    await client.send({
      from: Deno.env.get('GMAIL_USER'),
      to: "vorobey444@ya.ru",
      subject: subject,
      content: `
        Новое сообщение с anonimka.online
        
        От: ${senderEmail}
        Тема: ${subject}
        
        Сообщение:
        ${message}
        
        Отправлено с сайта anonimka.online
      `,
      html: `
        <h3>Новое сообщение с anonimka.online</h3>
        <p><strong>От:</strong> ${senderEmail}</p>
        <p><strong>Тема:</strong> ${subject}</p>
        <p><strong>Сообщение:</strong></p>
        <p>${message}</p>
        <hr>
        <small>Отправлено с сайта anonimka.online</small>
      `,
    })

    await client.close()

    return new Response(
      JSON.stringify({ success: true, message: 'Письмо отправлено через Gmail' }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Ошибка:', error)
    return new Response(
      JSON.stringify({ error: 'Ошибка отправки' }), 
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})