from red_flag_detection_assistant.domain import (
    RedFlagAnalysis,
    UseCaseTask,
)


def test_case_id_is_normalized() -> None:
    assert UseCaseTask.parse(" case-1001 ").case_id == "CASE-1001"


def test_red_flag_analysis_contract() -> None:
    analysis = RedFlagAnalysis.model_validate(
        {
            "case_id": "CASE-1001",
            "overall_risk": "high",
            "analysis_summary": "Multiple risk indicators.",
            "red_flags": [
                {
                    "category": "transaction_velocity",
                    "severity": "high",
                    "evidence": "Two large early transactions.",
                    "recommendation": "Perform enhanced review.",
                }
            ],
            "requires_human_review": True,
        }
    )

    assert analysis.overall_risk == "high"
    assert analysis.requires_human_review is True