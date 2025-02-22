from chatbot import TourChatbot, ConversationState
import asyncio
import logging
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from instagrapi import Client
import time

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class InstagramTourBot:
    def __init__(self):
        self.chatbot = TourChatbot()
        self.memory = {}  # Store conversation state for each user
        self.tour_search = None
        self.client = Client()
        self.last_check = datetime.now()
        
        # Login to Instagram
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        if not username or not password:
            raise ValueError("Instagram credentials not found in environment variables")
            
        print(f"🔄 Attempting to login as {username}...")
        self.client.login(username, password)
        print(f"✅ Successfully logged in as {username}")
        logger.info(f"Bot initialized and logged in as {username}")

    def _get_user_state(self, user_id):
        """Get or create state for a user"""
        if user_id not in self.memory:
            logger.info(f"Creating new state for user {user_id}")
            print(f"👤 New user detected (ID: {user_id})")
            self.memory[user_id] = {
                'chatbot': TourChatbot(),
                'last_message': None
            }
        return self.memory[user_id]

    async def _handle_message(self, thread_id, user_id, message_text):
        """Handle a single message from a user"""
        print(f"\n📩 Received message from user {user_id} in thread {thread_id}")
        print(f"Message content: '{message_text}'")
        
        user_state = self._get_user_state(user_id)
        chatbot = user_state['chatbot']
        
        print(f"Current chat state: {chatbot.state}")
        
        # Handle "new search" command
        if message_text.lower() in ['новый поиск', 'new search']:
            print("🔄 User requested new search")
            chatbot.reset()
            response = chatbot.get_next_message()
            print(f"🤖 Sending response: '{response}'")
            self.client.direct_answer(thread_id, response)
            return

        # Handle different states appropriately
        if chatbot.state == ConversationState.ASK_COUNTRY:
            print("🌍 Processing country input")
            response = await chatbot._handle_country(message_text)
        elif chatbot.state == ConversationState.GENERAL_CHAT:
            print("💭 Processing general chat")
            response = await chatbot.handle_general_chat(message_text)
        else:
            print(f"⚡ Processing state: {chatbot.state}")
            response = chatbot.get_next_message(message_text)

        # Handle search initiation
        if isinstance(response, tuple) and response[0] == "SEARCH_READY":
            print("🔍 Starting tour search...")
            self.client.direct_answer(thread_id, "🔍 Начинаю поиск туров...")
            
            search_params = response[1]
            print(f"Search parameters: {json.dumps(search_params, indent=2, ensure_ascii=False)}")
            
            search_result = await self._search_tours(search_params)
            
            # Split long messages if needed (Instagram has character limits)
            if len(search_result) > 2000:
                print("📝 Splitting long message into chunks")
                # First send the intro message
                intro_message = "🏨 Вот что я нашел для вас! Отправляю результаты частями..."
                self.client.direct_send(intro_message, thread_ids=[thread_id])
                
                # Split message into smaller chunks, being careful with the splits
                chunks = []
                current_chunk = ""
                
                # Split by hotel (split by the separator line)
                hotels = search_result.split("─" * 30)
                
                for hotel in hotels:
                    if not hotel.strip():
                        continue
                        
                    # If current chunk plus this hotel would be too long, save current chunk
                    if len(current_chunk) + len(hotel) > 1800:  # Using 1800 to be safe
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = hotel
                    else:
                        current_chunk += hotel + "\n" + "─" * 30 + "\n"
                
                # Add the last chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Send each chunk with a delay to avoid rate limits
                for i, chunk in enumerate(chunks, 1):
                    print(f"Sending chunk {i}/{len(chunks)}")
                    try:
                        # Add chunk number for better readability
                        numbered_chunk = f"Часть {i}/{len(chunks)}:\n\n{chunk}"
                        self.client.direct_send(numbered_chunk, thread_ids=[thread_id])
                        await asyncio.sleep(1)  # Small delay between chunks
                    except Exception as e:
                        print(f"Error sending chunk {i}: {e}")
                        await asyncio.sleep(5)  # Longer delay if there's an error
                        try:
                            # Try one more time
                            self.client.direct_send(numbered_chunk, thread_ids=[thread_id])
                        except:
                            print(f"Failed to send chunk {i} after retry")
                
                # Send final message
                self.client.direct_send("Это все результаты! Для нового поиска напишите 'новый поиск'", thread_ids=[thread_id])
            else:
                print("📤 Sending search results")
                self.client.direct_send(search_result, thread_ids=[thread_id])
            
            # Reset chatbot for new search
            chatbot.reset()
            new_response = chatbot.get_next_message()
            self.client.direct_send("\nДля нового поиска напишите 'новый поиск'", thread_ids=[thread_id])
        else:
            # Send normal response
            print(f"🤖 Sending response: '{response}'")
            self.client.direct_answer(thread_id, response)

    async def _search_tours(self, search_params):
        """Execute tour search and return formatted results"""
        try:
            print("\n🔍 Starting tour search with parameters:")
            print(json.dumps(search_params, indent=2, ensure_ascii=False))
            
            # Create initial search request
            from tour_search import TourSearch
            if not self.tour_search:
                self.tour_search = TourSearch()
            
            # Format dates in DD.MM.YYYY format
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            end_date = tomorrow + timedelta(days=30)
            
            search_request = {
                'departure': search_params['departure'],
                'country': search_params['country'],
                'datefrom': tomorrow.strftime('%d.%m.%Y'),
                'dateto': end_date.strftime('%d.%m.%Y'),
                'nightsfrom': search_params.get('nights_from', 7),
                'nightsto': search_params.get('nights_to', 14),
                'adults': search_params.get('adults', 2),
                'child': search_params.get('children', 0),
                'format': 'xml'
            }
            
            print("📤 Making API request for tour search")
            logger.info(f"Search request: {search_request}")
            
            # Create search request
            request_id = self.tour_search.create_search_request(search_request)
            if not request_id:
                print("❌ Failed to create search request")
                return "😔 Извините, не удалось выполнить поиск. Попробуйте позже."
            
            if isinstance(request_id, dict) and "error" in request_id:
                print(f"❌ Error in search request: {request_id['error']}")
                return f"❌ Ошибка при поиске: {request_id['error']}"
            
            print(f"✅ Search request created with ID: {request_id}")
            
            # Wait and check status until search is complete or timeout
            max_attempts = 24
            min_hotels_threshold = 10
            min_tours_threshold = 30
            
            for attempt in range(max_attempts):
                await asyncio.sleep(2.5)
                print(f"\r⏳ Checking search status (attempt {attempt + 1}/{max_attempts})", end='')
                
                try:
                    status = self.tour_search.get_search_status(request_id)
                    if not status:
                        continue
                    
                    state = status.get('state')
                    hotels_found = int(status.get('hotelsfound', '0'))
                    tours_found = int(status.get('toursfound', '0'))
                    
                    print(f"\r🔄 Status: {state} | Hotels: {hotels_found} | Tours: {tours_found}")
                    
                    if state == 'finished' or (
                        hotels_found >= min_hotels_threshold and 
                        tours_found >= min_tours_threshold
                    ):
                        print("\n✅ Search completed successfully")
                        break
                    elif state == 'error':
                        print("\n❌ Search ended with error")
                        return "😔 Произошла ошибка при поиске туров."
                    
                    if attempt == max_attempts - 1:
                        print("\n⌛ Search timed out")
                        return "⏳ Поиск занял слишком много времени. Попробуйте позже."
                except Exception as e:
                    logger.error(f"Error checking status: {e}")
                    print(f"\n⚠️ Error checking status: {e}")
                    continue
            
            # Get final results
            print("📥 Fetching search results")
            results = self.tour_search.get_search_results(request_id)


            if not results or 'result' not in results or 'hotels' not in results['result']:
                print("❌ No results found in response")
                return "😔 Не удалось получить результаты поиска."
            
            hotels = results['result']['hotels']
            if not hotels:
                print("🔍 No hotels found in search results")
                return "🔍 По вашему запросу туров не найдено."
            
            print(f"✅ Found {len(hotels)} hotels")
            
            # Sort hotels by price
            hotels.sort(key=lambda x: float(x.get('price', '999999999')))
            
            # Format results message
            status = results.get('status', {})
            message = (
                f"🎯 Найдено {status.get('hotelsfound', len(hotels))} отелей и "
                f"{status.get('toursfound', '0')} туров!\n"
                f"💰 Цены от {int(float(status.get('minprice', '0'))):,} ₽\n\n"
            )
            
            # Show top 5 hotels
            print("📝 Formatting top 5 hotels")
            for i, hotel in enumerate(hotels[:5], 1):
                name = hotel.get('hotelname', 'Отель')
                stars = "⭐" * int(hotel.get('hotelstars', '0'))
                price = int(float(hotel.get('price', '0')))
                country = hotel.get('countryname', '')
                region = hotel.get('regionname', '')
                rating = float(hotel.get('hotelrating', '0'))
                
                print(f"Processing hotel {i}: {name}")
                
                message += f"{i}. {name} {stars}\n"
                if rating > 0:
                    message += f"📊 Рейтинг: {rating:.1f}/5\n"
                message += f"📍 {country}, {region}\n"
                message += f"💰 От {price:,} ₽\n"
                
                # Only add description if it's short
                desc = hotel.get('hoteldescription', '')
                if desc and len(desc) < 100:  # Only include short descriptions
                    message += f"ℹ️ {desc[:100]}...\n"
                
                message += "\n" + "─" * 30 + "\n\n"
            
            print("✅ Results formatted successfully")
            return message
            
        except Exception as e:
            logger.error(f"Error in _search_tours: {e}", exc_info=True)
            print(f"❌ Error during tour search: {e}")
            return "😔 Произошла ошибка при поиске туров. Попробуйте позже."

    async def run(self):
        """Main loop to check and respond to Instagram messages"""
        print("🚀 Starting Instagram bot...")
        logger.info("Bot started")
        
        while True:
            try:
                print("\n👀 Checking for new messages...")
                # Get unread threads
                threads = self.client.direct_threads(selected_filter="unread")
                
                if not threads:
                    print("📭 No new messages")
                else:
                    print(f"📬 Found {len(threads)} unread threads")
                
                for thread in threads:
                    print(f"\n💬 Processing thread {thread.id}")
                    # Get messages in thread
                    messages = self.client.direct_messages(thread.id, amount=1)
                    
                    if not messages:
                        print("No messages in thread")
                        continue
                        
                    message = messages[0]
                    
                    # Skip if we've already processed this message
                    if thread.id in self.memory and self.memory[thread.id].get('last_message') == message.id:
                        print(f"⏭️ Skipping already processed message {message.id}")
                        continue
                    
                    # Process message if it's text
                    if message.text:
                        print(f"📝 Processing text message: '{message.text}'")
                        await self._handle_message(thread.id, message.user_id, message.text)
                        
                    # Update last processed message
                    if thread.id in self.memory:
                        self.memory[thread.id]['last_message'] = message.id
                        print(f"✅ Updated last processed message for thread {thread.id}")
                
                # Sleep to avoid hitting rate limits
                print("😴 Sleeping for 10 seconds...")
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                print(f"❌ Error in main loop: {e}")
                print("⏳ Waiting 30 seconds before retrying...")
                await asyncio.sleep(30)  # Wait longer if there's an error

async def main():
    print("🔄 Initializing Instagram Tour Bot...")
    bot = InstagramTourBot()
    await bot.run()

if __name__ == "__main__":
    print("🚀 Starting application...")
    asyncio.run(main()) 
