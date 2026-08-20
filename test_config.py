from src.config.loader import load_settings 

settings = load_settings()

print(settings)
print(settings["application_name"])