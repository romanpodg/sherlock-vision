import aiohttp
import asyncio
import base64
from app.config import settings
from app.logger import logger

class YandexARTClient:
    def __init__(self):
        self.api_key = settings.yandex_api_key
        self.folder_id = settings.yandex_folder_id
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
        self.operations_url = "https://llm.api.cloud.yandex.net/operations/"
        self.model_uri = f"art://{self.folder_id}/yandex-art/latest"

    async def _get_headers(self):
        return {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

    async def request_generation(self, prompt: str) -> str | None:
        """Starts async generation and returns operation ID. Raises TimeoutError on timeout."""
        data = {
            "modelUri": self.model_uri,
            "generationOptions": {
                "mimeType": "image/jpeg",
                "aspectRatio": {"widthRatio": 1, "heightRatio": 1}
            },
            "messages": [{"weight": "1", "text": prompt}]
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = await self._get_headers()
                timeout = aiohttp.ClientTimeout(total=15)
                async with session.post(self.base_url, headers=headers, json=data, timeout=timeout) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("id")
                    else:
                        logger.error(f"YandexART Request Error: {resp.status} - {await resp.text()}")
                        return None
            except asyncio.TimeoutError:
                logger.error("YandexART request timed out")
                raise TimeoutError("Сервисное сообщение: Сервер Яндекса сейчас перегружен, попробуйте отправить запрос через минуту")
            except Exception as e:
                logger.error(f"YandexART API call failed: {e}")
                return None

    async def get_operation_status(self, operation_id: str) -> dict:
        """Returns dict: {'done': bool, 'image_base64': str | None}"""
        url = f"{self.operations_url}{operation_id}"
        async with aiohttp.ClientSession() as session:
            try:
                headers = await self._get_headers()
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("done"):
                            response_data = data.get("response", {})
                            image_b64 = response_data.get("image")
                            return {"done": True, "image_base64": image_b64}
                        else:
                            return {"done": False, "image_base64": None}
                    else:
                        logger.error(f"YandexART Status Error: {resp.status} - {await resp.text()}")
                        return {"done": True, "image_base64": None} # treat error as done but failed
            except Exception as e:
                logger.error(f"YandexART Status check failed: {e}")
                return {"done": False, "image_base64": None}

yandex_art_client = YandexARTClient()
