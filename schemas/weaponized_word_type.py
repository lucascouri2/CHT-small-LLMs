from enum import Enum

class WeaponizedWordType(Enum):
    DEROGATORY = "derogatory"
    THREATENING = "threatening"
    WATCHWORD = "watchwords"
    DISCRIMINATORY = "discriminatory"

class DiscriminatoryType(Enum):
    NATIONALITY = "is_about_nationality"
    ETHNICITY = "is_about_ethnicity"
    RELIGION = "is_about_religion"
    GENDER = "is_about_gender"
    ORIENTATION = "is_about_orientation"
    DISABILITY = "is_about_disability"
    CLASS = "is_about_class"
