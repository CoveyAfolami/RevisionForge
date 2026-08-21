from dataclasses import dataclass

#Settings and SubjectConfig dataclasses to represent the configuration data
@dataclass
class Settings:
    application_name: str 

@dataclass
class SubjectConfig:
    name: str
    exam_board: str
    qualification: str
    anki_deck: str

