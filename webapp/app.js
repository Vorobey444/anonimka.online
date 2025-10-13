// Инициализация Telegram Web App
let tg = window.Telegram.WebApp;
tg.expand();

// Данные формы
let formData = {};
let currentStep = 1;
const totalSteps = 8;

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initializeTelegramWebApp();
    setupEventListeners();
    loadAds();
});

function initializeTelegramWebApp() {
    // Настройка темы
    tg.setHeaderColor('#0a0a0f');
    tg.setBackgroundColor('#0a0a0f');
    
    // Настройка главной кнопки
    tg.MainButton.setText('Главное меню');
    tg.MainButton.onClick(() => showMainMenu());
    
    // Настройка кнопки назад
    tg.BackButton.onClick(() => handleBackButton());
    
    console.log('Telegram Web App initialized');
}

function setupEventListeners() {
    // Кнопки выбора города
    document.querySelectorAll('.city-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.classList.contains('filter')) {
                handleCityFilter(this.dataset.city);
            } else {
                selectCity(this.dataset.city);
            }
        });
    });

    // Кнопки выбора пола
    document.querySelectorAll('.gender-btn').forEach(btn => {
        btn.addEventListener('click', () => selectGender(btn.dataset.gender));
    });

    // Кнопки выбора цели поиска
    document.querySelectorAll('.target-btn').forEach(btn => {
        btn.addEventListener('click', () => selectTarget(btn.dataset.target));
    });

    // Кнопки выбора цели знакомства
    document.querySelectorAll('.goal-btn').forEach(btn => {
        btn.addEventListener('click', () => selectGoal(btn.dataset.goal));
    });

    // Кнопки выбора телосложения
    document.querySelectorAll('.body-btn').forEach(btn => {
        btn.addEventListener('click', () => selectBody(btn.dataset.body));
    });

    // Кастомный город
    document.getElementById('customCity').addEventListener('input', function() {
        if (this.value.trim()) {
            clearCitySelection();
            formData.city = this.value.trim();
        }
    });
}

// Навигация между экранами
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
    
    // Обновляем кнопки Telegram
    updateTelegramButtons(screenId);
}

function updateTelegramButtons(screenId) {
    switch(screenId) {
        case 'mainMenu':
            tg.BackButton.hide();
            tg.MainButton.hide();
            break;
        case 'createAd':
            tg.BackButton.show();
            tg.MainButton.hide();
            break;
        case 'browseAds':
            tg.BackButton.show();
            tg.MainButton.hide();
            break;
        case 'adDetails':
            tg.BackButton.show();
            tg.MainButton.hide();
            break;
    }
}

function handleBackButton() {
    const activeScreen = document.querySelector('.screen.active').id;
    
    switch(activeScreen) {
        case 'createAd':
            showMainMenu();
            break;
        case 'browseAds':
            showMainMenu();
            break;
        case 'adDetails':
            showBrowseAds();
            break;
        default:
            showMainMenu();
    }
}

function showMainMenu() {
    showScreen('mainMenu');
    resetForm();
}

function showCreateAd() {
    showScreen('createAd');
    currentStep = 1;
    showStep(1);
}

function showBrowseAds() {
    showScreen('browseAds');
    loadAds();
}

