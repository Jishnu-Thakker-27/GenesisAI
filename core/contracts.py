from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from stages.stage2_intent import IntentExtractionResult
from stages.stage3_recommend import ApprovedBlueprint
from stages.stage4_system import MasterSpecification
from stages.stage5_schema import CompiledSchemaBundle
from stages.stage6_validate import ValidationReport, ValidationError
from stages.stage7_repair import RepairReport
from stages.stage8_execution import ExecutionSimulationReport
from stages.stage9_change import RequirementChangeReport, RequirementVersion, ChangeRiskAssessment, ImpactAnalysisReport, EvolutionTimelineEntry
from stages.stage10_requirements_intelligence import AIArchitectReport

class PipelineTrace(BaseModel):
    phase_name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class DashboardMetrics(BaseModel):
    total_projects: int = 0
    successful_compilations: int = 0
    failed_compilations: int = 0
    validation_pass_rate: float = 0.0
    repair_success_rate: float = 0.0
    simulation_pass_rate: float = 0.0
    average_latency: float = 0.0
    total_versions_created: int = 0

class FinalCompiledApplication(BaseModel):
    project_id: str
    app_name: str
    app_type: str
    prompt: str
    intent: IntentExtractionResult
    ai_architect_report: AIArchitectReport
    blueprint: ApprovedBlueprint
    system_design: MasterSpecification
    schema_bundle: CompiledSchemaBundle
    validation_report: ValidationReport
    repair_report: Optional[RepairReport] = None
    simulation_report: ExecutionSimulationReport
    evolution_summary: Optional[RequirementChangeReport] = None
    pipeline_traces: List[PipelineTrace] = Field(default_factory=list)
    execution_mode: str = "BALANCED"
    created_at: str
    updated_at: str

class DashboardScreen(BaseModel):
    success_rate: float
    validation_rate: float
    repair_rate: float
    simulation_rate: float
    recent_projects: List[Dict[str, Any]] = Field(default_factory=list)
    pipeline_statistics: DashboardMetrics

class CompilerScreen(BaseModel):
    prompt: str
    intent: IntentExtractionResult
    blueprint: ApprovedBlueprint
    system_design: MasterSpecification
    schema_bundle: CompiledSchemaBundle
    compiler_logs: List[str] = Field(default_factory=list)

class AIArchitectScreen(BaseModel):
    report: AIArchitectReport

class ValidationRepairScreen(BaseModel):
    validation_report: ValidationReport
    validation_score: float
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    repairs: List[Dict[str, Any]] = Field(default_factory=list)
    repair_history: List[Dict[str, Any]] = Field(default_factory=list)

class ArchitectureMapScreen(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    entity_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_graph: Dict[str, Any] = Field(default_factory=dict)

class ExecutionVerificationScreen(BaseModel):
    simulation_report: ExecutionSimulationReport
    workflow_results: List[Dict[str, Any]] = Field(default_factory=list)
    permission_results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_metrics: Dict[str, Any] = Field(default_factory=dict)

class VersionHistoryEvolutionScreen(BaseModel):
    versions: List[RequirementVersion] = Field(default_factory=list)
    change_reports: List[RequirementChangeReport] = Field(default_factory=list)
    risk_assessments: List[ChangeRiskAssessment] = Field(default_factory=list)
    impact_analysis: List[ImpactAnalysisReport] = Field(default_factory=list)
    evolution_timeline: List[EvolutionTimelineEntry] = Field(default_factory=list)
