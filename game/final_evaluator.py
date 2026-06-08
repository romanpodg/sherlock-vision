import json
import re
from app.logger import logger
from yandex_ai.prompt_builder import build_final_evaluation_prompt
from yandex_ai.yandex_gpt_client import yandex_gpt_client
from game.case_models import Solution, CaseData
from database.db import AsyncSessionLocal
from database.models import Investigation
from core.states import UserState
from vk_bot.vk_sender import vk_sender

class FinalEvaluator:
    def _extract_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json|JSON)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
        
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    async def evaluate_version(self, user_id: int, investigation_id: int, case: CaseData, user_version: str):
        system_prompt, user_message = build_final_evaluation_prompt(case, user_version)
        response = await yandex_gpt_client.generate_response(system_prompt, user_message, temperature=0.2)
        
        total_score = 0
        formatted_response = response
        
        try:
            cleaned_response = self._extract_json(response)
            data = json.loads(cleaned_response)
            total_score = data.get("total_score", 0)
            
            correct = "\n".join([f"- {p}" for p in data.get("correct_points", [])]) or "- Нет данных"
            mistakes = "\n".join([f"- {p}" for p in data.get("mistakes", [])]) or "- Нет ошибок"
            missed = "\n".join([f"- {p}" for p in data.get("missed_points", [])]) or "- Ничего не упущено"
            comment = data.get("final_comment", "Оценка завершена.")
            
            formatted_response = (
                f"🏆 Общий результат: {total_score} из 100\n\n"
                f"✅ Что определено верно:\n{correct}\n\n"
                f"❌ Ошибки:\n{mistakes}\n\n"
                f"💡 Что было упущено:\n{missed}\n\n"
                f"💬 Вердикт старшего инспектора:\n«{comment}»"
            )
        except Exception as e:
            logger.error(f"Failed to parse evaluation JSON: {e}\n{response}")
            formatted_response = response
            
        async with AsyncSessionLocal() as session:
            inv = await session.get(Investigation, investigation_id)
            if inv:
                inv.is_finished = True
                inv.score = total_score
                inv.state = UserState.CASE_RESULT.value
                await session.commit()

        final_message = f"👮‍♂️ Оценка руководства:\n\n{formatted_response}\n\nДело закрыто. Возвращаю вас в главное меню."
        from vk_bot.vk_keyboards import get_main_menu
        await vk_sender.send_message(user_id, final_message, keyboard=get_main_menu())

final_evaluator = FinalEvaluator()
