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

def prune_dict_recursive(data: Any) -> Any:
    if isinstance(data, dict):
        new_dict = {}
        is_val_report = "validated_components" in data
        is_spec_or_bp = "app_type" in data
        for k, v in data.items():
            pruned_val = prune_dict_recursive(v)
            
            protected_keys = {
                "actors", "entities", "relationships", "workflows", 
                "business_rules", "design_decisions", "app_name", "app_type", "prompt", 
                "project_id", "created_at", "updated_at", "schema_bundle", 
                "validation_report", "simulation_report", "intent", "blueprint", 
                "system_design", "is_valid"
            }
            
            if k == "missing_information" and isinstance(pruned_val, list):
                new_list = []
                for item in pruned_val:
                    if isinstance(item, dict):
                        item_copy = dict(item)
                        if "impact" in item_copy and "severity" not in item_copy:
                            item_copy["severity"] = item_copy["impact"]
                        elif "severity" in item_copy and "impact" not in item_copy:
                            item_copy["impact"] = item_copy["severity"]
                        new_list.append(item_copy)
                    else:
                        new_list.append(item)
                pruned_val = new_list

            is_protected = (
                k in protected_keys 
                or (is_val_report and k in ("errors", "warnings"))
                or (is_spec_or_bp and k == "permissions")
            )
            
            if is_protected:
                if pruned_val is None:
                    if k in ("actors", "entities", "relationships", "workflows", "permissions", "business_rules", "design_decisions", "errors", "warnings"):
                        pruned_val = []
                    elif k in ("schema_bundle", "validation_report", "simulation_report", "intent", "blueprint", "system_design"):
                        pruned_val = {}
                new_dict[k] = pruned_val
            else:
                if pruned_val not in (None, [], {}):
                    new_dict[k] = pruned_val
        return new_dict
    elif isinstance(data, list):
        new_list = []
        for item in data:
            pruned_item = prune_dict_recursive(item)
            if pruned_item not in (None, [], {}):
                new_list.append(pruned_item)
            elif isinstance(item, (str, int, float, bool)):
                new_list.append(pruned_item)
        return new_list
    else:
        return data

@app.post("/compile")
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
        return prune_dict_recursive(app_res.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/demo/compile")
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

@app.get("/ai-architect/{project_id}")
def get_ai_architect_report(project_id: str):
    proj = ProjectStorage.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    res = FinalCompiledApplication(**proj["pipeline_results"])
    return {"report": prune_dict_recursive(res.ai_architect_report.model_dump())}

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

@app.get("/project/{project_id}")
def get_project_details(project_id: str):
    proj = ProjectStorage.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return prune_dict_recursive(proj["pipeline_results"])

@app.on_event("startup")
def seed_default_project():
    try:
        ProjectStorage.init_db()
        if not ProjectStorage.get_project("proj_01"):
            print("Seeding default project 'proj_01' in SQLite database...")
            pipeline = GenesisPipeline(execution_mode="BALANCED", intelligence_mode="HYBRID")
            app_res = pipeline.run_pipeline("Build a gym management system")
            app_res.project_id = "proj_01"
            ProjectStorage.save_project(
                project_id="proj_01",
                prompt="Build a gym management system",
                pipeline_results=app_res.model_dump(),
                latency=pipeline.execution_time * 1000.0,
                execution_mode=app_res.execution_mode
            )
            print("Successfully seeded initial project 'proj_01'.")
    except Exception as e:
        print(f"Error seeding default project 'proj_01': {e}")
