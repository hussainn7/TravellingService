from datetime import datetime, timedelta
import logging
from enum import Enum, auto
import json

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
    DONE = auto()

class TourChatbot:
    def __init__(self):
        self.state = ConversationState.INIT
        self.user_data = {}
        self.departure_cities = {
            "1": "Москва",
            "2": "Санкт-Петербург",
            "3": "Казань"
        }
        self.countries = {
            "1": "Египет",
            "2": "Турция",
            "3": "ОАЭ",
            "4": "Таиланд"
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

    def get_next_message(self, user_input=None):
        """Process user input and return next message"""
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
        
        options = "\n".join([f"{k}: {v}" for k, v in self.countries.items()])
        return f"🌍 В какую страну хотите поехать?\n{options}\n\nВведите номер страны:"

    def _handle_country(self, user_input):
        if user_input not in self.countries:
            options = "\n".join([f"{k}: {v}" for k, v in self.countries.items()])
            return f"Пожалуйста, выберите страну из списка:\n{options}"
        
        self.user_data['country'] = user_input
        self.state = ConversationState.ASK_TRIP_LENGTH

        # Set default dates (next week for 2 weeks)
        start_date = datetime.now() + timedelta(days=7)
        end_date = start_date + timedelta(days=14)
        self.user_data['date_from'] = start_date.strftime('%Y-%m-%d')
        self.user_data['date_to'] = end_date.strftime('%Y-%m-%d')
        
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
        start_date = datetime.strptime(self.user_data['date_from'], '%Y-%m-%d')
        end_date = datetime.strptime(self.user_data['date_to'], '%Y-%m-%d')
        
        return (
            "🎉 Отлично! Проверьте данные для поиска тура:\n\n"
            f"✈️ Вылет из: {self.departure_cities[self.user_data['departure']]}\n"
            f"🌍 Страна: {self.countries[self.user_data['country']]}\n"
            f"📅 Примерные даты: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n"
            f"🌙 Ночей: {self.user_data['nights_from']}-{self.user_data['nights_to']}\n"
            f"👥 Взрослых: {self.user_data['adults']}\n"
            f"👶 Детей: {self.user_data['children']}\n\n"
            "Начать поиск туров? (да/нет)"
        )

    def _handle_confirmation(self, user_input):
        if user_input.lower() in ['да', 'yes', 'y', '+']:
            self.state = ConversationState.SEARCHING
            return "SEARCH_READY", self.user_data
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