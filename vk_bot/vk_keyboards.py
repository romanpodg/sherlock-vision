import json

def _get_button(label: str, color: str = "secondary", payload: dict = None) -> dict:
    if payload is None:
        payload = {"button": label}
    return {
        "action": {
            "type": "text",
            "label": label,
            "payload": json.dumps(payload)
        },
        "color": color # primary, secondary, negative, positive
    }

def get_main_menu() -> str:
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                _get_button("Начать новое дело", "primary", {"command": "start_new_case"}),
                _get_button("Сгенерировать случайное дело", "primary", {"command": "generate_random_case"}),
            ],
            [
                _get_button("Продолжить расследование", "secondary", {"command": "continue_case"}),
            ],
            [
                _get_button("Справка", "secondary", {"command": "help"}),
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def get_empty_keyboard() -> str:
    keyboard = {
        "one_time": True,
        "buttons": []
    }
    return json.dumps(keyboard, ensure_ascii=False)

def get_setting_menu() -> str:
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                _get_button("Классический детектив", "primary", {"setting": "Классический детектив"}),
                _get_button("Нуар", "primary", {"setting": "Нуар"}),
            ],
            [
                _get_button("Киберпанк", "primary", {"setting": "Киберпанк"}),
                _get_button("Современность", "primary", {"setting": "Современность"}),
            ],
            [
                _get_button("Отмена", "negative", {"command": "main_menu"}),
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def get_difficulty_menu() -> str:
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                _get_button("Легко", "positive", {"difficulty": "Легко"}),
                _get_button("Средне", "primary", {"difficulty": "Средне"}),
                _get_button("Сложно", "negative", {"difficulty": "Сложно"}),
            ],
            [
                _get_button("Отмена", "negative", {"command": "main_menu"}),
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)
