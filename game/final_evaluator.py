from yandex_ai.prompt_builder import build_final_evaluation_prompt
from yandex_ai.yandex_gpt_client import yandex_gpt_client
from game.case_models import Solution
from database.db import AsyncSessionLocal
from database.models import Investigation
from core.states import UserState
from vk_bot.vk_sender import vk_sender

class FinalEvaluator:
    async def evaluate_version(self, user_id: int, investigation_id: int, solution: Solution, user_version: str):
        system_prompt = build_final_evaluation_prompt(solution, user_version)
        response = await yandex_gpt_client.generate_response(system_prompt, user_version)
        
        async with AsyncSessionLocal() as session:
            inv = await session.get(Investigation, investigation_id)
            if inv:
                inv.is_finished = True
                inv.state = UserState.CASE_RESULT.value
                await session.commit()

        final_message = f"Оценка руководства:\n\n{response}\n\nДело закрыто. Возвращаю вас в главное меню."
        from vk_bot.vk_keyboards import get_main_menu
        await vk_sender.send_message(user_id, final_message, keyboard=get_main_menu())

final_evaluator = FinalEvaluator()
