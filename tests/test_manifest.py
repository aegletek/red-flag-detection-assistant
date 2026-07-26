from pathlib import Path

from orbit_core.admin import load_usecase_manifest


def test_manifest_is_valid() -> None:
    manifest = load_usecase_manifest(
        Path(__file__).parents[1]
        / "red_flag_detection_assistant"
        / "usecase-manifest.yaml"
    )

    assert manifest.id == "red-flag-detection-assistant"
    assert manifest.workflows[0].execution_adapter == "langgraph"
