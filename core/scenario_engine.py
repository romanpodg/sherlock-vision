from database.repositories import InvestigationRepository
from database.models import Investigation
from core.states import UserState
from game.case_loader import case_loader
from vk_bot.vk_sender import vk_sender
from game.witness_engine import witness_engine
from game.evidence_engine import evidence_engine
import json

def get_investigation_menu():
    return json.dumps({
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "Осмотреть место", "payload": json.dumps({"command": "inspect_location"})}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Опросить свидетелей", "payload": json.dumps({"command": "list_witnesses"})}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Изучить улики", "payload": json.dumps({"command": "list_evidence"})}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Создать фоторобот", "payload": json.dumps({"command": "start_portrait"})}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Дать финальную версию", "payload": json.dumps({"command": "final_version"})}, "color": "negative"}],
        ]
    }, ensure_ascii=False)

def get_back_button(command: str = "investigation_menu"):
    return json.dumps({
        "one_time": False,
        "buttons": [[{"action": {"type": "text", "label": "Назад", "payload": json.dumps({"command": command})}, "color": "primary"}]]
    }, ensure_ascii=False)

class ScenarioEngine:
    async def handle(self, user_id: int, text: str, payload: dict, inv: Investigation, inv_repo: InvestigationRepository):
        case = case_loader.get_case(inv.case_id)
        if not case:
            await vk_sender.send_message(user_id, "Дело не найдено. Обратитесь к администратору.")
            return

        state = inv.state
        command = payload.get("command")

        # Handle global "back" commands
        if command == "investigation_menu" or text.lower() == "назад":
            await inv_repo.update_state(inv.id, UserState.INVESTIGATION_MENU)
            await vk_sender.send_message(user_id, "Вы вернулись к материалам дела. Что делаем дальше?", keyboard=get_investigation_menu())
            return
            
        if command == "main_menu":
            await inv_repo.update_state(inv.id, UserState.MAIN_MENU)
            await vk_sender.send_message(user_id, "Для возврата в меню напишите /start или Старт.")
            return

        if state == UserState.CASE_INTRO.value:
            await vk_sender.send_message(
                user_id, 
                f"Вы приступили к делу: {case.title}\n\n{case.intro}",
                keyboard=get_investigation_menu()
            )
            await inv_repo.update_state(inv.id, UserState.INVESTIGATION_MENU)

        elif state == UserState.INVESTIGATION_MENU.value:
            if command == "inspect_location":
                await vk_sender.send_message(user_id, f"Вы осматриваете место: {case.location.name}.\n{case.location.description}", keyboard=get_investigation_menu())
            elif command == "list_witnesses":
                buttons = []
                for w in case.witnesses:
                    buttons.append([{"action": {"type": "text", "label": w.name, "payload": json.dumps({"command": "select_witness", "id": w.id})}, "color": "secondary"}])
                buttons.append([{"action": {"type": "text", "label": "Назад", "payload": json.dumps({"command": "investigation_menu"})}, "color": "primary"}])
                keyboard = json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)
                await vk_sender.send_message(user_id, "Кого из свидетелей вы хотите опросить?", keyboard=keyboard)
                await inv_repo.update_state(inv.id, UserState.WITNESS_SELECTION)
                
            elif command == "list_evidence":
                buttons = []
                for e in case.evidence:
                    buttons.append([{"action": {"type": "text", "label": e.title, "payload": json.dumps({"command": "select_evidence", "id": e.id})}, "color": "secondary"}])
                buttons.append([{"action": {"type": "text", "label": "Назад", "payload": json.dumps({"command": "investigation_menu"})}, "color": "primary"}])
                keyboard = json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)
                await vk_sender.send_message(user_id, "Какую улику изучить?", keyboard=keyboard)
                await inv_repo.update_state(inv.id, UserState.EVIDENCE_LIST)
                
            elif command == "start_portrait":
                suspect = case.suspects[0]
                from game.portrait_engine import portrait_engine
                await portrait_engine.request_portrait(user_id, inv.id, suspect)
                await vk_sender.send_message(user_id, "Возвращаю вас в меню расследования, пока рисуется фоторобот...", keyboard=get_investigation_menu())
                
            elif command == "final_version":
                await inv_repo.update_state(inv.id, UserState.FINAL_VERSION)
                await vk_sender.send_message(user_id, "Опишите вашу итоговую версию: кто совершил преступление, как и почему. (Напишите 'Назад', если пока не готовы).", keyboard=get_back_button())

            else:
                await vk_sender.send_message(user_id, "Что вы хотите сделать дальше?", keyboard=get_investigation_menu())

        elif state == UserState.WITNESS_SELECTION.value:
            if command == "select_witness":
                w_id = payload.get("id")
                from database.db import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    inv_db = await session.get(Investigation, inv.id)
                    inv_db.current_witness_id = w_id
                    inv_db.state = UserState.WITNESS_DIALOGUE.value
                    await session.commit()
                
                await vk_sender.send_message(user_id, "Вы начали допрос. Задайте ваш вопрос или напишите 'Назад' для выхода.", keyboard=get_back_button())
            else:
                await vk_sender.send_message(user_id, "Пожалуйста, выберите свидетеля с помощью кнопок.")

        elif state == UserState.WITNESS_DIALOGUE.value:
            w_id = inv.current_witness_id
            witness = next((w for w in case.witnesses if w.id == w_id), None)
            if witness:
                await vk_sender.send_message(user_id, "Свидетель думает...")
                await witness_engine.handle_question(user_id, witness, text)
            else:
                await vk_sender.send_message(user_id, "Ошибка: свидетель не найден.", keyboard=get_investigation_menu())
                await inv_repo.update_state(inv.id, UserState.INVESTIGATION_MENU)

        elif state == UserState.EVIDENCE_LIST.value:
            if command == "select_evidence":
                e_id = payload.get("id")
                from database.db import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    inv_db = await session.get(Investigation, inv.id)
                    inv_db.current_evidence_id = e_id
                    inv_db.state = UserState.EVIDENCE_ANALYSIS.value
                    await session.commit()
                    
                evidence = next((e for e in case.evidence if e.id == e_id), None)
                await vk_sender.send_message(user_id, f"Вы изучаете: {evidence.title}\n{evidence.description}\nЗадайте вопрос эксперту или напишите 'Назад'.", keyboard=get_back_button())
            else:
                await vk_sender.send_message(user_id, "Выберите улику кнопками.")

        elif state == UserState.EVIDENCE_ANALYSIS.value:
            e_id = inv.current_evidence_id
            evidence = next((e for e in case.evidence if e.id == e_id), None)
            if evidence:
                await vk_sender.send_message(user_id, "Эксперт анализирует...")
                await evidence_engine.handle_analysis(user_id, evidence, text)
            else:
                await vk_sender.send_message(user_id, "Ошибка: улика не найдена.", keyboard=get_investigation_menu())
                await inv_repo.update_state(inv.id, UserState.INVESTIGATION_MENU)

        elif state == UserState.FINAL_VERSION.value:
            from game.final_evaluator import final_evaluator
            await vk_sender.send_message(user_id, "Ваша версия отправлена на оценку руководству. Ожидайте...")
            await final_evaluator.evaluate_version(user_id, inv.id, case, text)

        else:
            await vk_sender.send_message(user_id, f"Вы находитесь в состоянии {state}. Логика для него пока в разработке.", keyboard=get_investigation_menu())

scenario_engine = ScenarioEngine()
