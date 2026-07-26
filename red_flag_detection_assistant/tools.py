import asyncio

from orbit_core import BaseTool, ToolMetadata, ToolResponse

from .config import UseCaseSettings
from .domain import RedFlagAnalysis
from .repository import UseCaseRepository


PLATFORM_TOOL_NAMES = ("cosmos",)


class RedFlagRepositoryTool(BaseTool):
    """Persist validated findings in the use-case-owned PostgreSQL database."""

    def __init__(
        self,
        repository: UseCaseRepository | None = None,
    ) -> None:
        super().__init__(
            ToolMetadata(
                name="red_flag_repository",
                description="Persist validated red-flag findings",
                capabilities=["findings_persistence"],
            )
        )
        self._repository = repository
        self._schema_ready = False

    def _get_repository(self) -> UseCaseRepository:
        if self._repository is None:
            settings = UseCaseSettings()
            if not settings.database_url:
                raise RuntimeError("DATABASE_URL is required")
            self._repository = UseCaseRepository(settings.database_url)
        return self._repository

    async def execute(self, runtime) -> ToolResponse:
        request = runtime.state.get("tool_request")
        if request is None:
            return ToolResponse(
                success=False,
                error="ToolRequest is required",
            )

        try:
            analysis = RedFlagAnalysis.model_validate(
                request.parameters["analysis"]
            )
            repository = self._get_repository()

            if not self._schema_ready:
                await asyncio.to_thread(repository.create_schema)
                self._schema_ready = True

            finding_id = await asyncio.to_thread(
                repository.save,
                analysis,
                model_name=request.parameters.get("model_name"),
                workflow_id=runtime.trace.workflow_id,
                request_id=runtime.trace.request_id,
            )

            return ToolResponse(
                success=True,
                data={
                    "finding_id": finding_id,
                    "case_id": analysis.case_id,
                    "overall_risk": analysis.overall_risk,
                    "requires_human_review": (
                        analysis.requires_human_review
                    ),
                },
            )
        except Exception as exc:
            return ToolResponse(
                success=False,
                error=f"Unable to persist red-flag findings: {exc}",
            )


CUSTOM_TOOLS = (RedFlagRepositoryTool,)