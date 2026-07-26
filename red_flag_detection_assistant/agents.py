import json

from orbit_core import (
    ChatRequest,
    ToolRequest,
    UserMessage,
    WorkerAgent,
    WorkerProfile,
)

from .domain import RedFlagAnalysis, UseCaseTask


def _load_previous_output(runtime) -> dict:
    value = runtime.prompt_variables.get("previous_output", "")
    if not value:
        raise RuntimeError("Previous workflow output is unavailable")

    if isinstance(value, dict):
        return value

    return json.loads(value)


def _extract_json_object(content: str) -> dict:
    text = content.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end < start:
        raise ValueError("LLM response does not contain a JSON object")

    return json.loads(text[start : end + 1])


class CaseDataRetrievalAgent(WorkerAgent):
    profile = WorkerProfile(
        capability="case_data_retrieval",
        prompt_template="case_data_retrieval",
    )
    tool_names = ("cosmos",)

    async def process(self, runtime):
        task = UseCaseTask.parse(
            runtime.prompt_variables["question"]
        )

        runtime.state["tool_request"] = ToolRequest(
            tool_name="cosmos",
            parameters={
                "query": (
                    "SELECT * FROM c "
                    "WHERE c.id = @case_id"
                ),
                "parameters": [
                    {
                        "name": "@case_id",
                        "value": task.case_id,
                    }
                ],
            },
        )

        response = await self.tool_executor.execute(
            "cosmos",
            runtime,
        )

        if not response.success:
            raise RuntimeError(
                f"Cosmos query failed: {response.error}"
            )

        records = response.data or []
        if not records:
            raise ValueError(
                f"Case {task.case_id} was not found"
            )

        return json.dumps(
            {
                "case_id": task.case_id,
                "case_data": records[0],
            },
            default=str,
            sort_keys=True,
        )


class RedFlagAnalysisAgent(WorkerAgent):
    profile = WorkerProfile(
        capability="red_flag_analysis",
        prompt_template="red_flag_analysis",
    )
    tool_names = ()

    async def process(self, runtime):
        retrieved = _load_previous_output(runtime)
        case_id = retrieved["case_id"]
        case_data = retrieved["case_data"]

        prompt = f"""
You are a financial and operational risk analyst.

Analyze the supplied case using only the provided evidence.
Do not invent missing facts. Identify material red flags that require
human review.

Return only one valid JSON object with this exact structure:

{{
  "case_id": "{case_id}",
  "overall_risk": "low|medium|high|critical",
  "analysis_summary": "concise evidence-based summary",
  "red_flags": [
    {{
      "category": "category name",
      "severity": "low|medium|high|critical",
      "evidence": "specific evidence from the supplied case",
      "recommendation": "recommended human follow-up"
    }}
  ],
  "requires_human_review": true
}}

Case data:
{json.dumps(case_data, default=str, sort_keys=True)}
""".strip()

        response = await self.llm.chat(
            ChatRequest(
                messages=[UserMessage(content=prompt)],
                temperature=0.1,
                max_tokens=2000,
            ),
            runtime,
        )

        result = _extract_json_object(response.content)
        result["case_id"] = case_id
        result["requires_human_review"] = True

        analysis = RedFlagAnalysis.model_validate(result)

        return json.dumps(
            {
                "analysis": analysis.model_dump(mode="json"),
                "model_name": response.model,
            },
            sort_keys=True,
        )


class FindingsPersistenceAgent(WorkerAgent):
    profile = WorkerProfile(
        capability="findings_persistence",
        prompt_template="findings_persistence",
    )
    tool_names = ("red_flag_repository",)

    async def process(self, runtime):
        analyzed = _load_previous_output(runtime)

        analysis = RedFlagAnalysis.model_validate(
            analyzed["analysis"]
        )

        runtime.state["tool_request"] = ToolRequest(
            tool_name="red_flag_repository",
            parameters={
                "analysis": analysis.model_dump(mode="json"),
                "model_name": analyzed.get("model_name"),
            },
        )

        response = await self.tool_executor.execute(
            "red_flag_repository",
            runtime,
        )

        if not response.success:
            raise RuntimeError(response.error)

        return json.dumps(
            {
                "status": "persisted",
                **response.data,
            },
            sort_keys=True,
        )


AGENTS = (
    CaseDataRetrievalAgent,
    RedFlagAnalysisAgent,
    FindingsPersistenceAgent,
)