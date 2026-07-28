from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    desc,
    func,
    insert,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.sql import func

from .domain import RedFlagAnalysis


class UseCaseRepository:
    """Application-owned persistence for validated red-flag findings."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
    ) -> None:
        if engine is None and not database_url:
            raise ValueError("DATABASE_URL is required")

        self.engine = engine or create_engine(
            database_url,
            pool_pre_ping=True,
        )
        self.metadata = MetaData()

        self.findings = Table(
            "red_flag_findings",
            self.metadata,
            Column("finding_id", String(64), primary_key=True),
            Column("case_id", String(64), nullable=False),
            Column("overall_risk", String(20), nullable=False),
            Column("analysis_summary", Text, nullable=False),
            Column("red_flags", JSONB, nullable=False),
            Column(
                "requires_human_review",
                Boolean,
                nullable=False,
                default=True,
            ),
            Column("model_name", String(200)),
            Column("workflow_id", String(64)),
            Column("request_id", String(64)),
            Column(
                "created_at",
                DateTime(timezone=True),
                nullable=False,
                server_default=func.now(),
            ),
        )

        Index(
            "ix_red_flag_findings_case_id",
            self.findings.c.case_id,
        )

    def create_schema(self) -> None:
        self.metadata.create_all(self.engine)

    def save(
        self,
        analysis: RedFlagAnalysis,
        *,
        model_name: str | None,
        workflow_id: str | None,
        request_id: str | None,
    ) -> str:
        finding_id = str(uuid4())

        statement = insert(self.findings).values(
            finding_id=finding_id,
            case_id=analysis.case_id,
            overall_risk=analysis.overall_risk,
            analysis_summary=analysis.analysis_summary,
            red_flags=[
                item.model_dump(mode="json")
                for item in analysis.red_flags
            ],
            requires_human_review=analysis.requires_human_review,
            model_name=model_name,
            workflow_id=workflow_id,
            request_id=request_id,
        )

        with self.engine.begin() as connection:
            connection.execute(statement)

        return finding_id

    def list_findings(self, *, search: str, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = []
        if search:
            pattern = f"%{search.lower()}%"
            filters.append(or_(func.lower(self.findings.c.case_id).like(pattern), func.lower(self.findings.c.overall_risk).like(pattern), func.lower(self.findings.c.workflow_id).like(pattern)))
        query, count = select(self.findings).order_by(desc(self.findings.c.created_at)), select(func.count()).select_from(self.findings)
        if filters: query, count = query.where(*filters), count.where(*filters)
        with self.engine.connect() as connection:
            total = int(connection.execute(count).scalar_one())
            rows = connection.execute(query.offset((page - 1) * page_size).limit(page_size)).mappings().all()
        return [dict(row) for row in rows], total

    def trend(self, *, days: int = 14) -> list[dict]:
        with self.engine.connect() as connection: dates = connection.execute(select(self.findings.c.created_at)).scalars().all()
        counts: dict[str, int] = {}
        for value in dates:
            key = value.date().isoformat(); counts[key] = counts.get(key, 0) + 1
        return [{"date": key, "runs": value} for key, value in sorted(counts.items())[-days:]]
