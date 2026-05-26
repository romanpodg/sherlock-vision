from yandex_ai.prompt_builder import build_witness_prompt
from yandex_ai.yandex_gpt_client import yandex_gpt_client
from game.case_models import Witness
from vk_bot.vk_sender import vk_sender

class WitnessEngine:
    async def handle_question(self, user_id: int, witness: Witness, question: str):
        # 1. Формируем системный промпт для YandexGPT
        system_prompt = build_witness_prompt(witness)
        
        # 2. Отправляем запрос
        response = await yandex_gpt_client.generate_response(system_prompt, question)
        
        # 3. Возвращаем ответ пользователю
        await vk_sender.send_message(user_id, f"{witness.name}:\n— {response}")

witness_engine = WitnessEngine()
