from dataclasses import dataclass

#Settings and Subjects dataclasses to represent the configuration data
@dataclass
class Settings:
    application_name: str 

@dataclass
class Subject:
    name: str
    exam_board: str
    qualification: str

