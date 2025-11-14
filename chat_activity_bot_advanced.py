"""
Расширенная версия бота активности с поддержкой контекста и диалогов
Может вести более естественные разговоры
"""

import os
import logging
import aiohttp
import asyncio
import random
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv('VERCEL_API_URL', 'https://anonimka.kz')

# Расширенные персонажи с контекстными ответами
PERSONAS = {
    "bot_alex": {
        "name": "Алекс",
        "emoji": "😎",
        "topics": ["музыка", "фильмы", "игры", "спорт"],
        "starters": [
            "Эй, кто-нибудь тут?",
            "Что нового интересного?",
            "Кто смотрел последние новинки?",
            "Погода огонь сегодня! ☀️",
        ],
        "context_responses": {
            "greeting": ["Йоу! Как дела?", "Привет! Что нового?", "Здарова! 👋"],
            "question": ["Хороший вопрос!", "А вот это интересно", "Дай подумать..."],
            "positive": ["Ага, точно!", "Да, согласен", "👍 Поддерживаю"],
            "negative": ["Хм, не уверен", "Не факт", "Сомневаюсь"],
        }
    },
    "bot_maria": {
        "name": "Мария", 
        "emoji": "🌸",
        "topics": ["путешествия", "кафе", "культура"],
        "starters": [
            "Всем привет! Как настроение? 😊",
            "Кто-нибудь был в новых местах недавно?",
            "Поделитесь чем-нибудь интересным!",
            "Сегодня такой прекрасный день! 🌻",
        ],
        "context_responses": {
            "greeting": ["Привет-привет! 🤗", "Здравствуй! Рада тебя видеть", "Привет! Как дела?"],
            "question": ["Отличный вопрос!", "Интересно, расскажи подробнее", "Хочу узнать больше!"],
            "positive": ["Да, это прекрасно!", "Согласна на все 100%!", "Точно! 💯"],
            "negative": ["Понимаю тебя", "Может и так", "У всех своё мнение 🤷‍♀️"],
        }
    },
    "bot_dima": {
        "name": "Дима",
        "emoji": "🎮",
        "topics": ["технологии", "новости", "игры"],
        "starters": [
            "Как дела?",
            "Что думаете?",
            "Кто в теме?",
            "Есть живые?",
        ],
        "context_responses": {
            "greeting": ["Здарова", "Привет", "Йоу"],
            "question": ["Не знаю", "Может быть", "Посмотрим"],
            "positive": ["Норм", "+1", "Ага"],
            "negative": ["Хз", "Не", "Сомнительно"],
        }
    },
    "bot_kate": {
        "name": "Катя",
        "emoji": "✨",
        "topics": ["настроение", "жизнь", "позитив"],
        "starters": [
            "Доброе утро всем! ☀️✨",
            "Как настроение у всех? 😊💫",
            "Делимся позитивом! 🌈",
            "Хочется чего-то волшебного! ✨🎭",
        ],
        "context_responses": {
            "greeting": ["Привет! 🤗💕", "Здравствуй! ✨", "Йоу! 👋😄"],
            "question": ["Интересно! 🤔✨", "Хороший вопрос! 💭", "Надо подумать! 🧐"],
            "positive": ["Ура! 🎉✨", "Да-да! 💯🔥", "Точно! 👌💫"],
            "negative": ["Хмм... 🤔", "Может быть... 🤷‍♀️", "Не уверена 😅"],
        }
    },
    "bot_artem": {
        "name": "Артём",
        "emoji": "🤔",
        "topics": ["вопросы", "обсуждения", "мнения"],
        "starters": [
            "Интересно, а что вы думаете про...?",
            "Кто-нибудь может ответить?",
            "У кого какое мнение?",
            "Хочу услышать ваши мысли 🤔",
        ],
        "context_responses": {
            "greeting": ["Привет! Рад видеть", "Здравствуй!", "Привет! Как ты?"],
            "question": ["Отличный вопрос! А как по-твоему?", "Интересно! Расскажи больше", "Хочу узнать твоё мнение"],
            "positive": ["Согласен!", "Да, именно так!", "Правильно думаешь"],
            "negative": ["Понимаю, но...", "Может по-другому посмотреть?", "А если с другой стороны?"],
        }
    }
}

