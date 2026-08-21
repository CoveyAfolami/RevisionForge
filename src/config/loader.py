import json
from .models import Settings, SubjectConfig
#Settings and SubjectConfig dataclasses to represent the configuration data

#Loads the settings from the settings.json file and returns a Settings object
def load_settings() -> Settings:
    with open("config/settings.json", "r") as file:
        settings = json.load(file)
    return Settings(
          application_name=settings["application_name"]
        )

#Loads the subjects from the subjects.json file and returns a list of SubjectConfig objects
def load_subject(subject_data, subject_name) -> SubjectConfig:
    return SubjectConfig(
        name=subject_name,
        exam_board=subject_data["exam_board"],
        qualification=subject_data["qualification"],
        anki_deck=subject_data["anki_deck"]
    )

#Loads the subjects from the subjects.json file and returns a list of SubjectConfig objects
def load_subjects() -> list[SubjectConfig]:
    with open("config/subjects.json", "r") as file:
        subjects = json.load(file)
    return [load_subject(subject, subject_name) for subject_name, subject in subjects["subjects"].items()]
    

