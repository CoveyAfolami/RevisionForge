from dataclasses import dataclass

# class Application:
#     def start(self) -> None:
#         print("Application is started.")

@dataclass
class Application:
    name: str = "RevisionForge"

    def start(self) -> None:
        try:
            print(f"{self.name} started.")
        except Exception as error:
            print(f"{self.name} failed to start: {error}")