# Расширенные шаблоны ответов с контекстом
SMART_RESPONSES = {
    "привет|здравствуй|hi|hello|йоу|хай": {
        "type": "greeting",
        "follow_up": ["Как дела?", "Что нового?", "Давно тут?"]
    },
    "как дела|как настроение|как ты|как сам": {
        "type": "question",
        "responses": [
            "Отлично! А у тебя как?",
            "Всё хорошо, спасибо! Ты как?",
            "Нормально, общаюсь тут 😊 А ты?",
            "Пойдёт! Как у тебя дела?",
        ]
    },
    "кто тут|есть кто|кто онлайн|кто живой": {
        "type": "question",
        "responses": [
            "Мы тут! 👋",
            "Народ есть, общаемся",
            "Я онлайн! Давай общаться",
            "Куча людей тут, заходи!",
        ]
    },
    "скучно|одиноко|грустно": {
        "type": "positive",
        "responses": [
            "Не грусти! Мы тут рядом 🤗",
            "Давай общаться! О чём поболтаем?",
            "Держись! Всё будет хорошо 💪",
            "Мы с тобой, не скучай! 😊",
        ]
    },
    "спасибо|благодарю|thanks|thx": {
        "type": "positive",
        "responses": [
            "Пожалуйста! 😊",
            "Не за что!",
            "Всегда рад помочь! 👍",
            "Обращайся ещё!",
        ]
    },
    "что делать|помогите|help": {
        "type": "question",
        "responses": [
            "Чем помочь? Расскажи подробнее",
            "Что случилось? Давай разберёмся",
            "Слушаю тебя, в чём проблема?",
            "Постараемся помочь! Что нужно?",
        ]
    },
    "хорошо|класс|отлично|круто|супер": {
        "type": "positive",
        "responses": [
            "Да, здорово! 🎉",
            "Рад за тебя!",
            "Круто! 👍",
            "Отлично! 😊",
        ]
    },
    "плохо|не нравится|фигня|ужас": {
        "type": "negative",
        "responses": [
            "Понимаю тебя...",
            "Да, бывает такое",
            "Держись! 💪",
            "Всё наладится!",
        ]
    },
}

