import asyncio
import base64
import os
import time
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.logger import logger
from database.db import AsyncSessionLocal
from database.models import GeneratedImage, Investigation, User
from yandex_ai.yandex_art_client import yandex_art_client
from vk_bot.vk_uploader import vk_uploader
from vk_bot.vk_sender import vk_sender

class ImageGenerationWorker:
    def __init__(self, interval_seconds: int = 5):
        self.interval_seconds = interval_seconds
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("Image Generation Worker started.")
        while self.is_running:
            try:
                await self._process_pending_images()
            except Exception as e:
                logger.error(f"Worker error: {e}")
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self.is_running = False

    async def _process_pending_images(self):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GeneratedImage).where(GeneratedImage.status == "pending")
            )
            pending_images = result.scalars().all()

            for image in pending_images:
                if not image.operation_id:
                    image.status = "failed"
                    continue

                status_data = await yandex_art_client.get_operation_status(image.operation_id)
                if status_data["done"]:
                    if status_data["image_base64"]:
                        os.makedirs("media/generated", exist_ok=True)
                        file_path = f"media/generated/img_{image.id}_{int(time.time())}.jpeg"
                        with open(file_path, "wb") as f:
                            f.write(base64.b64decode(status_data["image_base64"]))
                        
                        image.local_path = file_path
                        
                        inv_result = await session.execute(
                            select(Investigation).options(selectinload(Investigation.user)).where(Investigation.id == image.investigation_id)
                        )
                        inv = inv_result.scalars().first()
                        
                        if inv and inv.user:
                            vk_user_id = inv.user.vk_user_id
                            attachment = await vk_uploader.upload_photo_messages(vk_user_id, file_path)
                            
                            if attachment:
                                image.vk_attachment_id = attachment
                                image.status = "completed"
                                await vk_sender.send_message(
                                    vk_user_id, 
                                    "Фоторобот готов! (Изображение является художественной реконструкцией).", 
                                    attachment=attachment
                                )
                            else:
                                image.status = "failed"
                        else:
                            image.status = "failed"
                    else:
                        image.status = "failed"
            
            if pending_images:
                await session.commit()

image_generation_worker = ImageGenerationWorker()
