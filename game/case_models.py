from pydantic import BaseModel
from typing import List

class Appearance(BaseModel):
    age: str
    face: str
    eyes: str = ""
    nose: str = ""
    mouth: str = ""
    hair: str
    body: str
    clothes: str
    special_features: str = ""

class Suspect(BaseModel):
    id: str
    name: str
    role: str
    hidden_truth: bool
    appearance: Appearance
    motive: str

class Witness(BaseModel):
    id: str
    name: str
    role: str
    known_facts: List[str]
    uncertain_facts: List[str] = []
    unknown_facts: List[str]
    personality: str

class Evidence(BaseModel):
    id: str
    title: str
    evidence_type: str = "вещественное доказательство"
    found_at: str = "на месте происшествия"
    description: str
    importance: str
    linked_to: List[str]
    can_visualize: bool
    known_conclusions: List[str] = []
    unknown_conclusions: List[str] = []

class Solution(BaseModel):
    culprit_id: str
    method: str
    key_evidence: List[str]
    motive: str

class Location(BaseModel):
    name: str
    description: str

class CaseData(BaseModel):
    case_id: str
    title: str
    intro: str
    location: Location
    suspects: List[Suspect]
    witnesses: List[Witness]
    evidence: List[Evidence]
    solution: Solution
