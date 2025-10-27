// Конфигурация Supabase
const SUPABASE_CONFIG = {
    url: 'https://fmgopveobnsapjygobay.supabase.co', // Ваш Project URL
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtZ29wdmVvYm5zYXBqeWdvYmF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1Nzg5ODEsImV4cCI6MjA3NzE1NDk4MX0.p9DBgPeDDIkQvjYPJQ__8aywLye1hmOxDqe5KcFBRdE'
};

// Простой Supabase клиент (без библиотеки)
class SupabaseClient {
    constructor(url, key) {
        this.url = url;
        this.key = key;
        this.headers = {
            'apikey': key,
            'Authorization': `Bearer ${key}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        };
    }

    // Получить объявления
    async getAds(filters = {}) {
        let url = `${this.url}/rest/v1/ads?select=*&order=created_at.desc`;
        
        // Добавляем фильтры
        if (filters.city) {
            url += `&city=eq.${encodeURIComponent(filters.city)}`;
        }
        if (filters.region) {
            url += `&region=eq.${encodeURIComponent(filters.region)}`;
        }
        if (filters.category) {
            url += `&category=eq.${encodeURIComponent(filters.category)}`;
        }

        const response = await fetch(url, {
            method: 'GET',
            headers: this.headers
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // Создать объявление
    async createAd(adData) {
        const response = await fetch(`${this.url}/rest/v1/ads`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(adData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // Отправить email через Edge Function
    async sendEmail(emailData) {
        const response = await fetch(`${this.url}/functions/v1/send-email`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(emailData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
}

// Инициализация клиента
const supabase = new SupabaseClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);

// Функция для тестирования подключения
async function testSupabaseConnection() {
    try {
        console.log('🔗 Тестируем подключение к Supabase...');
        const ads = await supabase.getAds();
        console.log('✅ Supabase подключен успешно!', ads);
        return true;
    } catch (error) {
        console.error('❌ Ошибка подключения к Supabase:', error);
        return false;
    }
}

// Автоматический тест при загрузке (только для разработки)
if (window.location.hostname === 'localhost') {
    document.addEventListener('DOMContentLoaded', testSupabaseConnection);
}