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
