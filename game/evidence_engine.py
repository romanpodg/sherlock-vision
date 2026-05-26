from yandex_ai.prompt_builder import build_evidence_prompt
from yandex_ai.yandex_gpt_client import yandex_gpt_client
from game.case_models import Evidence
from vk_bot.vk_sender import vk_sender

class EvidenceEngine:
    async def handle_analysis(self, user_id: int, evidence: Evidence, question: str):
        # 1. Формируем системный промпт
        system_prompt = build_evidence_prompt(evidence, question)
        
        # 2. Отправляем запрос
        response = await yandex_gpt_client.generate_response(system_prompt, question)
        
        # 3. Возвращаем ответ
        await vk_sender.send_message(user_id, f"Анализ ({evidence.title}):\n{response}")

evidence_engine = EvidenceEngine()
