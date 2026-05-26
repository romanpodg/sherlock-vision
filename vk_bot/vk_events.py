import aiohttp
import asyncio
from vk_bot.vk_client import vk_client
from app.logger import logger

class VkLongPoll:
    def __init__(self):
        self.server = None
        self.key = None
        self.ts = None

    async def update_long_poll_server(self):
        logger.info("Updating Long Poll Server...")
        data = await vk_client.get_long_poll_server()
        self.server = data["server"]
        self.key = data["key"]
        self.ts = data["ts"]

    async def listen(self):
        await self.update_long_poll_server()
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25"
                try:
                    async with session.get(url) as response:
                        data = await response.json()
                        
                        if "failed" in data:
                            if data["failed"] == 1:
                                self.ts = data["ts"]
                            else:
                                await self.update_long_poll_server()
                            continue

                        self.ts = data["ts"]
                        for update in data.get("updates", []):
                            await self.process_update(update)

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    logger.error(f"Long Poll Error: {e}")
                    await asyncio.sleep(2)

    async def process_update(self, update: dict):
        if update["type"] == "message_new":
            message = update["object"]["message"]
            user_id = message["from_id"]
            text = message["text"]
            payload = message.get("payload")
            
            logger.info(f"New message from {user_id}: {text} (Payload: {payload})")
            
            # Use local import to avoid circular dependency early
            from core.router import route_message
            await route_message(user_id, text, payload)
