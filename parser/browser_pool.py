from playwright.async_api import async_playwright
import asyncio
from contextlib import asynccontextmanager
from playwright.async_api import Browser

class BrowserPool:
    def __init__(self, max_browsers=5):
        self.max_browsers = max_browsers
        self.semaphore = asyncio.Semaphore(max_browsers)
        self.browsers = []


    @asynccontextmanager
    async def get_browser(self):
        await self.semaphore.acquire()
        browser = None
        try:
            async with async_playwright() as p:
                browser = await self.__setup_browser(p)
                self.browsers.append(browser)
                yield browser
        finally:
            if browser:
                await browser.close()
                self.browsers.remove(browser)
            self.semaphore.release()

    async def close_all(self):
        for browser in self.browsers:
            await browser.close()
        self.browsers = []

    async def __setup_browser(self, p) -> Browser:
        browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--window-size=1920,1080'
                ]
            )
            
        # Создаем контекст с пользовательским User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        return context