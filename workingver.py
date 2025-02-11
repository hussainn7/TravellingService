from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import asyncio
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

# Настройка более детального логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

TOURVISOR_LOGIN = os.getenv("TOURVISOR_LOGIN")
TOURVISOR_PASS = os.getenv("TOURVISOR_PASS")
TOURVISOR_BASE_URL = "http://tourvisor.ru/xml"

# Add CORS middleware to allow all origins
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TourSearch:
    def __init__(self):
        self.base_url = TOURVISOR_BASE_URL
        self.auth = {
            'authlogin': TOURVISOR_LOGIN,
            'authpass': TOURVISOR_PASS
        }
        logger.info(f"Initialized TourSearch with login: {TOURVISOR_LOGIN}")

        # Test API connection on initialization
        self.test_connection()

    def test_connection(self):
        """Test API connection with credentials"""
        now = datetime.now()
        date_from = f"{now.day:02d}.{now.month:02d}.{now.year}"
        date_to = (now + timedelta(days=7))
        date_to = f"{date_to.day:02d}.{date_to.month:02d}.{date_to.year}"
        
        url = (
            f"{self.base_url}/search.php"
            f"?authlogin={self.auth['authlogin']}"
            f"&authpass={self.auth['authpass']}"
            f"&departure=1"  # Moscow
            f"&country=1"    # Egypt
            f"&datefrom={date_from}"
            f"&dateto={date_to}"
            f"&nightsfrom=7"
            f"&nightsto=14"
            f"&adults=2"
            f"&child=0"
        )
        
        try:
            logger.info(f"Testing connection with URL: {url}")
            response = requests.get(url, verify=False)
            logger.info(f"Test connection response: {response.text}")
            if response.status_code != 200:
                logger.error(f"API test failed with status code: {response.status_code}")
            if 'error' in response.text.lower():
                logger.error(f"API test failed with error: {response.text}")
        except Exception as e:
            logger.error(f"API test connection failed: {e}")

    def _parse_xml_to_dict(self, element):
        """Рекурсивно преобразует XML элемент в словарь"""
        result = {}
        for child in element:
            if len(child) > 0:
                if child.tag == 'tours':
                    result[child.tag] = [self._parse_xml_to_dict(tour) for tour in child]
                else:
                    result[child.tag] = self._parse_xml_to_dict(child)
            else:
                result[child.tag] = child.text
        return result

    def create_search_request(self, params):
        """Создает поисковый запрос в системе Tourvisor"""
        try:
            # Convert and validate dates
            try:
                # Parse input dates
                date_from = datetime.strptime(params['datefrom'], '%Y-%m-%d')
                date_to = datetime.strptime(params['dateto'], '%Y-%m-%d')
                
                # Format dates in simple format (dd.mm.yyyy without URL encoding)
                date_from_str = f"{date_from.day:02d}.{date_from.month:02d}.{date_from.year}"
                date_to_str = f"{date_to.day:02d}.{date_to.month:02d}.{date_to.year}"
                
                logger.info(f"Converted dates: from {date_from_str} to {date_to_str}")
            except ValueError as e:
                logger.error(f"Date parsing error: {e}")
                return {"error": "Неверный формат даты"}
            
            # Construct URL directly without using urlencode
            url = (
                f"{self.base_url}/search.php"
                f"?authlogin={self.auth['authlogin']}"
                f"&authpass={self.auth['authpass']}"
                f"&departure={params['departure']}"
                f"&country={params['country']}"
                f"&datefrom={date_from_str}"
                f"&dateto={date_to_str}"
                f"&nightsfrom={params['nightsfrom']}"
                f"&nightsto={params['nightsto']}"
                f"&adults={params['adults']}"
                f"&child={params['child']}"
            )
            
            logger.info(f"Sending request to URL: {url}")
            
            # Make request
            response = requests.get(url, verify=False, timeout=30)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Raw response text: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"API returned non-200 status code: {response.status_code}")
                return None
            
            # Check if response is empty
            if not response.text.strip():
                logger.error("Empty response received from API")
                return None
            
            # Parse XML response
            try:
                root = ET.fromstring(response.text)
                
                # Check for error first
                error_elem = root.find('.//errormessage')
                if error_elem is not None:
                    error_text = error_elem.text
                    logger.error(f"API returned error: {error_text}")
                    return {"error": error_text}
                
                request_id_elem = root.find('.//requestid')
                if request_id_elem is not None:
                    request_id = request_id_elem.text
                    logger.info(f"Successfully parsed request ID from XML: {request_id}")
                    return {'requestid': request_id}
                else:
                    logger.error("No requestid element found in XML response")
                    return None
                    
            except ET.ParseError as e:
                logger.error(f"Failed to parse XML: {e}")
                logger.error(f"XML content: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            logger.error(f"Response content: {response.text if 'response' in locals() else 'No response'}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_search_results(self, request_id, result_type='result'):
        """Получает результаты поиска"""
        url = f"{self.base_url}/result.php"
        
        # Format parameters exactly as in example
        params = {
            'authlogin': self.auth['authlogin'],
            'authpass': self.auth['authpass'],
            'requestid': request_id,
            'type': result_type,
            'page': '1',
            'onpage': '25'
        }
        
        try:
            # Create URL exactly as in example
            full_url = f"{url}?{urlencode(params)}"
            logger.info(f"Getting search results from URL: {full_url}")
            
            response = requests.get(full_url, verify=False)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Raw response text: {response.text}")
            
            response.raise_for_status()
            
            # Parse XML response
            try:
                root = ET.fromstring(response.text)
                if root.tag != 'data':
                    logger.error(f"Unexpected root tag: {root.tag}")
                    return None

                result = {}
                
                # Parse status block
                status_elem = root.find('status')
                if status_elem is not None:
                    result['status'] = self._parse_xml_to_dict(status_elem)
                
                # Parse result block if present
                result_elem = root.find('result')
                if result_elem is not None:
                    hotels = []
                    for hotel_elem in result_elem.findall('hotel'):
                        hotel_data = self._parse_xml_to_dict(hotel_elem)
                        hotels.append(hotel_data)
                    result['result'] = {'hotels': hotels}
                
                return result
                
            except ET.ParseError as e:
                logger.error(f"Failed to parse XML: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting results: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def make_test_request(self, test_params=None):
        """Make a test request to the API with provided or default parameters"""
        if test_params is None:
            now = datetime.now()
            date_from = f"{now.day:02d}.{now.month:02d}.{now.year}"
            date_to = (now + timedelta(days=7))
            date_to = f"{date_to.day:02d}.{date_to.month:02d}.{date_to.year}"
            
            url = (
                f"{self.base_url}/search.php"
                f"?authlogin={self.auth['authlogin']}"
                f"&authpass={self.auth['authpass']}"
                f"&departure=1"  # Moscow
                f"&country=1"    # Egypt
                f"&datefrom={date_from}"
                f"&dateto={date_to}"
                f"&nightsfrom=7"
                f"&nightsto=14"
                f"&adults=2"
                f"&child=0"
            )
        else:
            url = f"{self.base_url}/search.php?{urlencode(test_params)}"
        
        logger.debug(f"Making test request to URL: {url}")
        
        try:
            response = requests.get(url, verify=False, timeout=30)
            
            result = {
                'url': url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text,
                'encoding': response.encoding
            }
            
            # Try to parse XML
            try:
                root = ET.fromstring(response.text)
                result['xml_valid'] = True
                result['xml_root_tag'] = root.tag
                if root.find('.//error') is not None:
                    result['xml_error'] = root.find('.//error').text
                if root.find('.//requestid') is not None:
                    result['xml_requestid'] = root.find('.//requestid').text
            except ET.ParseError as e:
                result['xml_valid'] = False
                result['xml_error'] = str(e)
            
            return result
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__
            }

tour_search = TourSearch()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/search")
async def search_tours(
    request: Request,
    departure: str = Form(...),
    country: str = Form(...),
    date_from: str = Form(...),
    date_to: str = Form(...),
    nights_from: int = Form(...),
    nights_to: int = Form(...),
    adults: int = Form(2),
    children: int = Form(0)
):
    # Log the incoming request data
    logger.info(f"""
    Received search request:
    - Departure: {departure}
    - Country: {country}
    - Date From: {date_from}
    - Date To: {date_to}
    - Nights From: {nights_from}
    - Nights To: {nights_to}
    - Adults: {adults}
    - Children: {children}
    """)

    search_params = {
        'departure': departure,
        'country': country,
        'datefrom': date_from,
        'dateto': date_to,
        'nightsfrom': nights_from,
        'nightsto': nights_to,
        'adults': adults,
        'child': children
    }

    logger.info(f"Starting search with params: {search_params}")
    
    # Создаем поисковый запрос
    search_response = tour_search.create_search_request(search_params)
    if not search_response:
        logger.error("Failed to create search request")
        return {"error": "Ошибка при создании поискового запроса"}
    
    if "error" in search_response:
        return {"error": f"API вернула ошибку: {search_response['error']}"}

    request_id = search_response.get('requestid')
    if not request_id:
        logger.error(f"No request ID in response: {search_response}")
        return {"error": "Не удалось получить ID запроса"}

    logger.info(f"Got request ID: {request_id}")

    # Ждем несколько секунд и получаем первые результаты
    await asyncio.sleep(5)
    
    results = tour_search.get_search_results(request_id)
    if not results:
        logger.error("Failed to get search results")
        return {"error": "Не удалось получить результаты поиска"}

    return results

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    """Получение статуса поиска"""
    results = tour_search.get_search_results(request_id, 'status')
    return results

@app.get("/test", response_class=JSONResponse)
async def test_api():
    """Test endpoint to check API connectivity"""
    logger.info("Starting API test")
    
    # Test with default parameters
    default_test = tour_search.make_test_request()
    
    # Test with minimal parameters
    minimal_params = {
        'authlogin': TOURVISOR_LOGIN,
        'authpass': TOURVISOR_PASS,
        'departure': '1',
        'country': '1',
        'datefrom': datetime.now().strftime('%d%m%Y'),
        'dateto': (datetime.now() + timedelta(days=7)).strftime('%d%m%Y'),
        'nightsfrom': '7',
        'nightsto': '14'
    }
    minimal_test = tour_search.make_test_request(minimal_params)
    
    return {
        'credentials': {
            'login': TOURVISOR_LOGIN,
            'pass': '*' * len(TOURVISOR_PASS) if TOURVISOR_PASS else None
        },
        'default_test': default_test,
        'minimal_test': minimal_test
    }

@app.get("/test/{country_id}", response_class=JSONResponse)
async def test_country(country_id: str):
    """Test endpoint to check specific country search"""
    logger.info(f"Testing search for country_id: {country_id}")
    
    test_params = {
        'authlogin': TOURVISOR_LOGIN,
        'authpass': TOURVISOR_PASS,
        'departure': '1',  # Moscow
        'country': country_id,
        'datefrom': datetime.now().strftime('%d%m%Y'),
        'dateto': (datetime.now() + timedelta(days=7)).strftime('%d%m%Y'),
        'nightsfrom': '7',
        'nightsto': '14'
    }
    
    return tour_search.make_test_request(test_params)

if __name__ == "__main__":
    import uvicorn
    # Disable SSL verification warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Log environment info
    logger.info(f"Environment variables:")
    logger.info(f"TOURVISOR_LOGIN: {TOURVISOR_LOGIN}")
    logger.info(f"TOURVISOR_PASS: {'*' * len(TOURVISOR_PASS) if TOURVISOR_PASS else 'Not set'}")
    logger.info(f"TOURVISOR_BASE_URL: {TOURVISOR_BASE_URL}")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3000,
        log_level="debug"
    ) 