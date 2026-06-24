from fastapi.testclient import TestClient
import pytest
import sqlite3

from core.api import app
from core.pipeline import GenesisPipeline
from core.storage import ProjectStorage
from stages.stage10_requirements_intelligence import RequirementsIntelligenceEngine
from stages.stage2_intent import IntentExtractionEngine

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    ProjectStorage.init_db()
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM demo_projects;")
    conn.commit()
    conn.close()


def test_requirements_intelligence_detects_hospital_ambiguity():
    intent = IntentExtractionEngine(api_key="").extract_intent("Build a hospital management system")
    report = RequirementsIntelligenceEngine.analyze(
        "Build a hospital management system",
        intent,
        "HYBRID"
    )

    assert report.ambiguity_score > 0.0
    assert any(item.category == "integrations" for item in report.missing_information)
    assert any("billing" in item.description.lower() for item in report.missing_information)
    assert any(question.priority == "HIGH" for question in report.clarification_questions)


def test_requirements_intelligence_modes_filter_questions_and_assumptions():
    intent = IntentExtractionEngine(api_key="").extract_intent("Build a hospital management system")

    ask_only = RequirementsIntelligenceEngine.analyze("Build a hospital management system", intent, "ASK_ONLY")
    assume_only = RequirementsIntelligenceEngine.analyze("Build a hospital management system", intent, "ASSUME_ONLY")

    assert ask_only.assumptions_made == []
    assert len(ask_only.clarification_questions) > 0
    assert assume_only.clarification_questions == []
    assert len(assume_only.assumptions_made) > 0


def test_pipeline_includes_ai_architect_report_and_reasoning_trace():
    pipeline = GenesisPipeline(execution_mode="BALANCED", intelligence_mode="HYBRID")
    app_res = pipeline.run_pipeline("Build a hospital management system")

    assert app_res.ai_architect_report is not None
    assert app_res.ai_architect_report.mode == "HYBRID"
    assert len(app_res.ai_architect_report.architecture_reasoning_trace) > 0
    assert any(
        trace.component_type == "Entity"
        for trace in app_res.ai_architect_report.architecture_reasoning_trace
    )
    assert any(
        trace.phase_name == "AI Requirements Intelligence Engine"
        for trace in app_res.pipeline_traces
    )


def test_ai_architect_endpoint_returns_report():
    response = client.post("/compile", json={
        "prompt": "Build a hospital management system",
        "intelligence_mode": "HYBRID"
    })
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    report_response = client.get(f"/ai-architect/{project_id}")

    assert report_response.status_code == 200
    data = report_response.json()
    assert data["report"]["mode"] == "HYBRID"
    assert data["report"]["confidence_scores"]["overall_score"] > 0
