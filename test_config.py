import src.config.loader as loader 

settings = loader.load_settings()
subjects = loader.load_subjects()


print(settings)
print(settings.application_name)

#print(subjects)
print(subjects[0])