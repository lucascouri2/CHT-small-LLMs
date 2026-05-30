from dataclasses import dataclass

from schemas.refactoring_type import RefactoringType


@dataclass
class UnethicalInput:
    prompt: str
    benign_program: str
    refactoring_type: RefactoringType