import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from parser.parser_async import ParserAsync
from parser.search_keywords import MistralClient, SearchByMistral
from parser.browser_pool import BrowserPool
from dotenv import load_dotenv
import os

load_dotenv()
# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL") or "open-mistral-7b"
MAX_BROWSERS = os.getenv("MAX_BROWSERS") or 5
QUANTITY_KEYWORDS = os.getenv("QUANTITY_KEYWORDS") or 10
MAX_POSITIONS = os.getenv("MAX_POSITIONS") or 1000

try:
    MAX_BROWSERS = int(MAX_BROWSERS)
    QUANTITY_KEYWORDS = int(QUANTITY_KEYWORDS)
    MAX_POSITIONS = int(MAX_POSITIONS)
except ValueError:
    print("Ошибка: Неверный формат значения переменных окружения")
    exit(1)

if not BOT_TOKEN:
    print("Ошибка: Не указан токен бота")
    exit(1)
if not MISTRAL_API_KEY:
    print("Ошибка: Не указан ключ API Mistral")
    exit(1)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
browser_pool = BrowserPool(max_browsers=MAX_BROWSERS)
parser = ParserAsync(browser_pool)
client = MistralClient(MISTRAL_API_KEY, MISTRAL_MODEL)
search = SearchByMistral(client, QUANTITY_KEYWORDS)

async def update_message(chat_id, message_id, text):
    """Обновляет сообщение с безопасным HTML-форматированием"""
    try:
        # Экранируем специальные символы и проверяем HTML-теги
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Восстанавливаем наши корректные HTML-теги
        safe_text = safe_text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        safe_text = safe_text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
        safe_text = safe_text.replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=safe_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка при обновлении сообщения: {e}")

async def create_progress_message(chat_id):
    """Создает начальное сообщение с прогрессом"""
    return await bot.send_message(
        chat_id=chat_id,
        text="<b>🔍 Начинаю анализ товара...</b>",
        parse_mode="HTML"
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Отправь мне ссылку на товар с Wildberries, "
        "и я проверю его позиции по ключевым словам.\n\n"
        "Пример ссылки:\n"
        "https://www.wildberries.ru/catalog/12345678/detail.aspx"
    )

@dp.message()
async def handle_product_url(message: Message):
    url = message.text.strip()
    
    if not url.startswith("https://www.wildberries.ru/catalog/") or "/detail.aspx" not in url:
        await message.answer("Пожалуйста, отправьте корректную ссылку на товар Wildberries.")
        return
    
    # Создаем основное сообщение, которое будем обновлять
    main_msg = await create_progress_message(message.chat.id)
    
    try:
        # 1. Парсинг товара
        await update_message(
            main_msg.chat.id, main_msg.message_id,
            "🔄 <b>Получаю информацию о товаре...</b>"
        )
        
        product_info = await parser.parse_product(url)
        if not product_info:
            await update_message(
                main_msg.chat.id, main_msg.message_id,
                "❌ <b>Не удалось получить информацию о товаре. Проверьте ссылку.</b>"
            )
            return
        
        # 2. Извлечение ключевых слов
        await update_message(
            main_msg.chat.id, main_msg.message_id,
            f"🔍 <b>Анализирую товар:</b>\n"
            f"<b>Название:</b> {product_info['title']}\n"
            f"<b>Артикул:</b> {product_info['article']}\n\n"
            f"🔑 <b>Извлекаю ключевые слова...</b>"
        )
        
        keywords = await search.search_key_words(product_info['title'], product_info['description'])
        
        # 3. Подготовка структуры для результатов
        results = []
        base_text = (
            f"📊 <b>Результаты для товара:</b>\n"
            f"<b>{product_info['title']}</b>\n"
            f"Артикул: {product_info['article']}\n\n"
            f"🔍 <b>Позиции в поиске:</b>\n"
        )
        
        # 4. Проверка позиций с постепенным обновлением
        await update_message(
            main_msg.chat.id, main_msg.message_id,
            base_text + "\n<i>Идет проверка позиций...</i>"
        )
        
        tasks = [parser.check_position(keyword, product_info['article'], MAX_POSITIONS//100) 
                for keyword in keywords]
        
        found_positions = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            result = await task
            found_positions.append(result)
            
            # Сортируем результаты по позиции
            sorted_results = sorted(
                found_positions,
                key=lambda x: x['position'] if x['position'] else 9999
            )
            
            # Формируем текст с текущими результатами
            results_text = "\n".join(
                f"{'✅' if r['position'] else '❌'} {r['position'] or '--'}: {r['keyword']}"
                for r in sorted_results
            )
            
            # Обновляем сообщение каждые 2 результата или если это последний
            if i % 2 == 0 or i == len(tasks):
                progress = f"\n\n⏳ Проверено {i} из {len(tasks)} ключевых слов"
                await update_message(
                    main_msg.chat.id, main_msg.message_id,
                    base_text + results_text + progress
                )
        
        # 5. Финальное сообщение с сортировкой
        final_sorted = sorted(
            found_positions,
            key=lambda x: x['position'] if x['position'] else 9999
        )
        
        results_text = "\n".join(
            f"{'🔹' if r['position'] else '🔸'} {r['position'] or 'не найден'}: <code>{r['keyword']}</code>"
            for r in final_sorted
        )
        
        await update_message(
            main_msg.chat.id, main_msg.message_id,
            base_text + results_text + 
            f"\n\n✅ <b>Проверка завершена!</b>\n"
            f"Всего проверено: {len(keywords)} запросов\n"
            f"Максимальная глубина: {MAX_POSITIONS} позиций"
        )
        
    except Exception as e:
        await update_message(
            main_msg.chat.id, main_msg.message_id,
            f"⚠️ <b>Произошла ошибка:</b>\n{str(e)}"
        )
    finally:
        await browser_pool.close_all()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())