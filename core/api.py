from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time

from core.pipeline import GenesisPipeline
from core.storage import ProjectStorage
from core.contracts import (
    DashboardScreen, CompilerScreen, ValidationRepairScreen,
    ArchitectureMapScreen, ExecutionVerificationScreen, VersionHistoryEvolutionScreen,
    FinalCompiledApplication, DashboardMetrics, PipelineTrace, AIArchitectScreen
)
from stages.stage6_validate import ValidationReport, ValidationError
from stages.stage7_repair import RepairReport
from stages.stage8_execution import ExecutionSimulationReport
from stages.stage9_change import RequirementChangeReport, RequirementVersion, ChangeRiskAssessment, ImpactAnalysisReport, EvolutionTimelineEntry

app = FastAPI(title="GenesisAI Developer Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "GenesisAI Developer Portal API"}

class CompileRequest(BaseModel):
    prompt: str
    execution_mode: Optional[str] = "BALANCED"
    intelligence_mode: Optional[str] = "HYBRID"

class ValidateRequest(BaseModel):
    project_id: str

class RepairRequest(BaseModel):
    project_id: str

class SimulateRequest(BaseModel):
    project_id: str

@app.post("/compile", response_model=FinalCompiledApplication)
def compile_project(request: CompileRequest):
    pipeline = GenesisPipeline(
        execution_mode=request.execution_mode,
        intelligence_mode=request.intelligence_mode
    )
    try:
        app_res = pipeline.run_pipeline(request.prompt)
        ProjectStorage.save_project(
            project_id=app_res.project_id,
            prompt=request.prompt,
            pipeline_results=app_res.model_dump(),
            latency=pipeline.execution_time * 1000.0,
            execution_mode=app_res.execution_mode
        )
        return app_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/demo/compile", response_model=FinalCompiledApplication)
def demo_compile(request: CompileRequest):
    return compile_project(request)

@app.post("/validate", response_model=ValidationReport)
def validate_project(request: ValidateRequest):
    proj = ProjectStorage.get_project(request.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    results = FinalCompiledApplication(**proj["pipeline_results"])
    return results.validation_report

@app.post("/repair", response_model=RepairReport)
def repair_project(request: RepairRequest):
    proj = ProjectStorage.get_project(request.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    results = FinalCompiledApplication(**proj["pipeline_results"])
    if not results.repair_report:
        return RepairReport(
            repair_id=f"rep_mock_{request.project_id}",
            validation_errors_received=[],
            repair_candidates_generated=[],
            repair_actions_executed=[],
            successful_repairs=[],
            failed_repairs=[],
            revalidation_results=ValidationReport(is_valid=True, errors=[], warnings=[], execution_time=0.0),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
    return results.repair_report

@app.post("/simulate", response_model=ExecutionSimulationReport)
def simulate_project(request: SimulateRequest):
    proj = ProjectStorage.get_project(request.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    results = FinalCompiledApplication(**proj["pipeline_results"])
    return results.simulation_report

@app.get("/dashboard", response_model=DashboardScreen)
def get_dashboard():
    projects = ProjectStorage.get_all_projects()
    if not projects:
        return DashboardScreen(
            success_rate=0.0,
            validation_rate=0.0,
            repair_rate=0.0,
            simulation_rate=0.0,
            recent_projects=[],
            pipeline_statistics=DashboardMetrics()
        )
        
    total = len(projects)
    valid_count = 0
    repaired_count = 0
    sim_sum = 0.0
    lat_sum = 0.0
    total_versions = 0
    recent = []
    
    for p in projects:
        res = FinalCompiledApplication(**p["pipeline_results"])
        if res.validation_report.is_valid:
            valid_count += 1
        if res.repair_report:
            repaired_count += 1
        sim_sum += res.simulation_report.success_rate
        lat_sum += p["latency"]
        total_versions += 2 if res.evolution_summary else 1
        
        recent.append({
            "project_id": p["project_id"],
            "prompt": p["prompt"],
            "final_status": "SUCCESS" if res.validation_report.is_valid or (res.repair_report and res.repair_report.revalidation_results.is_valid) else "FAILED",
            "created_at": p["created_at"],
            "updated_at": p["updated_at"]
        })
        
    avg_latency = round(lat_sum / total, 2)
    val_rate = round(valid_count / total * 100.0, 2)
    rep_rate = round(repaired_count / total * 100.0, 2)
    sim_rate = round(sim_sum / total, 2)
    
    metrics = DashboardMetrics(
        total_projects=total,
        successful_compilations=valid_count + repaired_count,
        failed_compilations=total - (valid_count + repaired_count),
        validation_pass_rate=val_rate,
        repair_success_rate=rep_rate,
        simulation_pass_rate=sim_rate,
        average_latency=avg_latency,
        total_versions_created=total_versions
    )
    
    return DashboardScreen(
        success_rate=round((valid_count + repaired_count) / total * 100.0, 2),
        validation_rate=val_rate,
        repair_rate=rep_rate,
        simulation_rate=sim_rate,
        recent_projects=recent[:5],
        pipeline_statistics=metrics
    )

@app.get("/architecture/{project_id}", response_model=ArchitectureMapScreen)
def get_architecture(project_id: str):
    proj = ProjectStorage.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    res = FinalCompiledApplication(**proj["pipeline_results"])
    spec = res.system_design
    
    entity_relationships = []
    for rel in spec.relationships:
        entity_relationships.append({
            "relationship_id": rel.relationship_id,
            "source": rel.source_entity,
            "target": rel.target_entity,
            "type": rel.relationship_type,
            "description": rel.description
        })
        
    workflow_relationships = []
    for wf in spec.workflows:
        workflow_relationships.append({
            "workflow_id": wf.workflow_id,
            "name": wf.workflow_name,
            "steps": wf.workflow_steps,
            "actors": wf.actors,
            "dependencies": wf.dependencies
        })
        
    dependency_graph = {}
    if res.evolution_summary:
        dg = res.evolution_summary.impact_report.dependency_graph
        dependency_graph = {
            "changed_component": dg.changed_component,
            "directly_affected": dg.directly_affected,
            "indirectly_affected": dg.indirectly_affected,
            "dependency_depth": dg.dependency_depth
        }
        
    return ArchitectureMapScreen(
        nodes=spec.graph.nodes,
        edges=spec.graph.edges,
        entity_relationships=entity_relationships,
        workflow_relationships=workflow_relationships,
        dependency_graph=dependency_graph
    )

@app.get("/ai-architect/{project_id}", response_model=AIArchitectScreen)
def get_ai_architect_report(project_id: str):
    proj = ProjectStorage.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    res = FinalCompiledApplication(**proj["pipeline_results"])
    return AIArchitectScreen(report=res.ai_architect_report)

@app.get("/versions/{project_id}", response_model=VersionHistoryEvolutionScreen)
def get_versions(project_id: str):
    proj = ProjectStorage.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    res = FinalCompiledApplication(**proj["pipeline_results"])
    
    versions = []
    change_reports = []
    risk_assessments = []
    impact_analysis = []
    evolution_timeline = []
    
    baseline_version = RequirementVersion(
        version_id="v1.0",
        parent_version=None,
        created_at=proj["created_at"],
        change_summary="Initial system specification compilation"
    )
    versions.append(baseline_version)
    
    evolution_timeline.append(EvolutionTimelineEntry(
        version_id="v1.0",
        change_summary="Initial system specification compilation",
        impact_level="LOW",
        risk_level="LOW",
        timestamp=proj["created_at"]
    ))
    
    if res.evolution_summary:
        evo = res.evolution_summary
        versions.append(evo.version_info)
        change_reports.append(evo)
        risk_assessments.append(evo.risk_assessment)
        impact_analysis.append(evo.impact_report)
        
        evolution_timeline.append(EvolutionTimelineEntry(
            version_id=evo.version_info.version_id,
            change_summary=evo.version_info.change_summary,
            impact_level=evo.effectiveness.impact_level,
            risk_level=evo.effectiveness.risk_level,
            timestamp=evo.version_info.created_at
        ))
        
    return VersionHistoryEvolutionScreen(
        versions=versions,
        change_reports=change_reports,
        risk_assessments=risk_assessments,
        impact_analysis=impact_analysis,
        evolution_timeline=evolution_timeline
    )

@app.get("/project/{project_id}", response_model=FinalCompiledApplication)
def get_project_details(project_id: str):
    proj = ProjectStorage.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return FinalCompiledApplication(**proj["pipeline_results"])
