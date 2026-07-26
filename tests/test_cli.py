import asyncio
from types import SimpleNamespace

from red_flag_detection_assistant import cli


class FakeRuntime:
    async def execute(self, request):
        assert request.input == "CASE-1001"
        return SimpleNamespace(
            success=True,
            output='{"status":"persisted","case_id":"CASE-1001"}',
            error=None,
        )


def test_cli_runner_executes_workflow(monkeypatch) -> None:
    fake_application = SimpleNamespace(runtime=FakeRuntime())

    monkeypatch.setattr(
        cli,
        "build_application",
        lambda: fake_application,
    )

    output = asyncio.run(cli.run("CASE-1001"))

    assert '"case_id":"CASE-1001"' in output