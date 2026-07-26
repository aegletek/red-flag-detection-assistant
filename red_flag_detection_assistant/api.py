from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from orbit_core import WorkflowRequest

from orbit_core.admin import AdminOnboarding, AdminWorkflowTelemetry, CostSource


from .composition import UseCaseApplication, WORKFLOW_NAME, build_application

from .onboarding import build_admin_onboarding



class WorkflowTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=5000)
    user_id: str = Field(default="usecase-api", min_length=1, max_length=120)
    conversation_id: str = Field(default="usecase-api", min_length=1, max_length=120)


class WorkflowTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    output: str
    workflow_id: str
    request_id: str


def create_app(
    application: UseCaseApplication | None = None,

    onboarding: AdminOnboarding | None = None,

) -> FastAPI:
    application = application or build_application()

    onboarding = onboarding or build_admin_onboarding()
    workflow_telemetry = AdminWorkflowTelemetry(onboarding)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await onboarding.start()
        try:
            yield
        finally:
            await onboarding.stop()


    app = FastAPI(
        title=application.settings.app_name,
        version="0.1.0",

        lifespan=lifespan,

    )

    @app.get("/health/")
    async def health():
        return {"status": "healthy", "service": "red-flag-detection-assistant"}

    @app.get("/health/ready")
    async def readiness():
        return {
            "status": "ready",
            "service": "red-flag-detection-assistant",
            "version": app.version,
        }

    @app.post("/workflow/execute", response_model=WorkflowTaskResponse)
    async def execute(request: WorkflowTaskRequest):
        workflow_id = str(uuid4())
        request_id = str(uuid4())
        correlation_id = str(uuid4())

        run_id = str(uuid4())
        workflow_telemetry.started(
            WORKFLOW_NAME,
            run_id,
            workflow_id=workflow_id,
            request_id=request_id,
            correlation_id=correlation_id,
        )

        response = await application.runtime.execute(
            WorkflowRequest(
                workflow=WORKFLOW_NAME,
                input=request.task,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                workflow_id=workflow_id,
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )

        workflow_telemetry.finished(
            WORKFLOW_NAME,
            run_id,
            succeeded=response.success,
            workflow_id=response.workflow_id,
            request_id=response.request_id,
            correlation_id=response.correlation_id,
            trace_id=response.trace_id,
            duration_ms=response.duration_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cached_input_tokens=response.cached_input_tokens,
            cost_amount=response.cost_amount,
            cost_currency=response.cost_currency,
            cost_source=(
                CostSource.PROVIDER_REPORTED
                if response.cost_amount is not None
                else CostSource.UNAVAILABLE
            ),
            error_code="workflow_execution_failed" if not response.success else None,
        )

        if not response.success:
            raise HTTPException(status_code=502, detail="Workflow execution failed")
        return WorkflowTaskResponse(
            success=True,
            output=response.output,
            workflow_id=response.workflow_id,
            request_id=response.request_id,
        )

    return app
