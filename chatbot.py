from datetime import datetime, timedelta
import logging
from enum import Enum, auto
import json
from thefuzz import fuzz
from thefuzz import process
import pycountry
from typing import Dict, Tuple
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationState(Enum):
    INIT = auto()
    ASK_DEPARTURE = auto()
    ASK_COUNTRY = auto()
    ASK_TRIP_LENGTH = auto()
    ASK_ADULTS = auto()
    ASK_CHILDREN = auto()
    CONFIRM = auto()
    SEARCHING = auto()
    GENERAL_CHAT = auto()  # New state for general chat
    DONE = auto()

class TourChatbot:
    def __init__(self):
        self.state = ConversationState.INIT
        self.user_data = {}
        self.chat_history = []  # Store chat history for context
        self.departure_cities = {
            "1": "Москва",
            "2": "Санкт-Петербург",
            "3": "Казань"
        }
        self.countries = {
            "46": "Абхазия",
            "31": "Австрия",
            "55": "Азербайджан",
            "71": "Албания",
            "17": "Андорра",
            "88": "Аргентина",
            "53": "Армения",
            "72": "Аруба",
            "59": "Бахрейн",
            "57": "Беларусь",
            "20": "Болгария",
            "39": "Бразилия",
            "44": "Великобритания",
            "37": "Венгрия",
            "90": "Венесуэла",
            "16": "Вьетнам",
            "38": "Германия",
            "6": "Греция",
            "54": "Грузия",
            "11": "Доминикана",
            "1": "Египет",
            "30": "Израиль",
            "3": "Индия",
            "7": "Индонезия",
            "29": "Иордания",
            "92": "Иран",
            "14": "Испания",
            "24": "Италия",
            "78": "Казахстан",
            "40": "Камбоджа",
            "79": "Катар",
            "51": "Кения",
            "15": "Кипр",
            "60": "Киргизия",
            "13": "Китай",
            "10": "Куба",
            "80": "Ливан",
            "27": "Маврикий",
            "36": "Малайзия",
            "8": "Мальдивы",
            "50": "Мальта",
            "23": "Марокко",
            "18": "Мексика",
            "81": "Мьянма",
            "82": "Непал",
            "9": "ОАЭ",
            "64": "Оман",
            "87": "Панама",
            "35": "Португалия",
            "47": "Россия",
            "93": "Саудовская Аравия",
            "28": "Сейшелы",
            "58": "Сербия",
            "25": "Сингапур",
            "43": "Словения",
            "2": "Таиланд",
            "41": "Танзания",
            "5": "Тунис",
            "4": "Турция",
            "56": "Узбекистан",
            "26": "Филиппины",
            "34": "Финляндия",
            "32": "Франция",
            "22": "Хорватия",
            "21": "Черногория",
            "19": "Чехия",
            "52": "Швейцария",
            "12": "Шри-Ланка",
            "69": "Эстония",
            "70": "Южная Корея",
            "33": "Ямайка",
            "49": "Япония"
        }
        self.trip_lengths = {
            "1": "Короткая (5-7 ночей)",
            "2": "Средняя (7-10 ночей)",
            "3": "Длинная (10-14 ночей)",
            "4": "Очень длинная (14-21 ночь)"
        }
        self.trip_length_mapping = {
            "1": (5, 7),
            "2": (7, 10),
            "3": (10, 14),
            "4": (14, 21)
        }
        
        # Create reverse mapping and common variations
        self.country_variations = self._create_country_variations()

    def _create_country_variations(self) -> Dict[str, str]:
        """Create a dictionary of country name variations mapping to their IDs"""
        variations = {}
        
        # Common variations and abbreviations
        special_cases = {
            "оаэ": "9",
            "эмираты": "9",
            "дубай": "9",
            "dubai": "9",
            "uk": "44",
            "usa": "44",
            "uae": "9",
            "доминикана": "11",
            "dom": "11",
            "тай": "2",
            "тайланд": "2",
            "thai": "2",
            "egypt": "1",
            "егип": "1",
            "турц": "4",
            "turkey": "4",
            "greek": "6",
            "греч": "6",
            "кипр": "15",
            "cyprus": "15",
            "бали": "7",
            "bali": "7",
            "мальд": "8",
            "mald": "8",
            "шри": "12",
            "sri": "12",
        }
        
        # Add original names
        for id, name in self.countries.items():
            variations[name.lower()] = id
            # Add English name if available
            if country := pycountry.countries.get(name=name):
                variations[country.name.lower()] = id
            
        # Add special cases
        variations.update(special_cases)
        
        return variations

    async def _detect_country(self, user_input: str) -> Tuple[str, float]:
        """
        Detect country from user input using multiple methods:
        1. Direct match with variations
        2. Fuzzy matching
        3. AI interpretation as fallback
        """
        user_input = user_input.lower().strip()
        
        # 1. Direct match with variations
        if user_input in self.country_variations:
            return self.country_variations[user_input], 1.0
            
        # 2. Fuzzy matching
        matches = process.extractBests(
            user_input,
            self.country_variations.keys(),
            scorer=fuzz.ratio,
            score_cutoff=80
        )
        
        if matches:
            best_match = matches[0]
            return self.country_variations[best_match[0]], best_match[1] / 100
            
        # 3. AI interpretation as fallback
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Вы - туристический ассистент. Получив ввод пользователя о стране, сопоставьте его с одной из этих стран: {', '.join(self.countries.values())}. Отвечайте ТОЛЬКО точным названием страны из списка или 'неизвестно', если совпадений нет. Всегда отвечайте на русском языке."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            suggested_country = response.choices[0].message.content.strip()
            
            if suggested_country.lower() in self.country_variations:
                return self.country_variations[suggested_country.lower()], 0.8
                
        except Exception as e:
            logging.error(f"Error using OpenAI API: {e}")
            
        return None, 0.0

    async def handle_general_chat(self, user_input: str) -> str:
        """Handle general chat after tour search is complete"""
        try:
            # Add user message to history
            self.chat_history.append({"role": "user", "content": user_input})
            
            # Prepare the messages with context
            messages = [
                {"role": "system", "content": (
                    "Вы - опытный туристический ассистент. Вы можете обсуждать все аспекты путешествий, "
                    "и особенно хорошо разбираетесь в следующих темах:\n"
                    "1. Страны и направления в нашем каталоге туров\n"
                    "2. Советы и рекомендации по путешествиям\n"
                    "3. Местные обычаи и культура\n"
                    "4. Лучшее время для посещения\n"
                    "5. Что взять с собой и как подготовиться\n"
                    "6. Визовые требования\n"
                    "7. Местные достопримечательности и развлечения\n\n"
                    f"Пользователь только что искал туры в {self.countries.get(self.user_data.get('country', ''), 'направление')}. "
                    "Будьте полезны и дружелюбны, предоставляйте конкретную и актуальную информацию. "
                    "Всегда отвечайте на русском языке."
                )}
            ]
            
            # Add relevant chat history (last 5 exchanges)
            messages.extend(self.chat_history[-10:])
            
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add assistant response to history
            self.chat_history.append({"role": "assistant", "content": assistant_response})
            
            # Add helpful suggestions for continuing the conversation
            suggestions = [
                "\n\nВы также можете спросить меня о:",
                "🏨 Отелях и их особенностях",
                "🌍 Достопримечательностях",
                "🎫 Визах и документах",
                "🌡️ Погоде и лучшем времени для поездки",
                "💰 Ценах и расходах",
                "🍴 Местной кухне",
                "🚗 Транспорте и передвижении",
                "\nИли начать новый поиск туров! (напишите 'новый поиск')"
            ]
            
            return assistant_response + "\n\n" + "\n".join(suggestions)
            
        except Exception as e:
            logging.error(f"Error in general chat: {e}")
            return "Извините, произошла ошибка. Давайте попробуем еще раз или начнем новый поиск туров?"

    def get_next_message(self, user_input=None):
        """Process user input and return next message"""
        if user_input and user_input.lower() in ['новый поиск', 'new search']:
            self.state = ConversationState.INIT
            self.user_data = {}
            self.chat_history = []
            return self._format_departure_question()

        if self.state == ConversationState.INIT:
            self.state = ConversationState.ASK_DEPARTURE
            return self._format_departure_question()

        if user_input is None:
            return self._get_current_question()

        try:
            if self.state == ConversationState.ASK_DEPARTURE:
                return self._handle_departure(user_input)
            elif self.state == ConversationState.ASK_COUNTRY:
                return self._handle_country(user_input)
            elif self.state == ConversationState.ASK_TRIP_LENGTH:
                return self._handle_trip_length(user_input)
            elif self.state == ConversationState.ASK_ADULTS:
                return self._handle_adults(user_input)
            elif self.state == ConversationState.ASK_CHILDREN:
                return self._handle_children(user_input)
            elif self.state == ConversationState.CONFIRM:
                return self._handle_confirmation(user_input)
        except ValueError as e:
            return str(e)

        return "Извините, я не понял ваш ответ. Попробуйте еще раз."

    def _format_departure_question(self):
        options = "\n".join([f"{k}: {v}" for k, v in self.departure_cities.items()])
        return f"👋 Привет! Я помогу вам найти идеальный тур.\n\nОткуда вы хотите вылететь?\n{options}\n\nВведите номер города:"

    def _handle_departure(self, user_input):
        if user_input not in self.departure_cities:
            return f"Пожалуйста, выберите город из списка:\n{self._format_departure_question()}"
        
        self.user_data['departure'] = user_input
        self.state = ConversationState.ASK_COUNTRY
        
        return (
            "🌍 В какую страну хотите поехать?\n\n"
            "Просто напишите название страны, например:\n"
            "- Турция\n"
            "- ОАЭ\n"
            "- Таиланд\n\n"
            "Я пойму даже неточные названия и сокращения!"
        )

    async def _handle_country(self, user_input):
        country_id, confidence = await self._detect_country(user_input)
        
        if not country_id or confidence < 0.6:
            return (
                "🤔 Извините, я не уверен, какую страну вы имели в виду.\n"
                "Пожалуйста, попробуйте написать название страны более точно.\n"
                "Например: Турция, ОАЭ, Таиланд, и т.д."
            )
        
        if confidence < 0.8:
            country_name = self.countries[country_id]
            return f"🤔 Вы имели в виду {country_name}? (да/нет)"
            
        self.user_data['country'] = country_id
        self.state = ConversationState.ASK_TRIP_LENGTH
        
        options = "\n".join([f"{k}: {v}" for k, v in self.trip_lengths.items()])
        return f"⌛ Какой длительности тур вы предпочитаете?\n{options}\n\nВведите номер варианта:"

    def _handle_trip_length(self, user_input):
        if user_input not in self.trip_lengths:
            options = "\n".join([f"{k}: {v}" for k, v in self.trip_lengths.items()])
            return f"Пожалуйста, выберите длительность из списка:\n{options}"
        
        nights_from, nights_to = self.trip_length_mapping[user_input]
        self.user_data['nights_from'] = nights_from
        self.user_data['nights_to'] = nights_to
        self.state = ConversationState.ASK_ADULTS
        
        return "👥 Сколько взрослых поедет? (введите число от 1 до 6):"

    def _handle_adults(self, user_input):
        try:
            adults = int(user_input)
            if adults < 1 or adults > 6:
                return "Количество взрослых должно быть от 1 до 6. Попробуйте еще раз:"
            
            self.user_data['adults'] = adults
            self.state = ConversationState.ASK_CHILDREN
            
            return "👶 Сколько детей поедет? (введите число от 0 до 4):"
        except ValueError:
            return "Пожалуйста, введите число от 1 до 6:"

    def _handle_children(self, user_input):
        try:
            children = int(user_input)
            if children < 0 or children > 4:
                return "Количество детей должно быть от 0 до 4. Попробуйте еще раз:"
            
            self.user_data['children'] = children
            self.state = ConversationState.CONFIRM
            
            return self._format_confirmation_message()
        except ValueError:
            return "Пожалуйста, введите число от 0 до 4:"

    def _format_confirmation_message(self):
        start_date = datetime.now() + timedelta(days=1)  # Tomorrow
        end_date = start_date + timedelta(days=30)       # Tomorrow + 30 days
        
        return (
            "🎉 Отлично! Проверьте данные для поиска тура:\n\n"
            f"✈️ Вылет из: {self.departure_cities[self.user_data['departure']]}\n"
            f"🌍 Страна: {self.countries[self.user_data['country']]}\n"
            f"📅 Даты поиска: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n"
            f"🌙 Ночей: {self.user_data['nights_from']}-{self.user_data['nights_to']}\n"
            f"👥 Взрослых: {self.user_data['adults']}\n"
            f"👶 Детей: {self.user_data['children']}\n\n"
            "Начать поиск туров? (да/нет)"
        )

    def _handle_confirmation(self, user_input):
        if user_input.lower() in ['да', 'yes', 'y', '+']:
            self.state = ConversationState.SEARCHING
            
            # Format dates for the search
            start_date = datetime.now() + timedelta(days=1)  # Tomorrow
            end_date = start_date + timedelta(days=30)      # Tomorrow + 30 days
            
            # Prepare search parameters
            search_params = {
                'departure': self.user_data['departure'],
                'country': self.user_data['country'],
                'date_from': start_date.strftime('%Y-%m-%d'),
                'date_to': end_date.strftime('%Y-%m-%d'),
                'nights_from': self.user_data['nights_from'],
                'nights_to': self.user_data['nights_to'],
                'adults': self.user_data['adults'],
                'children': self.user_data['children']
            }
            
            # Return signal to start search with parameters
            return "SEARCH_READY", search_params
            
        elif user_input.lower() in ['нет', 'no', 'n', '-']:
            self.state = ConversationState.INIT
            self.user_data = {}
            return "Хорошо, давайте начнем сначала.\n" + self._format_departure_question()
        else:
            return "Пожалуйста, ответьте 'да' или 'нет':"

    def _get_current_question(self):
        """Get the current question based on state"""
        if self.state == ConversationState.ASK_DEPARTURE:
            return self._format_departure_question()
        elif self.state == ConversationState.ASK_COUNTRY:
            options = "\n".join([f"{k}: {v}" for k, v in self.countries.items()])
            return f"🌍 В какую страну хотите поехать?\n{options}"
        elif self.state == ConversationState.ASK_TRIP_LENGTH:
            options = "\n".join([f"{k}: {v}" for k, v in self.trip_lengths.items()])
            return f"⌛ Какой длительности тур вы предпочитаете?\n{options}"
        elif self.state == ConversationState.ASK_ADULTS:
            return "👥 Сколько взрослых поедет? (введите число от 1 до 6):"
        elif self.state == ConversationState.ASK_CHILDREN:
            return "👶 Сколько детей поедет? (введите число от 0 до 4):"
        elif self.state == ConversationState.CONFIRM:
            return self._format_confirmation_message()
        return "Извините, произошла ошибка. Давайте начнем сначала."

    def reset(self):
        """Reset the conversation state"""
        self.state = ConversationState.INIT
        self.user_data = {}

    def start_tour_search(self, departure, country, datefrom, dateto, trip_length, adults, children):
        # Set user data based on input
        self.user_data['departure'] = departure
        self.user_data['country'] = country
        self.user_data['date_from'] = datefrom
        self.user_data['date_to'] = dateto
        self.user_data['nights_from'], self.user_data['nights_to'] = self.trip_length_mapping[trip_length]
        self.user_data['adults'] = adults
        self.user_data['children'] = children

        # Proceed to search
        return self._handle_confirmation("да")  # Automatically confirm for demonstration

    async def handle_tour_search(self, chat_id: str):
        """Handle tour search requests"""
        search_params = {
            'departure': self.user_data['departure'],
            'country': self.user_data['country'],
            'date_from': self.user_data['date_from'],
            'date_to': self.user_data['date_to'],
            'nights_from': self.user_data['nights_from'],
            'nights_to': self.user_data['nights_to'],
            'adults': self.user_data['adults'],
            'children': self.user_data['children']
        }

        logger.info(f"Starting tour search for chat {chat_id} with params: {search_params}")
        request_id = await self.tourvisor.search_tours(search_params)
        if request_id:
            results = await self.tourvisor.get_results(request_id)
            if results:
                return format_tour_results(results)
            else:
                return "😔 Не удалось получить результаты поиска."
        else:
            return "😔 Не удалось инициировать поиск туров." 
