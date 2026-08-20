import json

with open("config/settings.json", "r") as file:
    settings = json.load(file)

print(settings)
print(settings["application_name"])