import json 

def load_settings() -> dict:
    with open("config/settings.json", "r") as file:
        settings = json.load(file)
    return settings

def load_subjects() -> dict:
    with open("config/subjects.json", "r") as file:
        subjects = json.load(file)
    return subjects