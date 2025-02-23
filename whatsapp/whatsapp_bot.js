const fs = require('fs');
const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');
const axios = require('axios'); // Import axios for making HTTP requests
const xml2js = require('xml2js'); // Import xml2js for XML parsing
require('dotenv').config(); // Load environment variables

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

        // Hardcoded API credentials
        this.OPENAI_API_KEY = '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';
        this.TOURVISOR_LOGIN = 'admotionapp@gmail.com'; // Replace with your actual login
        this.TOURVISOR_PASS = 'jqVZ4QLNLBN5'; // Replace with your actual password
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
            if (msg.fromMe) return; // Ignore messages from the bot itself
            await this.handleMessage(msg);
        });
    }

    async handleMessage(msg) {
        const userId = msg.from;
        console.log(`📩 Received message from user ${userId}: '${msg.body}'`);

        // Initialize user data if it doesn't exist
        if (!this.userData.has(userId)) {
            this.userData.set(userId, {
                isSearching: false,
                awaitingDeparture: false,
                awaitingCountry: false,
                awaitingNights: false,
                awaitingAdults: false,
                awaitingChildren: false,
                departure: null,
                country: null,
                nights: null,
                adults: null,
                children: null
            });
            // Send welcome message for new users
            await msg.reply('👋 Здравствуйте! Я ваш турагент-помощник. Я могу помочь вам найти подходящий тур или ответить на ваши вопросы о путешествиях.\n\nЧтобы начать поиск тура, просто напишите "тур".');
            return;
        }

        const userParams = this.userData.get(userId);

        // Check if user is in tour search mode
        if (msg.body.toLowerCase() === 'тур') {
            userParams.isSearching = true;
            userParams.awaitingDeparture = true;
            await this.askDeparture(msg);
            return;
        }

        // If user is in search mode, handle tour search flow
        if (userParams.isSearching) {
            await this.handleTourSearch(msg, userParams);
        } else {
            // Use AI for general conversation
            const response = await this.getChatGPTResponse(msg.body);
            await msg.reply(response);
        }
    }

    async handleTourSearch(msg, userParams) {
        try {
            if (userParams.awaitingDeparture) {
                userParams.departure = msg.body; // Store the city name
                userParams.awaitingDeparture = false;
                userParams.awaitingCountry = true;
                await this.askCountry(msg);
            } else if (userParams.awaitingCountry) {
                const cityName = msg.body.trim();
                const countryId = await this.getCountryIdFromCity(cityName);
                if (countryId) {
                    userParams.country = countryId; // Store the country ID
                    userParams.awaitingCountry = false;
                    userParams.awaitingNights = true;
                    await this.askNights(msg);
                } else {
                    await msg.reply('😔 Не удалось распознать страну по городу. Пожалуйста, попробуйте снова или введите страну.');
                }
            } else if (userParams.awaitingNights) {
                const nights = msg.body.split('-').map(Number);
                if (nights.length === 2) {
                    userParams.nights = nights; // Store as an array [nightsFrom, nightsTo]
                    userParams.awaitingNights = false;
                    userParams.awaitingAdults = true;
                    await this.askAdults(msg);
                } else {
                    await msg.reply('Пожалуйста, введите количество ночей в формате "X-Y", например "7-14".');
                }
            } else if (userParams.awaitingAdults) {
                userParams.adults = msg.body;
                userParams.awaitingAdults = false;
                userParams.awaitingChildren = true;
                await this.askChildren(msg);
            } else if (userParams.awaitingChildren) {
                userParams.children = msg.body;
                userParams.awaitingChildren = false;
                await this.confirmSearch(msg, userParams);
            }
        } catch (error) {
            console.error('Error in handleTourSearch:', error);
            await msg.reply('Произошла ошибка. Пожалуйста, напишите "тур" для начала поиска заново.');
            this.resetUserState(msg.from);
        }
    }

    async confirmSearch(msg, userParams) {
        console.log(`Starting search with the following parameters:`);
        console.log(`Departure: ${userParams.departure}`); // This is the city name
        console.log(`Country ID: ${userParams.country}`); // This should be the country ID
        console.log(`Nights: ${userParams.nights.join('-')}`);
        console.log(`Adults: ${userParams.adults}`);
        console.log(`Children: ${userParams.children}`);

        await msg.reply('Хорошо, начинаем поиск...');

        // Proceed to start the tour search
        const requestId = await this.startTourSearch(msg, userParams);
        if (requestId) {
            await this.getSearchResults(requestId, msg); // Directly get results
        }
    }

    async formatSearchRequest(userParams) {
        const today = new Date();
        const dateFrom = new Date(today);
        dateFrom.setDate(today.getDate() + 1);
        const dateTo = new Date(today);
        dateTo.setDate(today.getDate() + 30);

        const formattedDateFrom = `${dateFrom.getDate().toString().padStart(2, '0')}.${(dateFrom.getMonth() + 1).toString().padStart(2, '0')}.${dateFrom.getFullYear()}`;
        const formattedDateTo = `${dateTo.getDate().toString().padStart(2, '0')}.${(dateTo.getMonth() + 1).toString().padStart(2, '0')}.${dateTo.getFullYear()}`;

        return `http://tourvisor.ru/xml/search.php?authlogin=${this.TOURVISOR_LOGIN}&authpass=${this.TOURVISOR_PASS}&departure=${userParams.country}&country=${userParams.country}&datefrom=${formattedDateFrom}&dateto=${formattedDateTo}&nightsfrom=${userParams.nights[0]}&nightsto=${userParams.nights[1]}&adults=${userParams.adults}&child=${userParams.children}&format=xml`;
    }

    async startTourSearch(msg, userParams) {
        const apiUrl = await this.formatSearchRequest(userParams);
        console.log(`Making API request to: ${apiUrl}`);

        try {
            const response = await axios.get(apiUrl);
            console.log(`API Response: ${response.data}`);
            const result = await this.parseApiResponse(response.data);
            return result.requestid; // Return the request ID for direct result fetching
        } catch (error) {
            console.error('Error making API request:', error);
            await msg.reply('Произошла ошибка при отправке запроса на поиск туров.');
            return null;
        }
    }

    async getSearchResults(requestId, msg) {
        const resultsUrl = `http://tourvisor.ru/xml/result.php?authlogin=${this.TOURVISOR_LOGIN}&authpass=${this.TOURVISOR_PASS}&requestid=${requestId}&type=result`;
        console.log(`Fetching results from: ${resultsUrl}`); // Print the result link

        // Set a timeout for the request
        const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 15000));

        try {
            const response = await Promise.race([
                axios.get(resultsUrl),
                timeout
            ]);
            console.log(`Results Response: ${response.data}`);
            await this.handleResults(response.data, msg);
        } catch (error) {
            console.error('Error fetching results:', error);
            await msg.reply('Произошла ошибка при получении результатов поиска. Пожалуйста, попробуйте позже.');
        }
    }

    async handleResults(xmlData, msg) {
        const parser = new xml2js.Parser();
        parser.parseString(xmlData, (err, result) => {
            if (err) {
                console.error('Error parsing results:', err);
                msg.reply('Не удалось обработать результаты поиска.');
                return;
            }

            // Check if the result contains hotels
            const hotels = result.data.result[0].hotel;
            if (hotels && hotels.length > 0) {
                let responseMessage = '🏨 Найденные отели:\n';
                hotels.forEach(hotel => {
                    const hotelName = hotel.hotelname[0];
                    const price = hotel.price[0];
                    const description = hotel.hoteldescription[0];
                    const fullDescLink = hotel.fulldesclink[0];

                    // Extracting fly dates from tours
                    const tours = hotel.tours[0].tour;
                    const flyDates = tours.map(tour => tour.flydate[0]).join(', ');

                    responseMessage += `\n🏨 Название: ${hotelName}\n💰 Цена: ${price} руб.\n✈️ Даты вылета: ${flyDates}\n📝 Описание: ${description}\n🔗 Полное описание: ${fullDescLink}\n`;
                });
                msg.reply(responseMessage);
            } else {
                msg.reply('😔 К сожалению, отели не найдены по вашему запросу.');
            }
        });
    }

    async parseApiResponse(xmlData) {
        const parser = new xml2js.Parser();
        return new Promise((resolve, reject) => {
            parser.parseString(xmlData, (err, result) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(result.result);
                }
            });
        });
    }

    async getCountryIdFromCity(cityName) {
        // Predefined mapping of cities to country IDs
        const cityCountryMap = {
            "Москва": 4,
            "Санкт-Петербург": 4,
            "Хургада": 1,
            "Анталия": 4,
            "Турция": 4,
            // Add more cities and their corresponding country IDs as needed
        };

        // Check if the city is in the predefined list
        if (cityCountryMap[cityName]) {
            return cityCountryMap[cityName];
        } else {
            // If not found, use ChatGPT to find the country
            const countryId = await this.getCountryIdFromChatGPT(cityName);
            return countryId;
        }
    }

    async getCountryIdFromChatGPT(cityName) {
        const apiKey = this.OPENAI_API_KEY; // Use the hardcoded OpenAI API key
        const endpoint = 'https://api.openai.com/v1/chat/completions';

        try {
            const response = await axios.post(endpoint, {
                model: 'gpt-3.5-turbo',
                messages: [
                    { 
                        role: 'system', 
                        content: 'You are a helpful assistant. Given a city name, provide the corresponding country ID from the predefined list.'
                    },
                    { 
                        role: 'user', 
                        content: `What is the country ID for the city: ${cityName}?`
                    }
                ],
            }, {
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                },
            });

            // Extract the country ID from the response
            const countryId = response.data.choices[0].message.content; // Adjust based on the expected response format
            return countryId;
        } catch (error) {
            console.error('Error connecting to ChatGPT:', error);
            return null; // Return null if there is an error
        }
    }

    async getChatGPTResponse(userMessage) {
        const apiKey = this.OPENAI_API_KEY; // Use the hardcoded OpenAI API key
        const endpoint = 'https://api.openai.com/v1/chat/completions';

        try {
            const response = await axios.post(endpoint, {
                model: 'gpt-3.5-turbo',
                messages: [
                    { 
                        role: 'system', 
                        content: 'You are a helpful travel agent assistant. Provide friendly and informative responses about travel-related questions. If someone asks about booking a tour, remind them they can type "тур" to start the booking process.'
                    },
                    { 
                        role: 'user', 
                        content: userMessage 
                    }
                ],
            }, {
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                },
            });

            return response.data.choices[0].message.content;
        } catch (error) {
            console.error('Error connecting to ChatGPT:', error);
            return "🚨 Извините, произошла ошибка при обращении к ChatGPT. Проверьте ваш API ключ и попробуйте позже.";
        }
    }

    async askDeparture(msg) {
        await msg.reply('🏙️ Из какого города вы хотите вылететь?');
    }

    async askCountry(msg) {
        await msg.reply('🌍 В какую страну вы хотите поехать?');
    }

    async askNights(msg) {
        await msg.reply('⌛ На сколько ночей планируете поездку?');
    }

    async askAdults(msg) {
        await msg.reply('👥 Сколько взрослых поедет? (введите число от 1 до 6)');
    }

    async askChildren(msg) {
        await msg.reply('👶 Сколько детей поедет? (введите число от 0 до 4)');
    }

    resetUserState(userId) {
        this.userData.set(userId, {
            isSearching: false,
            awaitingDeparture: false,
            awaitingCountry: false,
            awaitingNights: false,
            awaitingAdults: false,
            awaitingChildren: false,
            departure: null,
            country: null,
            nights: null,
            adults: null,
            children: null
        });
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
