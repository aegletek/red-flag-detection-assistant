from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orbit_core import PromptTemplate, bootstrap

from .agents import AGENTS
from .config import UseCaseSettings
from .tools import CUSTOM_TOOLS, PLATFORM_TOOL_NAMES


WORKFLOW_FILES = {
    "red_flag_detection": "workflows/red_flag_detection.yaml",
}
WORKFLOW_NAMES = tuple(WORKFLOW_FILES)
WORKFLOW_NAME = "red_flag_detection"


@dataclass(slots=True)
class UseCaseApplication:
    runtime: Any
    settings: UseCaseSettings


def build_application(
    settings: UseCaseSettings | None = None,
) -> UseCaseApplication:
    settings = settings or UseCaseSettings()

    def configure(registry):
        for agent in AGENTS:
            registry.agent(agent)
            registry.prompt(
                PromptTemplate(
                    name=agent.profile.prompt_template,
                    description=f"Generated prompt for {agent.profile.capability}.",
                    template=(
                        "Perform the approved capability "
                        f"{agent.profile.capability} for: "
                        "{{ question }}"
                    ),
                )
            )
        for tool in CUSTOM_TOOLS:
            registry.tool(tool())
        # Platform tools are registered by Orbit Core bootstrap. The tuple is
        # retained as an explicit, reviewable dependency declaration.
        _ = PLATFORM_TOOL_NAMES
        package_root = Path(__file__).parent
        for workflow_name, relative_path in WORKFLOW_FILES.items():
            registry.workflow(workflow_name, package_root / relative_path)

    return UseCaseApplication(
        runtime=bootstrap(configure).runtime(),
        settings=settings,
    )
