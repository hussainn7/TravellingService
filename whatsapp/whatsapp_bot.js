const fs = require('fs');
const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');
const axios = require('axios'); // Import axios for making HTTP requests
const xml2js = require('xml2js'); // Add this at the top with other requires

class WhatsAppBot {
    constructor() {
        this.client = new Client({
            authStrategy: new LocalAuth(),
            puppeteer: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            }
        });

        this.userData = new Map(); // Store user data
        this.countries = this.loadCountries(); // Load country list
        this.setupEventHandlers();
    }

    loadCountries() {
        // Define the list of countries
        return [
            { id: "46", name: "Абхазия" },
            { id: "31", name: "Австрия" },
            { id: "55", name: "Азербайджан" },
            { id: "71", name: "Албания" },
            { id: "17", name: "Андорра" },
            { id: "88", name: "Аргентина" },
            { id: "53", name: "Армения" },
            { id: "72", name: "Аруба" },
            { id: "59", name: "Бахрейн" },
            { id: "57", name: "Беларусь" },
            { id: "20", name: "Болгария" },
            { id: "39", name: "Бразилия" },
            { id: "44", name: "Великобритания" },
            { id: "37", name: "Венгрия" },
            { id: "90", name: "Венесуэла" },
            { id: "16", name: "Вьетнам" },
            { id: "38", name: "Германия" },
            { id: "6", name: "Греция" },
            { id: "54", name: "Грузия" },
            { id: "11", name: "Доминикана" },
            { id: "1", name: "Египет" },
            { id: "30", name: "Израиль" },
            { id: "3", name: "Индия" },
            { id: "7", name: "Индонезия" },
            { id: "29", name: "Иордания" },
            { id: "92", name: "Иран" },
            { id: "14", name: "Испания" },
            { id: "24", name: "Италия" },
            { id: "78", name: "Казахстан" },
            { id: "40", name: "Камбоджа" },
            { id: "79", name: "Катар" },
            { id: "51", name: "Кения" },
            { id: "15", name: "Кипр" },
            { id: "60", name: "Киргизия" },
            { id: "13", name: "Китай" },
            { id: "10", name: "Куба" },
            { id: "80", name: "Ливан" },
            { id: "27", name: "Маврикий" },
            { id: "36", name: "Малайзия" },
            { id: "8", name: "Мальдивы" },
            { id: "50", name: "Мальта" },
            { id: "23", name: "Марокко" },
            { id: "18", name: "Мексика" },
            { id: "81", name: "Мьянма" },
            { id: "82", name: "Непал" },
            { id: "9", name: "ОАЭ" },
            { id: "64", name: "Оман" },
            { id: "87", name: "Панама" },
            { id: "35", name: "Португалия" },
            { id: "47", name: "Россия" },
            { id: "93", name: "Саудовская Аравия" },
            { id: "28", name: "Сейшелы" },
            { id: "58", name: "Сербия" },
            { id: "25", name: "Сингапур" },
            { id: "43", name: "Словения" },
            { id: "2", name: "Таиланд" },
            { id: "41", name: "Танзания" },
            { id: "5", name: "Тунис" },
            { id: "4", name: "Турция" },
            { id: "56", name: "Узбекистан" },
            { id: "26", name: "Филиппины" },
            { id: "34", name: "Финляндия" },
            { id: "32", name: "Франция" },
            { id: "22", name: "Хорватия" },
            { id: "21", name: "Черногория" },
            { id: "19", name: "Чехия" },
            { id: "52", name: "Швейцария" },
            { id: "12", name: "Шри-Ланка" },
            { id: "69", name: "Эстония" },
            { id: "70", name: "Южная Корея" },
            { id: "33", name: "Ямайка" },
            { id: "49", name: "Япония" }
        ];
    }

    setupEventHandlers() {
        // QR Code generation (only needed for first-time setup)
        this.client.on('qr', (qr) => {
            qrcode.generate(qr, { small: true });
            console.log('QR Code generated. Please scan with WhatsApp!');
        });

        // Ready event
        this.client.on('ready', () => {
            console.log('WhatsApp bot is ready!');
        });

        // Message handling
        this.client.on('message', async (msg) => {
            console.log(`Received message: ${msg.body} from ${msg.from}`); // Log received message
            if (msg.fromMe) return; // Ignore messages from the bot itself

            const userId = msg.from;
            if (!this.userData.has(userId)) {
                this.userData.set(userId, {}); // Initialize user data
                console.log(`New user detected: ${userId}`); // Log new user
                await msg.reply('Привет! Если вы хотите начать поиск тура, напишите "тур".');
            } else {
                await this.handleUserInput(msg);
            }
        });
    }

    async handleUserInput(msg) {
        const userId = msg.from;
        const userParams = this.userData.get(userId);

        console.log(`Handling user input for ${userId}: ${msg.body}`);
        console.log('Current user params:', userParams); // Add this to debug

        try {
            if (msg.body.toLowerCase() === 'тур') {
                userParams.awaitingDeparture = true;
                await this.askDeparture(msg);
            } else if (userParams.awaitingDeparture) {
                await this.collectParameters(msg);
            } else if (userParams.awaitingNights) {
                // Use default values if something goes wrong
                userParams.nights = { min: 7, max: 10 }; // Default medium stay
                userParams.awaitingNights = false;
                console.log('Using default nights range (7-10)');
                await this.askAdults(msg);
            } else if (userParams.awaitingAdults) {
                userParams.adults = '2'; // Default 2 adults
                userParams.awaitingAdults = false;
                await this.askChildren(msg);
            } else if (userParams.awaitingChildren) {
                userParams.children = '0'; // Default 0 children
                userParams.awaitingChildren = false;
                await this.startTourSearch(msg);
            } else {
                await msg.reply('Если вы хотите начать поиск тура, напишите "тур".');
            }
        } catch (error) {
            console.error('Error in handleUserInput:', error);
            // Use defaults and continue
            if (userParams.awaitingNights) {
                userParams.nights = { min: 7, max: 10 };
                userParams.awaitingNights = false;
                await this.askAdults(msg);
            } else if (userParams.awaitingAdults) {
                userParams.adults = '2';
                userParams.awaitingAdults = false;
                await this.askChildren(msg);
            } else if (userParams.awaitingChildren) {
                userParams.children = '0';
                userParams.awaitingChildren = false;
                await this.startTourSearch(msg);
            }
        }
    }

    async askDeparture(msg) {
        console.log('Asking for departure city code.'); // Log asking for departure
        await msg.reply('Введите код города вылета:');
    }

    async collectParameters(msg) {
        const userId = msg.from;
        const userParams = this.userData.get(userId);

        console.log(`Collecting parameters for user ${userId}: ${msg.body}`);

        if (!userParams.departure) {
            userParams.departure = msg.body;
            userParams.awaitingDeparture = false; // Clear the flag
            await this.askCountry(msg); // Ask for destination country
        } else if (userParams.awaitingCountry) {
            const input = msg.body.toLowerCase();
            const matchingCountries = this.countries.filter(c => c.name.toLowerCase().startsWith(input));

            if (matchingCountries.length > 0) {
                userParams.country = matchingCountries[0].id; // Use the first match
                userParams.awaitingCountry = false; // Clear the flag
                console.log(`Country code saved: ${userParams.country}`);
                await this.askNights(msg); // Ask for nights
            } else {
                // Check if the input matches a known city and map to country ID
                const cityToCountryMap = {
                    "дубай": "9", // UAE
                    // Add more city mappings here
                };

                const countryId = cityToCountryMap[input];
                if (countryId) {
                    userParams.country = countryId; // Use the mapped country ID
                    userParams.awaitingCountry = false; // Clear the flag
                    console.log(`Country code saved from city: ${userParams.country}`);
                    await this.askNights(msg); // Ask for nights
                } else {
                    await msg.reply('Страна не найдена. Пожалуйста, введите первые буквы названия страны или название города.');
                }
            }
        } else if (userParams.awaitingNights) {
            const nightsOption = msg.body;
            let nightsRange;

            switch (nightsOption) {
                case '1':
                    nightsRange = { min: 5, max: 7 }; // Short stay
                    break;
                case '2':
                    nightsRange = { min: 7, max: 10 }; // Medium stay
                    break;
                case '3':
                    nightsRange = { min: 10, max: 14 }; // Long stay
                    break;
                case '4':
                    nightsRange = { min: 14, max: 21 }; // Very long stay
                    break;
                default:
                    // If input is invalid, set default nights range
                    nightsRange = { min: 7, max: 10 }; // Default to Medium stay
                    await msg.reply('Вы ввели неверный вариант. Используем стандартный диапазон (7-10 ночей).');
                    break;
            }

            userParams.nights = nightsRange; // Store the nights range
            userParams.awaitingNights = false; // Clear the flag
            console.log(`Nights range saved: ${userParams.nights}`);
            await this.askAdults(msg); // Ask for adults
        } else if (userParams.awaitingAdults) {
            userParams.adults = msg.body; // Store adults
            userParams.awaitingAdults = false; // Clear the flag
            console.log(`Adults saved: ${userParams.adults}`);
            await this.askChildren(msg); // Ask for children
        } else if (userParams.awaitingChildren) {
            userParams.children = msg.body; // Store children
            userParams.awaitingChildren = false; // Clear the flag
            console.log(`Children saved: ${userParams.children}`);
            await this.startTourSearch(msg); // Proceed to search
        }
    }

    async askCountry(msg) {
        console.log('Asking for destination country.');
        await msg.reply('В какую страну вы хотите поехать? Введите первые буквы названия страны (например: "Тур" для Турции).');
        this.userData.get(msg.from).awaitingCountry = true; // Set flag
    }

    async askNights(msg) {
        console.log('Asking for number of nights.'); // Log asking for nights
        await msg.reply('Выберите количество ночей:\n' +
                        '1: Короткая (5-7 ночей)\n' +
                        '2: Средняя (7-10 ночей)\n' +
                        '3: Длинная (10-14 ночей)\n' +
                        '4: Очень длинная (14-21 ночь)');
        this.userData.get(msg.from).awaitingNights = true; // Set flag
    }

    async askAdults(msg) {
        console.log('Asking for number of adults.'); // Log asking for adults
        await msg.reply('Сколько взрослых будет в поездке?');
        this.userData.get(msg.from).awaitingAdults = true; // Set flag
    }

    async askChildren(msg) {
        console.log('Asking for number of children.'); // Log asking for children
        await msg.reply('Сколько детей будет в поездке?');
        this.userData.get(msg.from).awaitingChildren = true; // Set flag
    }

    async startTourSearch(msg) {
        const userId = msg.from;
        const userParams = this.userData.get(userId);
        
        console.log('Starting tour search with params:', userParams);

        const today = new Date();
        const dateFrom = new Date(today);
        dateFrom.setDate(today.getDate() + 1);
        const dateTo = new Date(today);
        dateTo.setDate(today.getDate() + 30);

        const formattedDateFrom = `${dateFrom.getDate().toString().padStart(2, '0')}.${(dateFrom.getMonth() + 1).toString().padStart(2, '0')}.${dateFrom.getFullYear()}`;
        const formattedDateTo = `${dateTo.getDate().toString().padStart(2, '0')}.${(dateTo.getMonth() + 1).toString().padStart(2, '0')}.${dateTo.getFullYear()}`;

        let nightsFrom, nightsTo;

        // Determine nights range based on user selection
        if (typeof userParams.nights === 'object') {
            nightsFrom = userParams.nights.min;
            nightsTo = userParams.nights.max;
        } else {
            nightsFrom = userParams.nights; // If it's a single number
            nightsTo = userParams.nights; // Same for single number
        }

        const apiUrl = `http://tourvisor.ru/xml/search.php?authlogin=admotionapp@gmail.com&authpass=jqVZ4QLNLBN5&departure=${userParams.departure}&country=${userParams.country}&datefrom=${formattedDateFrom}&dateto=${formattedDateTo}&nightsfrom=${nightsFrom}&nightsto=${nightsTo}&adults=${userParams.adults}&child=${userParams.children}&format=xml`;

        try {
            await msg.reply('Начинаем поиск туров...');
            const response = await axios.get(apiUrl);
            
            // Parse XML response
            const parser = new xml2js.Parser({ explicitArray: false });
            const result = await parser.parseStringPromise(response.data);
            
            if (result && result.result && result.result.requestid) {
                const requestId = result.result.requestid;
                console.log(`Request ID: ${requestId}`);
                // await msg.reply(`Поиск начат. ID запроса: ${requestId}`);
                await this.checkSearchStatus(requestId, msg);
            } else {
                console.error('Unexpected response structure:', result);
                await msg.reply('Произошла ошибка при получении ID запроса.');
            }
        } catch (error) {
            console.error('Error sending request to Tourvisor API:', error);
            await msg.reply('Произошла ошибка при отправке запроса на поиск туров.');
        }
    }

    async checkSearchStatus(requestId, msg) {
        const statusUrl = `http://tourvisor.ru/xml/result.php?authlogin=admotionapp@gmail.com&authpass=jqVZ4QLNLBN5&requestid=${requestId}&type=status`;

        try {
            const response = await axios.get(statusUrl);
            const parser = new xml2js.Parser({ explicitArray: false });
            const result = await parser.parseStringPromise(response.data);

            if (result.data && result.data.status) {
                const status = result.data.status;
                console.log('Search Status:', status);

                if (status.state === 'finished') {
                    await msg.reply(`Поиск завершен!\nНайдено отелей: ${status.hotelsfound}\nНайдено туров: ${status.toursfound}\nМинимальная цена: ${status.minprice} руб.`);
                    await this.getSearchResults(requestId, msg);
                } else {
                    await msg.reply(`Поиск продолжается...`);
                    // Check again in 5 seconds if not finished
                    setTimeout(() => this.checkSearchStatus(requestId, msg), 5000);
                }
            }
                            } catch (error) {
            console.error('Error checking search status:', error);
            await msg.reply('Произошла ошибка при проверке статуса поиска.');
        }
    }

    async getSearchResults(requestId, msg) {
        const resultsUrl = `http://tourvisor.ru/xml/result.php?authlogin=admotionapp@gmail.com&authpass=jqVZ4QLNLBN5&requestid=${requestId}&type=result`;

        try {
            const response = await axios.get(resultsUrl);
            const parser = new xml2js.Parser({ explicitArray: false });
            const result = await parser.parseStringPromise(response.data);

            if (result.data && result.data.result && result.data.result.hotel) {
                const hotels = Array.isArray(result.data.result.hotel) 
                    ? result.data.result.hotel 
                    : [result.data.result.hotel];

                // Send first 5 hotels info
                for (let i = 0; i < Math.min(5, hotels.length); i++) {
                    const hotel = hotels[i];
                    const tours = Array.isArray(hotel.tours.tour) 
                        ? hotel.tours.tour 
                        : [hotel.tours.tour];
                    
                    let message = `🏨 *${hotel.hotelname}* ${hotel.hotelstars}⭐\n`;
                    message += `📍 ${hotel.countryname}, ${hotel.regionname}\n`;
                    message += `💰 Цена от: ${hotel.price} руб.\n`;
                    message += `⭐ Рейтинг: ${hotel.hotelrating}\n`;
                    message += `📝 ${hotel.hoteldescription}\n\n`;
                    message += `🎫 Доступные туры:\n`;

                    // Add first 3 tours for this hotel
                    for (let j = 0; j < Math.min(3, tours.length); j++) {
                        const tour = tours[j];
                        message += `\n🔸 Вылет: ${tour.flydate}\n`;
                        message += `  ⌛ Ночей: ${tour.nights}\n`;
                        message += `  💶 Цена: ${tour.price} руб.\n`;
                        message += `  🍽 Питание: ${tour.mealrussian}\n`;
                    }

                    message += `\n🔗 Подробнее: http://manyhotels.ru/${hotel.fulldesclink}`;
                    await msg.reply(message);
                }

                await msg.reply('Это были первые 5 отелей из списка. Чтобы начать новый поиск, напишите "тур"');
            } else {
                await msg.reply('К сожалению, не удалось найти подходящие туры.');
            }
        } catch (error) {
            console.error('Error getting search results:', error);
            await msg.reply('Произошла ошибка при получении результатов поиска.');
        }
    }

    start() {
        console.log('Starting WhatsApp bot...');
        this.client.initialize()
            .then(() => console.log('Bot initialized successfully'))
            .catch(err => console.error('Failed to initialize bot:', err));
    }
}

// Create and start the bot
const bot = new WhatsAppBot();
bot.start(); 
