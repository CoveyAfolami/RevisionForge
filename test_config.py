from src.config.loader import load_settings, load_subjects 

settings = load_settings()
subjects = load_subjects()

print(settings)
print(settings["application_name"])

print(subjects)