# Tour Search Chatbot

A modern chatbot interface for searching tours using the TourVisor API. The application provides an intuitive way to search for tours by guiding users through a series of questions about their travel preferences.

## Features

- 🤖 Interactive chatbot interface
- 🌍 Tour search with multiple parameters
- 🏨 Beautiful hotel cards with details
- 📅 Automatic date handling
- 💬 User-friendly conversation flow
- 🎯 Real-time search results
- 🔄 Easy reset functionality

## Prerequisites

- Python 3.7+
- FastAPI
- TourVisor API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hussainn7/TravellingService.git
cd TravellingService
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Then edit `.env` with your TourVisor API credentials.

## Usage

1. Start the server:
```bash
python main.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:3000
```

3. Start chatting with the bot to search for tours!

## Chatbot Flow

The chatbot will guide you through the following steps:
1. Choose departure city
2. Select destination country
3. Pick trip duration
4. Specify number of adults
5. Specify number of children
6. Confirm and search

## API Integration

The application integrates with the TourVisor API to provide:
- Real-time tour searches
- Hotel information
- Pricing details
- Availability checks

## Environment Variables

Create a `.env` file with the following variables:
```
TOURVISOR_LOGIN=your_login_here
TOURVISOR_PASS=your_password_here
```

## Project Structure

```
├── main.py           # FastAPI application and API integration
├── chatbot.py        # Chatbot logic and conversation handling
├── requirements.txt  # Python dependencies
├── templates/        # HTML templates
│   └── index.html   # Main interface template
├── .env             # Environment variables (not in repo)
└── .env.example     # Example environment variables
```

## Security

- Environment variables are used for sensitive data
- CORS protection enabled
- Input validation
- Error handling
- Secure credential management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- TourVisor API for tour data
- FastAPI for the web framework
- Bootstrap for UI components 