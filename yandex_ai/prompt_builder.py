from yandex_ai.system_prompts import WITNESS_PROMPT, EVIDENCE_PROMPT, EVALUATION_PROMPT
from game.case_models import Witness, Evidence, Suspect, Solution

def build_witness_prompt(witness: Witness) -> str:
    known = "\n".join([f"- {f}" for f in witness.known_facts])
    unknown = "\n".join([f"- {f}" for f in witness.unknown_facts])
    
    return WITNESS_PROMPT.format(
        name=witness.name,
        role=witness.role,
        personality=witness.personality,
        known_facts=known,
        unknown_facts=unknown
    )

def build_evidence_prompt(evidence: Evidence, question: str) -> str:
    return EVIDENCE_PROMPT.format(
        title=evidence.title,
        description=evidence.description,
        importance=evidence.importance,
        question=question
    )

def build_yandex_art_portrait_prompt(suspect: Suspect) -> str:
    app = suspect.appearance
    return f"Realistic detective suspect portrait, fictional character, age {app.age}, {app.body} build, {app.face} face, {app.hair} hair, wearing {app.clothes}, neutral facial expression, police sketch style, realistic lighting, plain background, no text, no logos."

def build_final_evaluation_prompt(solution: Solution, user_version: str) -> str:
    key_ev = ", ".join(solution.key_evidence)
    return EVALUATION_PROMPT.format(
        culprit_id=solution.culprit_id,
        method=solution.method,
        key_evidence=key_ev,
        motive=solution.motive,
        user_version=user_version
    )
