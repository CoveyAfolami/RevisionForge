from dataclasses import dataclass

# class Application:
#     def start(self) -> None:
#         print("Application is started.")

@dataclass
class Application:
    name: str = "RevisionForge"

    def start(self) -> None:
        print(f"{self.name} started.")
