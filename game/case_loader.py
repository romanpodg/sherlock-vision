import json
import os
from typing import Dict
from app.logger import logger
from game.case_models import CaseData

class CaseLoader:
    def __init__(self, data_dir: str = "data/cases"):
        self.data_dir = data_dir
        self.cases: Dict[str, CaseData] = {}
        self._load_all()

    def _load_all(self):
        if not os.path.exists(self.data_dir):
            logger.warning(f"Cases directory {self.data_dir} does not exist.")
            return
            
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.data_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        case = CaseData(**data)
                        self.cases[case.case_id] = self._clean_case_data(case)
                        logger.info(f"Loaded case {case.case_id}")
                except Exception as e:
                    logger.error(f"Failed to load case {filename}: {e}")

    def _clean_case_data(self, case: CaseData) -> CaseData:
        import re
        
        replacements = {}
        
        # Замены подозреваемых
        for s in case.suspects:
            replacements[s.id.lower()] = s.name
            
            digits = re.findall(r"\d+", s.id)
            if digits:
                num = digits[0]
                roots = ["подозреваемый", "подозреваемого", "подозреваемому", "подозреваемым", "подозреваемом"]
                for root in roots:
                    replacements[f"{root}_{num}"] = s.name
                    replacements[f"{root} {num}"] = s.name
                    replacements[f"{root.capitalize()}_{num}"] = s.name
                    replacements[f"{root.capitalize()} {num}"] = s.name
                    
        # Замены улик
        for e in case.evidence:
            replacements[e.id.lower()] = f"«{e.title}»"
            
            digits = re.findall(r"\d+", e.id)
            if digits:
                num = digits[0]
                roots = ["улика", "улики", "улике", "улику", "уликой"]
                for root in roots:
                    replacements[f"{root}_{num}"] = f"«{e.title}»"
                    replacements[f"{root} {num}"] = f"«{e.title}»"
                    replacements[f"{root.capitalize()}_{num}"] = f"«{e.title}»"
                    replacements[f"{root.capitalize()} {num}"] = f"«{e.title}»"
                    
        # Сопоставление старых/несоответствующих ID улик по ключевым словам
        solution = case.solution
        for ev_id in solution.key_evidence:
            ev_name = None
            for e in case.evidence:
                if e.id == ev_id:
                    ev_name = e.title
                    break
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
            if ev_name:
                replacements[ev_id.lower()] = f"«{ev_name}»"
                replacements[ev_id.lower().replace("_", " ")] = f"«{ev_name}»"

        sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
        
        def clean_text(text: str) -> str:
            if not text:
                return text
            for key in sorted_keys:
                pattern = re.compile(re.escape(key), re.IGNORECASE)
                text = pattern.sub(replacements[key], text)
            return text

        # Выполняем очистку всех текстовых полей дела
        case.intro = clean_text(case.intro)
        case.location.description = clean_text(case.location.description)
        case.solution.method = clean_text(case.solution.method)
        case.solution.motive = clean_text(case.solution.motive)
        
        for s in case.suspects:
            s.motive = clean_text(s.motive)
            
        for w in case.witnesses:
            w.known_facts = [clean_text(f) for f in w.known_facts]
            w.uncertain_facts = [clean_text(f) for f in getattr(w, "uncertain_facts", [])]
            w.unknown_facts = [clean_text(f) for f in w.unknown_facts]
            w.personality = clean_text(w.personality)
            
        for e in case.evidence:
            e.description = clean_text(e.description)
            e.known_conclusions = [clean_text(c) for c in getattr(e, "known_conclusions", [])]
            e.unknown_conclusions = [clean_text(c) for c in getattr(e, "unknown_conclusions", [])]

        return case

    def get_case(self, case_id: str) -> CaseData | None:
        return self.cases.get(case_id)

    async def get_case_async(self, case_id: str) -> CaseData | None:
        if case_id in self.cases:
            return self.cases[case_id]
            
        from database.db import AsyncSessionLocal
        from database.models import CaseModel
        from sqlalchemy.future import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CaseModel).where(CaseModel.id == case_id)
            )
            db_case = result.scalar_one_or_none()
            if db_case:
                case = CaseData(**db_case.data)
                return self._clean_case_data(case)
        return None

case_loader = CaseLoader()
