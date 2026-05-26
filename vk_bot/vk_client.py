import aiohttp
from app.config import settings
from app.logger import logger

class VkClient:
    def __init__(self):
        self.token = settings.vk_token
        self.group_id = settings.vk_group_id
        self.api_version = "5.199"
        self.base_url = "https://api.vk.com/method/"
        self.session = None

    async def init_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def _request(self, method: str, params: dict) -> dict:
        await self.init_session()
        params["access_token"] = self.token
        params["v"] = self.api_version
        url = f"{self.base_url}{method}"
        
        async with self.session.post(url, data=params) as response:
            data = await response.json()
            if "error" in data:
                logger.error(f"VK API Error ({method}): {data['error']}")
                raise Exception(data["error"]["error_msg"])
            return data.get("response", data)

    async def get_long_poll_server(self) -> dict:
        return await self._request("groups.getLongPollServer", {"group_id": self.group_id})

    async def send_message(self, user_id: int, message: str, keyboard: str = None, attachment: str = None, random_id: int = 0) -> int:
        params = {
            "user_id": user_id,
            "message": message,
            "random_id": random_id,
        }
        if keyboard:
            params["keyboard"] = keyboard
        if attachment:
            params["attachment"] = attachment
            
        return await self._request("messages.send", params)

vk_client = VkClient()
