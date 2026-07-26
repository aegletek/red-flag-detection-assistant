from dataclasses import asdict, dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True, slots=True)
class UseCaseTask:
    value: str

    @classmethod
    def parse(cls, value: str) -> "UseCaseTask":
        case_id = value.strip().upper()
        if not case_id:
            raise ValueError("case_id is required")
        if len(case_id) > 64:
            raise ValueError("case_id must not exceed 64 characters")
        if not all(character.isalnum() or character in "-_" for character in case_id):
            raise ValueError("case_id contains unsupported characters")
        return cls(value=case_id)

    @property
    def case_id(self) -> str:
        return self.value

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class RedFlagItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    evidence: str = Field(min_length=1, max_length=1000)
    recommendation: str = Field(min_length=1, max_length=1000)


class RedFlagAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=64)
    overall_risk: Literal["low", "medium", "high", "critical"]
    analysis_summary: str = Field(min_length=1, max_length=4000)
    red_flags: list[RedFlagItem] = Field(default_factory=list, max_length=50)
    requires_human_review: bool = True