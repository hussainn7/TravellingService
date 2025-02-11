# Tourvisor Search Bot

Чат-бот для поиска туров с использованием API Tourvisor.

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и добавьте свои учетные данные Tourvisor:
```
TOURVISOR_LOGIN=your_login
TOURVISOR_PASS=your_password
```

## Запуск

1. Запустите сервер:
```bash
python main.py
```

2. Откройте браузер и перейдите по адресу: `http://localhost:8000`

## Функциональность

- Поиск туров по различным параметрам
- Асинхронная загрузка результатов
- Отображение прогресса поиска
- Фильтрация по:
  - Городу вылета
  - Стране
  - Датам
  - Количеству ночей
  - Количеству туристов
- Отображение информации об отелях и турах
- Сортировка по цене и рейтингу

## Технологии

- FastAPI
- Python 3.7+
- HTML/CSS/JavaScript
- Bootstrap 5
- Tourvisor API 