class AdvancedChatBot:
    def __init__(self):
        self.last_bot_message_time = {}  # Время последнего сообщения для каждого персонажа
        self.last_checked_message_id = 0
        self.conversation_context = defaultdict(list)  # Контекст разговоров
        self.user_interactions = defaultdict(int)  # Счётчик взаимодействий с пользователем
        
    async def get_messages(self, limit=50):
        """Получить сообщения из чата"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE_URL}/api/world-chat?limit={limit}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('messages', [])
                    return []
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений: {e}")
            return []
    
    async def send_message(self, persona_id, message_text):
        """Отправить сообщение"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE_URL}/api/world-chat",
                    json={
                        "userId": persona_id,
                        "message": message_text,
                        "isBot": True
                    }
                ) as response:
                    if response.status == 200:
                        persona = PERSONAS[persona_id]
                        logger.info(f"✅ {persona['emoji']} {persona['name']}: {message_text}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            return False
    
    def analyze_message(self, message_text):
        """Анализ сообщения для определения типа ответа"""
        message_lower = message_text.lower()
        
        for pattern, config in SMART_RESPONSES.items():
            keywords = pattern.split('|')
            if any(keyword in message_lower for keyword in keywords):
                return pattern, config
        
        # Определяем тип сообщения по длине и структуре
        if '?' in message_text:
            return None, {"type": "question"}
        elif len(message_text) > 100:
            return None, {"type": "positive"}
        else:
            return None, {"type": "greeting"}
    
    def select_persona_for_response(self, message_context):
        """Выбрать подходящего персонажа для ответа"""
        # Выбираем персонажа, который давно не писал
        available_personas = list(PERSONAS.keys())
        
        # Сортируем по времени последнего сообщения
        sorted_personas = sorted(
            available_personas,
            key=lambda p: self.last_bot_message_time.get(p, 0)
        )
        
        # Берём одного из трёх самых "молчаливых"
        return random.choice(sorted_personas[:3])
    
    def generate_smart_response(self, persona_id, pattern, config):
        """Генерация умного ответа с учётом контекста"""
        persona = PERSONAS[persona_id]
        response_type = config.get('type', 'greeting')
        
        # Если есть готовые ответы в шаблоне
        if 'responses' in config:
            return random.choice(config['responses'])
        
        # Иначе используем контекстные ответы персонажа
        context_responses = persona.get('context_responses', {})
        if response_type in context_responses:
            base_response = random.choice(context_responses[response_type])
            
            # Добавляем follow-up вопрос иногда
            if 'follow_up' in config and random.random() < 0.3:
                follow_up = random.choice(config['follow_up'])
                return f"{base_response} {follow_up}"
            
            return base_response
        
        return random.choice(context_responses.get('greeting', ["Привет!"]))
    
    async def respond_to_message(self, message):
        """Ответить на сообщение пользователя"""
        user_id = message.get('userToken') or message.get('user_token') or 'unknown'
        message_text = message.get('message', '')
        
        # Увеличиваем счётчик взаимодействий
        self.user_interactions[user_id] += 1
        
        # Анализируем сообщение
        pattern, config = self.analyze_message(message_text)
        
        # ВСЕГДА отвечаем если есть паттерн
        if not pattern:
            logger.info(f"⏭️ Пропускаем сообщение без паттерна: {message_text[:30]}")
            return
        
        # Имитация набора текста
        await asyncio.sleep(random.uniform(2, 5))
        
        # Выбираем персонажа
        persona_id = self.select_persona_for_response(config)
        
        # Генерируем ответ
        response = self.generate_smart_response(persona_id, pattern, config)
        
        # Отправляем ответ
        if await self.send_message(persona_id, response):
            self.last_bot_message_time[persona_id] = asyncio.get_event_loop().time()
            
            # Сохраняем контекст
            self.conversation_context[user_id].append({
                'user_message': message_text,
                'bot_response': response,
                'persona': persona_id,
                'time': datetime.now()
            })
    
    async def send_random_message(self):
        """Отправить случайное сообщение для создания активности"""
        current_time = asyncio.get_event_loop().time()
        
        # Выбираем персонажа который давно не писал
        available = [
            p for p, t in self.last_bot_message_time.items()
            if current_time - t > 120  # Не писал 2+ минуты
        ]
        
        if not available:
            available = list(PERSONAS.keys())
        
        persona_id = random.choice(available)
        persona = PERSONAS[persona_id]
        
        # Выбираем случайное стартовое сообщение
        message = random.choice(persona['starters'])
        
        if await self.send_message(persona_id, message):
            self.last_bot_message_time[persona_id] = current_time
    
    async def process_new_messages(self):
        """Обработка новых сообщений"""
        messages = await self.get_messages(limit=30)
        
        if not messages:
            return
        
        # Находим новые сообщения от реальных пользователей
        new_messages = [
            msg for msg in messages
            if msg.get('id', 0) > self.last_checked_message_id
            and not msg.get('isBot', False)
        ]
        
        if not new_messages:
            return
        
        # Обновляем последний ID
        self.last_checked_message_id = max(msg.get('id', 0) for msg in messages)
        
        # Обрабатываем каждое новое сообщение
        for message in new_messages:
            logger.info(f"📩 Новое сообщение: {message.get('message', '')[:50]}...")
            await self.respond_to_message(message)
            
            # Небольшая задержка между ответами
            await asyncio.sleep(random.uniform(3, 8))
    
    async def run(self):
        """Основной цикл"""
        logger.info("🤖 Расширенный бот активности запущен!")
        logger.info(f"👥 Персонажей: {len(PERSONAS)}")
        logger.info(f"🧠 Умных шаблонов: {len(SMART_RESPONSES)}")
        logger.info("─" * 50)
        
        while True:
            try:
                # Обрабатываем новые сообщения
                await self.process_new_messages()
                
                # Иногда отправляем случайное сообщение
                if random.random() < 0.2:  # 20% шанс
                    await self.send_random_message()
                
                # Ждём перед следующей проверкой
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Бот остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
                await asyncio.sleep(10)

async def main():
    bot = AdvancedChatBot()
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
