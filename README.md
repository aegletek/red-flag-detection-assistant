# Red Flag Detection Assistant

Retrieves approved case data from Cosmos DB, uses an LLM to identify evidence-based red flags, and persists structured findings for human review.

This independently owned use case is powered by Orbit Core. Its validated
local flow is Cosmos DB -> LLM analysis -> PostgreSQL persistence, with
Langfuse tracing and sanitized workflow telemetry in the Admin Dashboard.

## Generated baseline

- Initializr schema: `1.0`
- Template: `standard-usecase@0.1.0`
- Orbit Core: `github@main`
- Workflow adapter: `langgraph`
- Python: `3.10`

- Generation mode: uploaded use-case manifest



## Manifest-derived architecture

Initializr preserved the reviewed manifest architecture rather than generating
the generic example workflow.

### Workflows


- `red_flag_detection` — starts at `retrieve_case_data`, uses
  `langgraph`, and is stored at
  `red_flag_detection_assistant/workflows/red_flag_detection.yaml`.


### Agents and assigned tools

| Capability | Generated class | Allowed tools |
|---|---|---|
| `case_data_retrieval` | `CaseDataRetrievalAgent` | `cosmos` |
| `red_flag_analysis` | `RedFlagAnalysisAgent` | None |
| `findings_persistence` | `FindingsPersistenceAgent` | `red_flag_repository` |


### Tool boundaries

| Tool | Source | Generated behavior |
|---|---|---|
| `cosmos` | `platform` | Referenced from Orbit Core; no duplicate implementation |
| `red_flag_repository` | `usecase` | PostgreSQL persistence in `tools.py` |


Agent stubs declare their allowed `tool_names`, but developers must implement
approved tool parameters and business behavior. Credentials belong in the
runtime environment or secret store, never in the manifest or source code.


## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python -m pytest
```


Run the workflow for an existing case:

```powershell
python -m red_flag_detection_assistant.cli --task CASE-1001
```


Run the API and open Swagger at `http://127.0.0.1:8040/docs`:

```powershell
python -m uvicorn red_flag_detection_assistant.api:create_app --factory --port 8040
```


Build with an approved Orbit Core runtime image whose Python version matches
`3.10`:

```powershell
docker build `
  --build-arg ORBIT_CORE_IMAGE=<approved-orbit-core-image-for-python-3.10> `
  -t red-flag-detection-assistant:local .
```

The platform team publishes or builds the compatible base image. Do not put a
registry credential in the image name, Dockerfile, or repository.


## Team implementation checklist


1. Implement the generated agent stubs without changing their declared capabilities.
2. Implement only the custom use-case tool stubs; reuse declared platform tools.
3. Review every generated agent-to-tool assignment for least privilege.
4. Confirm generated runtime workflows and `usecase-manifest.yaml` remain synchronized.
5. Add domain request/response models and tests.
6. Configure provider, guardrail, retention, and support policies.
7. Review `usecase-manifest.yaml` before Admin registration.
8. Keep all real credentials outside the repository.


## Documentation

- [Developer implementation guide](docs/developer-guide.md)
- [End-to-end onboarding runbook](https://github.com/aegletek/orbit-repo/blob/main/docs/demo/RED_FLAG_DETECTION_END_TO_END_RUNBOOK.md)
- Swagger: `http://127.0.0.1:8040/docs`
- Admin Dashboard: `http://127.0.0.1:8010/admin/`

The Admin Dashboard manifest publishes these links without exposing case data,
LLM prompts, findings, or credentials.
