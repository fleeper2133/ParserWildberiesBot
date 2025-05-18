from .browser_pool import BrowserPool
from urllib.parse import quote_plus

class ParserAsync:
    def __init__(self, browser_pool: BrowserPool):
        self.__browser_pool = browser_pool

    async def parse_product(self, url: str) -> dict:
    
        async with self.__browser_pool.get_browser() as browser:
        
            page = await browser.new_page()
            
            try:
                # Загружаем страницу с таймаутом
                await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                
            
                await page.wait_for_selector("h1.product-page__title", state="attached", timeout=15000)
            
                
            # Получаем данные
                article = await page.text_content("span#productNmId")
                title = await page.text_content("h1.product-page__title")
                
                # Пробуем открыть описание (с несколькими попытками)
                for _ in range(2):
                    try:
                        await page.click("button.product-page__btn-detail", timeout=5000)
                        await page.wait_for_timeout(1000)
                        break
                    except:
                        await page.wait_for_timeout(500)
                
                # Получаем описание (с альтернативными селекторами)
                description = await page.evaluate('''() => {
                    const selectors = [
                        'div.product-page__description',
                        'div.collapsable__content',
                        'p.option__text'
                    ];
                    
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) return el.textContent.trim();
                    }
                    return '';
                }''')
                
                return {
                    'article': article,
                    'title': title,
                    'description': description,
                    'url': url
                }
                
            except Exception as e:
                print(f"Ошибка парсинга: {e}")
                return None
            finally:
                # await context.close()
                await browser.close()

    async def check_position(self, keyword, article, max_pages=10):
        async with self.__browser_pool.get_browser() as browser:
            
            page = await browser.new_page()
            
            try:
                encoded_keyword = quote_plus(keyword)
                
                for page_num in range(1, max_pages + 1):
                    url = f"https://www.wildberries.ru/catalog/0/search.aspx?page={page_num}&sort=popular&search={encoded_keyword}"
                    await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_selector("article", state="attached", timeout=15000)
                    
                    # Плавная прокрутка
                    await self.__scroll_page(page)
                    
                    # Ищем товар
                    items = await page.query_selector_all("article[data-nm-id]")
                    for position, item in enumerate(items, 1):
                        item_id = await item.get_attribute("data-nm-id")
                        if item_id == article:
                            print(position)
                            return {
                                'keyword': keyword,
                                'page': page_num,
                                'position': position + (page_num-1)*100,
                                'url': url
                            }
                    
                    # Проверяем есть ли следующая страница
                    error_wrap = await page.query_selector("div.not-found-search__wrap")
                    if error_wrap:
                        break
                        
                return {
                    'keyword': keyword,
                    'page': None,
                    'position': None,
                    'url': None
                }
                
            except Exception as e:
                print(f"Ошибка при проверке позиции: {e}")
                return {
                    'keyword': keyword,
                    'page': None,
                    'position': None,
                    'url': None
                }
            finally:
                await browser.close()

    async def __scroll_page(self, page):
        """Плавная прокрутка страницы"""
        scroll_step = 1500
        current_pos = 0
        
        while True:
            # Получаем высоту страницы
            page_height = await page.evaluate("document.body.scrollHeight")
            
            # Прокручиваем
            await page.evaluate(f"window.scrollTo(0, {current_pos})")
            await page.wait_for_timeout(300)
            
            # Увеличиваем позицию
            current_pos += scroll_step
            
            # Проверяем достигли ли конца
            if current_pos >= page_height:
                break
                
            # Обновляем высоту (на случай динамической подгрузки)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > page_height:
                page_height = new_height