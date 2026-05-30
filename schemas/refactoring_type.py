from enum import Enum

class RefactoringType(Enum):
    RENAME_CLASS = "rename class"
    RENAME_FIELD = "rename field"
    RENAME_METHOD = "rename method"
    RENAME_VARIABLE = "rename variable"
    CHANGE_METHOD_SIGNATURE = "change method signature"
    INTRODUCE_PARAMETER_OBJECT = "introduce parameter object"
    INTRODUCE_PARAMETER = "introduce parameter"
    EXTRACT_CLASS = "extract class"
    EXTRACT_METHOD = "extract method"
    EXTRACT_VARIABLE = "extract variable"
    ENCAPSULATE_COLLECTION = "encapsulate collection"
    ENCAPSULATE_RECORD = "encapsulate record"
    ENCAPSULATE_VARIABLE = "encapsulate variable"
    EXTRACT_SUPERCLASS = "extract superclass"
    HIDE_DELEGATE = "hide delegate"
    INTRODUCE_SPECIAL_CASE = "introduce special case"
    PARAMETERIZE_FUNCTION = "parameterize function"
    REMOVE_FLAG_ARGUMENT = "remove flag argument"
    REPLACE_COMMAND_WITH_FUNCTION = "replace command with function"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace conditional with polymorphism"
    REPLACE_CONSTRUCTOR_WITH_FACTORY_FUNCTION = "replace constructor with factory function"
    REPLACE_ERROR_CODE_WITH_EXCEPTION = "replace error code with exception"
    REPLACE_FUNCTION_WITH_COMMAND = "replace function with command"
    REPLACE_MAGIC_LITERAL = "replace magic literal"
    REPLACE_PRIMITIVE_WITH_OBJECT = "replace primitive with object"
    REPLACE_SUBCLASS_WITH_DELEGATE = "replace subclass with delegate"
    REPLACE_SUPERCLASS_WITH_DELEGATE = "replace superclass with delegate"
    REPLACE_TEMP_WITH_QUERY = "replace temp with query"
    REPLACE_TYPE_CODE_WITH_SUBCLASSES = "replace type code with subclasses"
    SEPARATE_QUERY_FROM_MODIFIER = "separate query from modifier"
    SPLIT_PHASE = "split phase"
    SPLIT_VARIABLE = "split variable"

    @staticmethod
    def from_string(refactoring_type: str):
        try:
            enum_key = refactoring_type.upper().replace(" ", "_")
            return RefactoringType[enum_key]
        except KeyError:
            raise ValueError(f"Unknown refactoring type: {refactoring_type}")