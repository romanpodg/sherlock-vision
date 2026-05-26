from enum import Enum

class UserState(str, Enum):
    START = "start"
    MAIN_MENU = "main_menu"
    CASE_INTRO = "case_intro"
    INVESTIGATION_MENU = "investigation_menu"
    LOCATION_INSPECTION = "location_inspection"
    WITNESS_SELECTION = "witness_selection"
    WITNESS_DIALOGUE = "witness_dialogue"
    EVIDENCE_LIST = "evidence_list"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    SUSPECT_DESCRIPTION = "suspect_description"
    PORTRAIT_GENERATION = "portrait_generation"
    PORTRAIT_REFINEMENT = "portrait_refinement"
    IMAGE_GENERATION_WAITING = "image_generation_waiting"
    FINAL_VERSION = "final_version"
    CASE_RESULT = "case_result"
