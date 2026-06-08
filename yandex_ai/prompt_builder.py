import re
from yandex_ai.system_prompts import (
    WITNESS_SYSTEM_PROMPT,
    WITNESS_USER_MESSAGE,
    EVIDENCE_SYSTEM_PROMPT,
    EVIDENCE_USER_PROMPT,
    EVALUATION_SYSTEM_PROMPT,
    EVALUATION_USER_PROMPT
)
from game.case_models import Witness, Evidence, Suspect, Solution, CaseData

def build_witness_prompt(witness: Witness, question: str) -> tuple[str, str]:
    known = "\n".join([f"- {f}" for f in witness.known_facts]) or "- Нет точных сведений"
    uncertain = "\n".join([f"- {f}" for f in getattr(witness, "uncertain_facts", [])]) or "- Нет неуверенных сведений"
    unknown = "\n".join([f"- {f}" for f in witness.unknown_facts]) or "- Нет отдельно указанных неизвестных тем"
    
    system_prompt = WITNESS_SYSTEM_PROMPT
    user_message = WITNESS_USER_MESSAGE.format(
        name=witness.name,
        role=witness.role,
        personality=witness.personality,
        known_facts=known,
        uncertain_facts=uncertain,
        unknown_facts=unknown,
        user_question=question
    )
    return system_prompt, user_message

def build_evidence_prompt(evidence: Evidence, question: str) -> tuple[str, str]:
    known = "\n".join([f"- {c}" for c in getattr(evidence, "known_conclusions", [])]) or "- Нет точных экспертных выводов"
    unknown = "\n".join([f"- {c}" for c in getattr(evidence, "unknown_conclusions", [])]) or "- Нет явных ограничений на выводы"
    
    system_prompt = EVIDENCE_SYSTEM_PROMPT
    user_message = EVIDENCE_USER_PROMPT.format(
        title=evidence.title,
        evidence_type=getattr(evidence, "evidence_type", "вещественное доказательство"),
        found_at=getattr(evidence, "found_at", "на месте происшествия"),
        description=evidence.description,
        importance=evidence.importance,
        known_conclusions=known,
        unknown_conclusions=unknown,
        question=question
    )
    return system_prompt, user_message

def _short(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit].rstrip(" ,.;:")


def build_yandex_art_portrait_prompt(suspect: Suspect) -> str:
    app = suspect.appearance
    prompt = (
        "Forensic sketch, identikit, front-facing portrait. "
        f"Age {_short(app.age, 10)}; "
        f"{_short(app.body, 20)}; "
        f"Face: {_short(app.face, 40)}; "
        f"Eyes: {_short(getattr(app, 'eyes', ''), 30)}; "
        f"Nose: {_short(getattr(app, 'nose', ''), 30)}; "
        f"Mouth: {_short(getattr(app, 'mouth', ''), 30)}; "
        f"Hair: {_short(app.hair, 40)}; "
        f"Clothes: {_short(app.clothes, 40)}; "
        f"Features: {_short(getattr(app, 'special_features', ''), 40)}. "
        "Pencil drawing, monochrome."
    )
    return prompt[:500]

def build_final_evaluation_prompt(case: CaseData, user_version: str) -> tuple[str, str]:
    solution = case.solution
    culprit_id = solution.culprit_id
    culprit_name = "Неизвестно"
    culprit_role = "Неизвестно"
    for s in case.suspects:
        if s.id == culprit_id:
            culprit_name = s.name
            culprit_role = s.role
            break
            
    key_ev_names = []
    for ev_id in solution.key_evidence:
        ev_name = None
        # 1. Точное совпадение по ID
        for e in case.evidence:
            if e.id == ev_id:
                ev_name = e.title
                break
                
        # 2. Поиск по ключевым словам (для обратной совместимости со старыми делами)
        if not ev_name:
            ev_id_clean = ev_id.lower().replace("_", " ")
            keywords_map = {
                "pearl": "жемчуг",
                "footprint": "след",
                "footprints": "след",
                "guest": "гост",
                "visitor": "посетит",
                "report": "отчет",
                "reports": "отчет",
                "fabric": "ткань",
                "ink": "чернил",
                "letter": "письмо",
                "note": "записк",
                "glass": "стекл",
                "window": "окно",
                "ring": "кольц",
                "key": "ключ",
                "blood": "кров",
                "poison": "яд",
                "knife": "нож",
                "gun": "оруж",
                "fingerprint": "отпечат",
                "fingerprints": "отпечат",
                "handwriting": "почерк"
            }
            best_match = None
            best_score = 0
            for e in case.evidence:
                score = 0
                title_lower = e.title.lower()
                desc_lower = e.description.lower()
                id_lower = e.id.lower()
                for en_word, ru_word in keywords_map.items():
                    if en_word in ev_id_clean:
                        if ru_word in title_lower or ru_word in desc_lower or ru_word in id_lower:
                            score += 1
                if score > best_score:
                    best_score = score
                    best_match = e.title
            if best_match and best_score > 0:
                ev_name = best_match

        # 3. Сопоставление по индексу, если ID содержит число
        if not ev_name:
            digits = re.findall(r"\d+", ev_id)
            if digits:
                idx = int(digits[0]) - 1
                if 0 <= idx < len(case.evidence):
                    ev_name = case.evidence[idx].title
                    
        # 4. Фоллбек: красивое форматирование самого ID
        if not ev_name:
            ev_name = ev_id.replace("_", " ").capitalize()
            
        key_ev_names.append(ev_name)
        
    key_ev = ", ".join(key_ev_names)
    
    system_prompt = EVALUATION_SYSTEM_PROMPT
    user_message = EVALUATION_USER_PROMPT.format(
        culprit_id=culprit_id,
        culprit_name=culprit_name,
        culprit_role=culprit_role,
        method=solution.method,
        key_evidence=key_ev,
        motive=solution.motive,
        user_version=user_version
    )
    return system_prompt, user_message
