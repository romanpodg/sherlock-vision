from yandex_ai.prompt_builder import build_witness_prompt
from yandex_ai.yandex_gpt_client import yandex_gpt_client
from game.case_models import Witness
from vk_bot.vk_sender import vk_sender
from database.db import AsyncSessionLocal
from database.models import InvestigationWitness
from sqlalchemy.future import select

class WitnessEngine:
    async def handle_question(self, user_id: int, inv_id: int, witness: Witness, question: str):
        # 1. Формируем промпты для YandexGPT
        system_prompt, user_message = build_witness_prompt(witness, question)
        
        async with AsyncSessionLocal() as session:
            # Получаем или создаем запись свидетеля
            result = await session.execute(
                select(InvestigationWitness)
                .where(InvestigationWitness.investigation_id == inv_id)
                .where(InvestigationWitness.witness_id == witness.id)
            )
            inv_witness = result.scalars().first()
            
            if not inv_witness:
                inv_witness = InvestigationWitness(
                    investigation_id=inv_id,
                    witness_id=witness.id,
                    is_interviewed=True,
                    dialog_history=[]
                )
                session.add(inv_witness)
            else:
                inv_witness.is_interviewed = True
                
            # Берем последние 6 сообщений (3 пары вопрос-ответ)
            history = inv_witness.dialog_history[-6:] if inv_witness.dialog_history else []
            
            # 2. Отправляем запрос с историей
            response = await yandex_gpt_client.generate_response(system_prompt, user_message, history, temperature=0.2)
            
            # Обновляем историю
            new_history = inv_witness.dialog_history.copy() if inv_witness.dialog_history else []
            new_history.append({"role": "user", "text": question})
            new_history.append({"role": "assistant", "text": response})
            
            inv_witness.dialog_history = new_history
            await session.commit()
        
        # 3. Возвращаем ответ пользователю
        await vk_sender.send_message(user_id, f"{witness.name}:\n— {response}")

witness_engine = WitnessEngine()
