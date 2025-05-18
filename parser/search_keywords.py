import json
from mistralai import Mistral
from abc import ABC, abstractmethod

class Search(ABC):
    @abstractmethod
    async def search_key_words(self, title: str, description: str) -> list:
        pass


class MistralClient:
    def __init__(self, api_key: str, model: str = "open-mistral-nemo"):
        self.__client = Mistral(api_key=api_key)
        self.__model = model

    @property
    def client(self):
        return self.__client
    
    @property
    def model(self):
        return self.__model

class SearchByMistral(Search):
    def __init__(self, mistral_client: MistralClient, quantity_keywords: int = 10):
        self.__mistral_client = mistral_client
        self.__quantity_keywords = quantity_keywords

    async def search_key_words(self, title, description) -> list:
        model = self.__mistral_client.model

        client = self.__mistral_client.client

        prompt = f"""
        Товар: {title}
        Описание: {description}

        Задача: Выдели {self.__quantity_keywords} ключевых слов/фраз (на русском), которые лучше всего использовать для поиска этого товара. 
        Учитывай: 
        - Характеристики товара (материал, фасон, размер) 
        - Бренд и модель 
        - Целевую аудиторию 
        - Стиль и назначение
        - Популярные поисковые запросы

        Формат: JSON-список, только слова/фразы.
        Пример: ["футболка утягивающая", "скимс", "летний топ", "облегающая"]

        Ключевые слова:
        """

        chat_response = await client.chat.complete_async(
            model = model,
            messages = [
                {
                    "role": "user",
                    "content": f"{prompt}",
                },
            ]
        )

        print(chat_response.choices[0].message.content)
        return json.loads(chat_response.choices[0].message.content) 