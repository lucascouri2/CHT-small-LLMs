from dataclasses import dataclass
from typing import List

from schemas.refactoring_type import RefactoringType

@dataclass
class ClassDetail:
    class_name: str
    content: str

@dataclass
class ResponseContent:
    classes: List[ClassDetail]

@dataclass
class BenignClassInfo:
    html_url: str
    response_content: ResponseContent
    compile_result: int
    input_program_loc: int
    refactoring_type: RefactoringType
    prompt: str