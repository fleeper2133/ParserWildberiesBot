
# ParserWildberiesBot

ParserWildberiesBot — это Telegram-бот, который анализирует позиции товаров на Wildberries по ключевым словам.

## Описание

Этот бот позволяет пользователям отправлять ссылки на товары с Wildberries и получать информацию о позициях этих товаров в поиске по различным ключевым словам. Бот использует Playwright для парсинга страниц и Mistral API для извлечения ключевых слов.

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/fleeper2133/ParserWildberiesBot.git
   cd ParserWildberiesBot
   ```

2. Создайте файл `.env` в корневой директории проекта и добавьте в него следующие переменные окружения:

   ```plaintext
   MISTRAL_API_KEY=ваш_ключ_API_Mistral
   BOT_TOKEN=ваш_токен_Telegram_бота
   MISTRAL_MODEL=open-mistral-nemo
   MAX_BROWSERS=5
   QUANTITY_KEYWORDS=10
   MAX_POSITIONS=1000
   ```

3. Запустите бота:

   ```bash
   docker-compose up --build
   ```

## Использование

1. Откройте Telegram и найдите вашего бота по имени.
2. Отправьте боту ссылку на товар с Wildberries.
3. Бот начнет анализ и отправит вам результаты позиций товара по ключевым словам.

## Пример ссылки

Пример корректной ссылки на товар:

```
https://www.wildberries.ru/catalog/12345678/detail.aspx
```

## Зависимости

- Python 3.8+
- aiogram
- playwright
- python-dotenv
- requests

## Конфигурация

Вы можете настроить следующие параметры в файле `.env`:

- `MISTRAL_API_KEY`: Ключ API для Mistral.
- `BOT_TOKEN`: Токен вашего Telegram-бота.
- `MISTRAL_MODEL`: Модель Mistral для извлечения ключевых слов.
- `MAX_BROWSERS`: Максимальное количество браузеров для парсинга.
- `QUANTITY_KEYWORDS`: Количество ключевых слов для анализа.
- `MAX_POSITIONS`: Максимальное количество позиций для проверки.
