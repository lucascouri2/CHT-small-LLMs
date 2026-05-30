from enum import Enum


class HarmfulType(Enum):
    DOXING = "doxing"
    IDENTITY_ATTACK = "identity attack"
    IDENTITY_MISREPRESENTATION = "identity misrepresentation"
    INSULT = "insult"
    SEXUAL_AGGRESSION = "sexual aggression"
    THREAT_OF_VIOLENCE = "threat of violence"
    EATING_DISORDER_PROMOTION = "eating disorder promotion"
    SELF_HARM = "self-harm"
    MISINFORMATION = "misinformation"
    EXTREMISM = "extremism, terrorism & organized crime"
    ADULT_SEXUAL_SERVICES = "adult sexual services"
    CHILD_SEXUAL_ABUSE_MATERIALS = "child sexual abuse materials"
    SCAMS = "scams"

    @classmethod
    def from_string(cls, value: str):
        value = value.strip().lower()
        for item in cls:
            if item.value.lower() == value:
                return item
        raise ValueError(f"{value} is not a valid HarmfulType")


class Offensiveness(Enum):
    EXTREMELY_OFFENSIVE = "extremely offensive"
    SIGNIFICANTLY_OFFENSIVE = "significantly offensive"
    VERY_OFFENSIVE = "very offensive"
    MODERATELY_OFFENSIVE = "moderately offensive"

    @classmethod
    def from_string(cls, value: str):
        value = value.strip().lower()
        for item in cls:
            if item.value.lower() == value:
                return item
        raise ValueError(f"{value} is not a valid Offensiveness")