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
                        self.cases[case.case_id] = case
                        logger.info(f"Loaded case {case.case_id}")
                except Exception as e:
                    logger.error(f"Failed to load case {filename}: {e}")

    def get_case(self, case_id: str) -> CaseData | None:
        return self.cases.get(case_id)

case_loader = CaseLoader()
