from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.core.config import get_settings


def test_liveness(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readiness_connects_to_postgres(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["database"] == "ok"
    assert body["migration_revision"]


def test_migrations_applied_to_head(db):
    head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    current = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert current == head


def test_expected_tables_exist(db):
    tables = set(inspect(db.get_bind()).get_table_names())
    assert {"users", "sessions", "partners", "cultural_traditions", "instructors", "movements",
            "movement_rubrics", "courses", "course_modules", "lessons", "lesson_materials",
            "enrollments", "lesson_progress", "audit_logs"} <= tables


def test_cors_allows_frontend_origin_only(client):
    origin = get_settings().cors_origin_list[0]
    ok = client.options(
        "/api/v1/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == origin
    bad = client.options(
        "/api/v1/health",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers
