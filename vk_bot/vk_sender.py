import random
from vk_bot.vk_client import vk_client
from app.logger import logger

class VkSender:
    async def send_message(self, user_id: int, text: str, keyboard: str = None, attachment: str = None):
        random_id = random.randint(1, 2**31)
        try:
            await vk_client.send_message(
                user_id=user_id,
                message=text,
                keyboard=keyboard,
                attachment=attachment,
                random_id=random_id
            )
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")

vk_sender = VkSender()
