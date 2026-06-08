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

def _is_suspect_mentioned(suspect_name: str, target_text: str) -> bool:
    import re
    target_text = target_text.lower()
    target_words = [re.sub(r"[^\w]", "", w) for w in target_text.split()]
    
    suspect_name = suspect_name.lower()
    s_parts = suspect_name.split()
    
    for part in s_parts:
        if len(part) <= 2:
            continue
        for t_word in target_words:
            if t_word.startswith(part):
                # Avoid matching first name (e.g. "Петр") to last name (e.g. "Петрова")
                if len(t_word) - len(part) <= 2:
                    return True
    return False

def get_discovered_suspects(case, witnesses_db: list) -> list:
    # Изначально подозреваемые скрыты, пока их не упомянут свидетели, 
    # либо пока их не найдут в уликах.

    discovered = []
    for s in case.suspects:
        is_found = False
        
        # 1. Match witness names
        for w in case.witnesses:
            if _is_suspect_mentioned(s.name, w.name):
                is_found = True
                break
        if is_found:
            discovered.append(s)
            continue
            
        # 2. Check intro and location description
        intro_desc = case.intro + " " + case.location.description
        if _is_suspect_mentioned(s.name, intro_desc):
            discovered.append(s)
            continue
            
        # 3. Check evidence titles and descriptions
        for e in case.evidence:
            e_text = e.title + " " + e.description
            if _is_suspect_mentioned(s.name, e_text):
                is_found = True
                break
        if is_found:
            discovered.append(s)
            continue
            
        # 4. Check witness cards of already interviewed witnesses
        for w in case.witnesses:
            w_db = next((w_d for w_d in witnesses_db if w_d.witness_id == w.id), None)
            if w_db and w_db.is_interviewed:
                facts_text = " ".join(w.known_facts + getattr(w, "uncertain_facts", []) + w.unknown_facts)
                if _is_suspect_mentioned(s.name, facts_text):
                    is_found = True
                    break
        if is_found:
            discovered.append(s)
            continue
            
        # 5. Check dialog history
        for w_db in witnesses_db:
            if w_db.dialog_history:
                history_str = json.dumps(w_db.dialog_history, ensure_ascii=False)
                if _is_suspect_mentioned(s.name, history_str):
                    is_found = True
                    break
        if is_found:
            discovered.append(s)
            continue
            
    return discovered

class ScenarioEngine:
    async def handle(self, user_id: int, text: str, payload: dict, inv: Investigation, inv_repo: InvestigationRepository):
        case = await case_loader.get_case_async(inv.case_id)
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
                from database.db import AsyncSessionLocal
                from database.models import InvestigationWitness, GeneratedImage
                from sqlalchemy.future import select
                
                async with AsyncSessionLocal() as session:
                    # Check if at least one witness has been interviewed (is_interviewed == True)
                    witness_res = await session.execute(
                        select(InvestigationWitness)
                        .where(InvestigationWitness.investigation_id == inv.id)
                        .where(InvestigationWitness.is_interviewed == True)
                    )
                    interviewed_witnesses = witness_res.scalars().all()
                    
                    # Also load all witnesses to pass to get_discovered_suspects
                    all_witnesses_res = await session.execute(
                        select(InvestigationWitness)
                        .where(InvestigationWitness.investigation_id == inv.id)
                    )
                    witnesses_db = all_witnesses_res.scalars().all()
                    
                    # Check if a portrait has already been generated
                    portrait_res = await session.execute(
                        select(GeneratedImage)
                        .where(GeneratedImage.investigation_id == inv.id)
                        .where(GeneratedImage.image_type == "portrait")
                    )
                    existing_portrait = portrait_res.scalars().first()
                
                if not interviewed_witnesses:
                    await vk_sender.send_message(
                        user_id,
                        "Для составления фоторобота у нас пока недостаточно сведений. Опросите хотя бы одного свидетеля, чтобы собрать приметы.",
                        keyboard=get_investigation_menu()
                    )
                elif existing_portrait:
                    await vk_sender.send_message(
                        user_id,
                        "Криминалисты уже составили один фоторобот для этого дела. Ресурсы ограничены!",
                        keyboard=get_investigation_menu()
                    )
                else:
                    discovered_suspects = get_discovered_suspects(case, witnesses_db)
                    
                    if not discovered_suspects:
                        await vk_sender.send_message(
                            user_id,
                            "Мы пока не выявили конкретных подозреваемых. Опросите свидетелей или изучите улики, чтобы установить круг подозреваемых.",
                            keyboard=get_investigation_menu()
                        )
                    else:
                        await inv_repo.update_state(inv.id, UserState.PORTRAIT_GENERATION)
                        
                        buttons = []
                        for s in discovered_suspects:
                            buttons.append([{"action": {"type": "text", "label": s.name, "payload": json.dumps({"command": "select_suspect_portrait", "id": s.id})}, "color": "secondary"}])
                        buttons.append([{"action": {"type": "text", "label": "Назад", "payload": json.dumps({"command": "investigation_menu"})}, "color": "primary"}])
                        keyboard = json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)
                        
                        await vk_sender.send_message(
                            user_id,
                            "Выберите подозреваемого, для которого нужно составить фоторобот:",
                            keyboard=keyboard
                        )
                
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
                await witness_engine.handle_question(user_id, inv.id, witness, text)
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

        elif state == UserState.PORTRAIT_GENERATION.value:
            if command == "select_suspect_portrait":
                suspect_id = payload.get("id")
                suspect = next((s for s in case.suspects if s.id == suspect_id), None)
                if suspect:
                    from game.portrait_engine import portrait_engine
                    await portrait_engine.request_portrait(user_id, inv.id, suspect)
                    await inv_repo.update_state(inv.id, UserState.INVESTIGATION_MENU)
                    await vk_sender.send_message(user_id, "Возвращаю вас в меню расследования, пока рисуется фоторобот...", keyboard=get_investigation_menu())
                else:
                    await vk_sender.send_message(user_id, "Ошибка: подозреваемый не найден.", keyboard=get_investigation_menu())
                    await inv_repo.update_state(inv.id, UserState.INVESTIGATION_MENU)
            else:
                await vk_sender.send_message(user_id, "Пожалуйста, выберите подозреваемого с помощью кнопок.")

        elif state == UserState.FINAL_VERSION.value:
            from game.final_evaluator import final_evaluator
            await vk_sender.send_message(user_id, "Ваша версия отправлена на оценку руководству. Ожидайте...")
            await final_evaluator.evaluate_version(user_id, inv.id, case, text)

        else:
            await vk_sender.send_message(user_id, f"Вы находитесь в состоянии {state}. Логика для него пока в разработке.", keyboard=get_investigation_menu())

scenario_engine = ScenarioEngine()
