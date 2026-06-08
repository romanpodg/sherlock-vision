import aiohttp
from app.config import settings
from app.logger import logger

class YandexGPTClient:
    def __init__(self):
        self.api_key = settings.yandex_api_key
        self.folder_id = settings.yandex_folder_id
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt-lite/latest"

    async def generate_response(self, system_prompt: str, user_message: str, history: list = None, temperature: float = 0.3) -> str:
        import asyncio
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system",
                "text": system_prompt
            }
        ]
        
        if history:
            messages.extend(history)
            
        messages.append({
            "role": "user",
            "text": user_message
        })
        
        data = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": 1000
            },
            "messages": messages
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                timeout = aiohttp.ClientTimeout(total=15)
                async with session.post(self.base_url, headers=headers, json=data, timeout=timeout) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result["result"]["alternatives"][0]["message"]["text"]
                    else:
                        error_text = await resp.text()
                        logger.error(f"YandexGPT API Error: {resp.status} - {error_text}")
                        return "Произошла ошибка при обращении к ИИ."
            except asyncio.TimeoutError:
                logger.error("YandexGPT request timed out")
                return "Сервисное сообщение: Сервер Яндекса сейчас перегружен, попробуйте отправить запрос через минуту"
            except Exception as e:
                logger.error(f"YandexGPT request failed: {e}")
                return "Ошибка сети при обращении к ИИ."

yandex_gpt_client = YandexGPTClient()
