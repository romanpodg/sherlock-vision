import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.logger import logger
from database.db import init_db
from vk_bot.vk_events import VkLongPoll
from vk_bot.vk_client import vk_client
from workers.image_generation_worker import image_generation_worker

async def main():
    logger.info("Starting Sherlock Vision bot...")
    
    # Initialize DB
    await init_db()
    
    # Start background worker for YandexART
    worker_task = asyncio.create_task(image_generation_worker.start())
    
    # Start Long Poll
    lp = VkLongPoll()
    try:
        await lp.listen()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        image_generation_worker.stop()
        await worker_task
        await vk_client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