// Управление шагами формы
function showStep(step) {
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step${step}`).classList.add('active');
    
    // Обновляем кнопки навигации
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    prevBtn.style.display = step > 1 ? 'block' : 'none';
    nextBtn.style.display = step < totalSteps ? 'block' : 'none';
    submitBtn.style.display = step === totalSteps ? 'block' : 'none';
}

function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < totalSteps) {
            currentStep++;
            showStep(currentStep);
        }
    }
}

function previousStep() {
    if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
    }
}

function validateCurrentStep() {
    switch(currentStep) {
        case 1:
            return formData.city || document.getElementById('customCity').value.trim();
        case 2:
            return formData.gender;
        case 3:
            return formData.target;
        case 4:
            return formData.goal;
        case 5:
            const ageFrom = document.getElementById('ageFrom').value;
            const ageTo = document.getElementById('ageTo').value;
            if (ageFrom && ageTo) {
                formData.ageFrom = ageFrom;
                formData.ageTo = ageTo;
                return true;
            }
            return false;
        case 6:
            const myAge = document.getElementById('myAge').value;
            if (myAge) {
                formData.myAge = myAge;
                return true;
            }
            return false;
        case 7:
            return formData.body;
        case 8:
            const adText = document.getElementById('adText').value.trim();
            if (adText) {
                formData.text = adText;
                return true;
            }
            return false;
    }
    return false;
}

// Обработчики выбора
function selectCity(city) {
    clearCitySelection();
    formData.city = city;
    document.querySelector(`[data-city="${city}"]:not(.filter)`).classList.add('selected');
    document.getElementById('customCity').value = '';
}

function clearCitySelection() {
    document.querySelectorAll('.city-btn:not(.filter)').forEach(btn => {
        btn.classList.remove('selected');
    });
}

function selectGender(gender) {
    document.querySelectorAll('.gender-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelector(`[data-gender="${gender}"]`).classList.add('selected');
    formData.gender = gender;
}

function selectTarget(target) {
    document.querySelectorAll('.target-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelector(`[data-target="${target}"]`).classList.add('selected');
    formData.target = target;
}

function selectGoal(goal) {
    document.querySelectorAll('.goal-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelector(`[data-goal="${goal}"]`).classList.add('selected');
    formData.goal = goal;
}

function selectBody(body) {
    document.querySelectorAll('.body-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelector(`[data-body="${body}"]`).classList.add('selected');
    formData.body = body;
}

// Отправка объявления
async function submitAd() {
    if (!validateCurrentStep()) {
        tg.showAlert('Заполните все поля');
        return;
    }

    try {
        // Подготавливаем данные
        const adData = {
            ...formData,
            userId: tg.initDataUnsafe?.user?.id || 'anonymous',
            timestamp: Date.now()
        };

        console.log('Отправка объявления:', adData);

        // Отправляем данные боту
        tg.sendData(JSON.stringify({
            action: 'createAd',
            data: adData
        }));

        // Показываем успех
        tg.showAlert('Объявление успешно создано!', () => {
            showMainMenu();
        });

    } catch (error) {
        console.error('Ошибка создания объявления:', error);
        tg.showAlert('Ошибка при создании объявления');
    }
}

// Загрузка и отображение объявлений
async function loadAds() {
    try {
        // Запрашиваем объявления у бота
        tg.sendData(JSON.stringify({
            action: 'getAds'
        }));

    } catch (error) {
        console.error('Ошибка загрузки объявлений:', error);
    }
}

function displayAds(ads, city = null) {
    const adsList = document.getElementById('adsList');
    
    if (!ads || ads.length === 0) {
        adsList.innerHTML = `
            <div class="no-ads">
                <div class="neon-icon">😔</div>
                <h3>Пока нет объявлений</h3>
                <p>Будьте первым, кто разместит объявление!</p>
            </div>
        `;
        return;
    }

    // Фильтруем по городу если задан
    const filteredAds = city ? ads.filter(ad => ad.city === city) : ads;

    adsList.innerHTML = filteredAds.map((ad, index) => `
        <div class="ad-card" onclick="showAdDetails(${index})">
            <div class="ad-info">
                <div class="ad-field">
                    <span class="icon">🏙</span>
                    <span class="label">Город:</span>
                    <span class="value">${ad.city}</span>
                </div>
                <div class="ad-field">
                    <span class="icon">👤</span>
                    <span class="label">Пол:</span>
                    <span class="value">${ad.gender}</span>
                </div>
                <div class="ad-field">
                    <span class="icon">🔍</span>
                    <span class="label">Ищет:</span>
                    <span class="value">${ad.target}</span>
                </div>
                <div class="ad-field">
                    <span class="icon">🎯</span>
                    <span class="label">Цель:</span>
                    <span class="value">${ad.goal}</span>
                </div>
                <div class="ad-field">
                    <span class="icon">🎂</span>
                    <span class="label">Возраст:</span>
                    <span class="value">${ad.myAge} лет</span>
                </div>
            </div>
            <div class="ad-text">
                "${ad.text.substring(0, 100)}${ad.text.length > 100 ? '...' : ''}"
            </div>
        </div>
    `).join('');
}

function handleCityFilter(city) {
    // Сброс выбора
    document.querySelectorAll('.city-btn.filter').forEach(btn => {
        btn.classList.remove('selected');
    });

    // Выбор нового города
    document.querySelector(`[data-city="${city}"].filter`).classList.add('selected');

    // Запрос объявлений по городу
    tg.sendData(JSON.stringify({
        action: 'getAdsByCity',
        city: city
    }));
}

function showAdDetails(index) {
    // Здесь будет логика показа деталей объявления
    // Пока просто переход на экран деталей
    showScreen('adDetails');
}

function contactAuthor() {
    tg.showAlert('Функция связи с автором будет доступна в следующей версии');
}

// Сброс формы
function resetForm() {
    formData = {};
    currentStep = 1;
    
    // Сброс всех выборов
    document.querySelectorAll('.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Очистка полей
    document.getElementById('customCity').value = '';
    document.getElementById('ageFrom').value = '';
    document.getElementById('ageTo').value = '';
    document.getElementById('myAge').value = '';
    document.getElementById('adText').value = '';
    
    showStep(1);
}

// Обработка данных от бота
tg.onEvent('web_app_data_received', function(data) {
    try {
        const response = JSON.parse(data);
        
        switch(response.action) {
            case 'adsLoaded':
                displayAds(response.ads);
                break;
            case 'cityAdsLoaded':
                displayAds(response.ads, response.city);
                break;
            case 'adCreated':
                tg.showAlert('Объявление создано!');
                showMainMenu();
                break;
            default:
                console.log('Unknown response:', response);
        }
    } catch (error) {
        console.error('Error parsing bot data:', error);
    }
});

// Отладочные функции
window.debugApp = {
    formData: () => console.log(formData),
    currentStep: () => console.log(currentStep),
    tg: () => console.log(tg)
};