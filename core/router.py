import json
from vk_bot.vk_sender import vk_sender
from vk_bot.vk_keyboards import get_main_menu, get_empty_keyboard
from app.logger import logger
from database.db import AsyncSessionLocal
from database.repositories import UserRepository, InvestigationRepository
from core.states import UserState
from core.scenario_engine import scenario_engine

async def route_message(user_id: int, text: str, payload_str: str = None):
    payload = {}
    if payload_str:
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            pass

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        inv_repo = InvestigationRepository(session)
        
        user = await user_repo.get_or_create_user(user_id)
        active_inv = await inv_repo.get_active_investigation(user.id)
        current_state = active_inv.state if active_inv else UserState.START.value
        command = payload.get("command")
        
        # Route to scenario engine if there is an active investigation and it's not a top-level command
        if active_inv and command not in ["start_new_case", "continue_case", "help", "generate_random_case", "main_menu"] and text.lower() not in ["/start", "старт"]:
            if active_inv.case_id == "pending":
                if active_inv.state == UserState.SELECT_SETTING.value:
                    setting = payload.get("setting")
                    if setting:
                        data = {"setting": setting}
                        active_inv.suspect_description = json.dumps(data, ensure_ascii=False)
                        active_inv.state = UserState.SELECT_DIFFICULTY.value
                        await session.commit()
                        from vk_bot.vk_keyboards import get_difficulty_menu
                        await vk_sender.send_message(user_id, "Отлично! Теперь выберите уровень сложности:", keyboard=get_difficulty_menu())
                    else:
                        from vk_bot.vk_keyboards import get_setting_menu
                        await vk_sender.send_message(user_id, "Пожалуйста, выберите сеттинг с помощью кнопок.", keyboard=get_setting_menu())
                elif active_inv.state == UserState.SELECT_DIFFICULTY.value:
                    difficulty = payload.get("difficulty")
                    if difficulty:
                        data = json.loads(active_inv.suspect_description or "{}")
                        setting = data.get("setting", "Современность")
                        active_inv.state = "generating"
                        await session.commit()
                        
                        await vk_sender.send_message(user_id, f"Начинаю генерацию...\nСеттинг: {setting}\nСложность: {difficulty}", keyboard=get_empty_keyboard())
                        
                        import asyncio
                        from game.scenario_generator import scenario_generator
                        
                        async def generate_and_start(vk_uid: int, db_uid: int, inv_id: int, s: str, d: str):
                            try:
                                logger.info(f"Starting generate_and_start background task for vk_user {vk_uid} (db_user {db_uid})")
                                async def progress_callback(msg: str):
                                    await vk_sender.send_message(vk_uid, msg)
                                    
                                case = await scenario_generator.generate_case(setting=s, difficulty=d, callback=progress_callback)
                                async with AsyncSessionLocal() as sess:
                                    local_repo = InvestigationRepository(sess)
                                    inv = await local_repo.get_active_investigation(db_uid)
                                    if case and inv and inv.id == inv_id:
                                        inv.case_id = case.case_id
                                        inv.state = UserState.CASE_INTRO.value
                                        inv.suspect_description = None
                                        await sess.commit()
                                        await scenario_engine.handle(vk_uid, "", {}, inv, local_repo)
                                    elif not case:
                                        if inv and inv.id == inv_id:
                                            inv.is_finished = True
                                            await sess.commit()
                                        await vk_sender.send_message(vk_uid, "К сожалению, не удалось сгенерировать дело. Попробуйте еще раз позже.", keyboard=get_main_menu())
                            except Exception as e:
                                logger.exception(f"Unhandled exception in generate_and_start background task: {e}")
                                await vk_sender.send_message(vk_uid, f"Произошла системная ошибка при генерации дела. Пожалуйста, обратитесь к разработчику.")
                                
                        asyncio.create_task(generate_and_start(user.vk_user_id, user.id, active_inv.id, setting, difficulty))
                    else:
                        from vk_bot.vk_keyboards import get_difficulty_menu
                        await vk_sender.send_message(user_id, "Пожалуйста, выберите сложность с помощью кнопок.", keyboard=get_difficulty_menu())
            else:
                await scenario_engine.handle(user_id, text, payload, active_inv, inv_repo)
            return

        if command == "main_menu":
            if active_inv and active_inv.case_id == "pending":
                active_inv.is_finished = True
                await session.commit()
            await vk_sender.send_message(user_id, "Возврат в главное меню.", keyboard=get_main_menu())

        elif command == "start_new_case" or text.lower() == "начать новое дело":
            case_id = "case_001_gallery_ring"
            active_inv = await inv_repo.create_investigation(user.id, case_id)
            await scenario_engine.handle(user_id, text, payload, active_inv, inv_repo)
            
        elif command == "generate_random_case":
            if active_inv:
                active_inv.is_finished = True
                await session.commit()
            active_inv = await inv_repo.create_investigation(user.id, "pending")
            active_inv.state = UserState.SELECT_SETTING.value
            await session.commit()
            
            from vk_bot.vk_keyboards import get_setting_menu
            await vk_sender.send_message(user_id, "Выберите сеттинг для нового дела:", keyboard=get_setting_menu())

        elif command == "continue_case" or text.lower() == "продолжить расследование":
            if active_inv:
                await scenario_engine.handle(user_id, text, payload, active_inv, inv_repo)
            else:
                await vk_sender.send_message(user_id, "У вас нет активных дел.", keyboard=get_main_menu())
                
        elif command == "help" or text.lower() == "справка":
            help_text = "Справка по боту:\nДля навигации используйте кнопки меню."
            await vk_sender.send_message(user_id, help_text, keyboard=get_main_menu())

        elif text.lower() in ["/start", "старт"] or current_state == UserState.START.value:
            welcome_text = (
                "Добро пожаловать в Sherlock Vision. Вы — детектив, которому поручено расследование. "
                "Я помогу вам собрать показания, восстановить внешность подозреваемого, "
                "визуализировать улики и подготовить итоговую версию произошедшего."
            )
            await vk_sender.send_message(user_id, welcome_text, keyboard=get_main_menu())
            
        else:
            await vk_sender.send_message(user_id, f"Главное меню. Вы написали: {text}", keyboard=get_main_menu())
