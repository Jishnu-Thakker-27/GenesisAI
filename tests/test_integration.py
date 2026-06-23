import pytest
from fastapi.testclient import TestClient
import sqlite3
import os

from core.api import app
from core.pipeline import GenesisPipeline
from core.storage import ProjectStorage
from core.contracts import FinalCompiledApplication

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

def test_pipeline_orchestrator():
    pipeline = GenesisPipeline(execution_mode="BALANCED")
    app_res = pipeline.run_pipeline("Build a gym management system")
    assert isinstance(app_res, FinalCompiledApplication)
    assert app_res.app_type == "Gym Management"
    assert len(app_res.pipeline_traces) > 0
    assert app_res.validation_report.is_valid is True
    assert app_res.simulation_report.success_rate > 0.0

def test_compile_endpoint():
    response = client.post("/compile", json={"prompt": "Build a gym management system"})
    assert response.status_code == 200
    data = response.json()
    assert data["prompt"] == "Build a gym management system"
    assert data["app_type"] == "Gym Management"
    assert len(data["pipeline_traces"]) > 0

def test_dashboard_endpoint():
    client.post("/compile", json={"prompt": "Build a gym management system"})
    
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["pipeline_statistics"]["total_projects"] == 1
    assert data["success_rate"] == 100.0
    assert len(data["recent_projects"]) == 1

def test_architecture_endpoint():
    res = client.post("/compile", json={"prompt": "Build a gym management system"})
    project_id = res.json()["project_id"]
    
    response = client.get(f"/architecture/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
    assert len(data["entity_relationships"]) > 0

def test_simulation_endpoint():
    res = client.post("/compile", json={"prompt": "Build a gym management system"})
    project_id = res.json()["project_id"]
    
    response = client.post("/simulate", json={"project_id": project_id})
    assert response.status_code == 200
    data = response.json()
    assert data["success_rate"] > 0.0
    assert len(data["simulation_traces"]) > 0

def test_evolution_endpoint():
    res = client.post("/compile", json={"prompt": "Build a gym management system"})
    project_id = res.json()["project_id"]
    
    response = client.get(f"/versions/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["versions"]) >= 2  # v1.0 and evolved v1.1
    assert len(data["evolution_timeline"]) >= 2

def test_demo_mode_gym():
    response = client.post("/demo/compile", json={"prompt": "Build a gym management system"})
    assert response.status_code == 200
    data = response.json()
    assert "gym" in data["app_type"].lower()
    assert data["evolution_summary"] is not None
    assert data["evolution_summary"]["updated_bundle"] is not None

def test_demo_mode_hospital():
    response = client.post("/demo/compile", json={"prompt": "Compile a hospital app"})
    assert response.status_code == 200
    data = response.json()
    assert "hospital" in data["app_type"].lower() or "health" in data["app_type"].lower()
    assert data["evolution_summary"] is not None

def test_demo_mode_crm():
    response = client.post("/demo/compile", json={"prompt": "Create a CRM system"})
    assert response.status_code == 200
    data = response.json()
    assert "crm" in data["app_type"].lower()
    assert data["evolution_summary"] is not None

def test_demo_mode_school():
    response = client.post("/demo/compile", json={"prompt": "Build a school database"})
    assert response.status_code == 200
    data = response.json()
    assert "school" in data["app_type"].lower()
    assert data["evolution_summary"] is not None

def test_demo_mode_inventory():
    response = client.post("/demo/compile", json={"prompt": "Generate an inventory system"})
    assert response.status_code == 200
    data = response.json()
    assert "inventory" in data["app_type"].lower()
    assert data["evolution_summary"] is not None
