import json
from .models import Settings, SubjectConfig
#Settings and subjects are loaded from their respective JSON files.
def load_settings() -> Settings:
    with open("config/settings.json", "r") as file:
        settings = json.load(file)
    return Settings(
          application_name=settings["application_name"]
        )

def load_subject(subject_data) -> SubjectConfig:
    return SubjectConfig(
        name=subject_data["name"],
        exam_board=subject_data["exam_board"],
        qualification=subject_data["qualification"],
        anki_deck=subject_data["anki_deck"]
    )

def load_subjects() -> list[SubjectConfig]:
    with open("config/subjects.json", "r") as file:
        subjects = json.load(file)
    return [load_subject(subject) for subject in subjects["subjects"]]
    

