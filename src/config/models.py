from dataclasses import dataclass

#
@dataclass
class AppConfig:
    settings: Settings
    subjects: list[SubjectConfig]


@dataclass
class Settings:
    application_name: str 

@dataclass
class SubjectConfig:
    name: str
    exam_board: str
    qualification: str
    anki_deck: str


