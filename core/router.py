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
        if active_inv and command not in ["start_new_case", "continue_case", "help"] and text.lower() not in ["/start", "старт"]:
            await scenario_engine.handle(user_id, text, payload, active_inv, inv_repo)
            return

        if command == "start_new_case" or text.lower() == "начать новое дело":
            case_id = "case_001_gallery_ring"
            active_inv = await inv_repo.create_investigation(user.id, case_id)
            await scenario_engine.handle(user_id, text, payload, active_inv, inv_repo)
            
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
