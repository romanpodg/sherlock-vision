from yandex_ai.prompt_builder import build_yandex_art_portrait_prompt
from yandex_ai.yandex_art_client import yandex_art_client
from game.case_models import Suspect
from database.db import AsyncSessionLocal
from database.models import GeneratedImage
from vk_bot.vk_sender import vk_sender

class PortraitEngine:
    async def request_portrait(self, user_id: int, investigation_id: int, suspect: Suspect):
        prompt = build_yandex_art_portrait_prompt(suspect)
        
        # 1. Запрос в YandexART
        operation_id = await yandex_art_client.request_generation(prompt)
        
        if not operation_id:
            await vk_sender.send_message(user_id, "Ошибка при обращении к художнику (ИИ). Попробуйте позже.")
            return

        # 2. Сохраняем задачу в базу
        async with AsyncSessionLocal() as session:
            img = GeneratedImage(
                investigation_id=investigation_id,
                image_type="portrait",
                prompt=prompt,
                operation_id=operation_id,
                status="pending"
            )
            session.add(img)
            await session.commit()
            
        # 3. Сообщаем пользователю
        await vk_sender.send_message(user_id, "Ожидайте, фоторобот формируется. Это может занять около 20-30 секунд. Как только он будет готов, я пришлю его вам.")

portrait_engine = PortraitEngine()
