from enum import Enum

class SensoryActionMode(Enum):
    ABSOLUTE = 1
    RELATIVE = 2

    @staticmethod
    def from_string(s: str):
        match(s.lower()):
            case "absolute":
                return SensoryActionMode.ABSOLUTE
            case "relative":
                return SensoryActionMode.RELATIVE
            case _:
                raise ValueError("Invalid sensory action mode")
            
    def __str__(self):
        match(self):
            case SensoryActionMode.ABSOLUTE:
                return "absolute"
            case SensoryActionMode.RELATIVE:
                return "relative"