// GenesisAI Frontend TypeScript Models

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface PipelineTrace {
  phase_name: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  status: string;
  errors: string[];
  warnings: string[];
}

export interface DashboardMetrics {
  total_projects: number;
  successful_compilations: number;
  failed_compilations: number;
  validation_pass_rate: number;
  repair_success_rate: number;
  simulation_pass_rate: number;
  average_latency: number;
  total_versions_created: number;
}

export interface FinalCompiledApplication {
  project_id: string;
  app_name: string;
  app_type: string;
  prompt: string;
  intent: any; // IntentExtractionResult
  blueprint: any; // ApprovedBlueprint
  system_design: any; // MasterSpecification
  schema_bundle: any; // CompiledSchemaBundle
  validation_report: ValidationReport;
  repair_report: RepairReport | null;
  simulation_report: ExecutionSimulationReport;
  evolution_summary: RequirementChangeReport | null;
  pipeline_traces: PipelineTrace[];
  execution_mode: string;
  created_at: string;
  updated_at: string;
}

export interface ValidationError {
  error_id: string;
  error_code: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  layer: "Database" | "API" | "UI" | "Auth" | "Workflow" | "Coverage" | "Graph" | "Traceability" | "Contract" | "Cross-Layer";
  component: string;
  message: string;
  source_component: string;
  repair_hint: string;
}

export interface ValidationReport {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  validated_components: string[];
  timestamp: string;
}

export interface RepairCandidate {
  candidate_id: string;
  error_id: string;
  repair_strategy: string;
  confidence: number;
  target_components: string[];
  estimated_impact: string;
  repair_type: "CREATE" | "UPDATE" | "DELETE" | "LINK" | "RENAME" | "REGENERATE_PARTIAL";
}

export interface RepairAction {
  action_id: string;
  candidate_id: string;
  action_description: string;
  affected_components: string[];
  before_state: string;
  after_state: string;
  success: boolean;
}

export interface RepairReport {
  repair_id: string;
  validation_errors_received: ValidationError[];
  repair_candidates_generated: RepairCandidate[];
  repair_actions_executed: RepairAction[];
  successful_repairs: RepairAction[];
  failed_repairs: RepairAction[];
  revalidation_results: ValidationReport;
  timestamp: string;
}

export interface SimulationTrace {
  timestamp: string;
  actor: string;
  action: string;
  outcome: "SUCCESS" | "FAILED";
  reason: string;
  affected_components: string[];
}

export interface StateTransitionRule {
  entity: string;
  from_state: string;
  to_state: string;
  allowed: boolean;
}

export interface ExecutionSimulationReport {
  simulation_id: string;
  workflows_executed: string[];
  successful_steps: number;
  failed_steps: number;
  permission_failures: number;
  contract_failures: number;
  validation_failures: number;
  repair_failures: number;
  business_rule_failures: number;
  success_rate: number;
  simulation_traces: SimulationTrace[];
}

export interface RequirementVersion {
  version_id: string;
  parent_version: string | null;
  created_at: string;
  change_summary: string;
}

export interface ChangeDiff {
  component: string;
  before_state: string | null;
  after_state: string | null;
  change_reason: string;
}

export interface ChangeImpactScore {
  entities_changed: number;
  workflows_changed: number;
  apis_changed: number;
  permissions_changed: number;
  business_rules_changed: number;
  score: number;
  impact_level: "LOW" | "MEDIUM" | "HIGH";
}

export interface ChangeDependencyGraph {
  changed_component: string;
  directly_affected: string[];
  indirectly_affected: string[];
  dependency_depth: number;
  direct_dependencies: string[];
  indirect_dependencies: string[];
}

export interface ImpactAnalysisReport {
  affected_components: string[];
  unaffected_components: string[];
  estimated_effort: string;
  impact_score: ChangeImpactScore;
  dependency_graph: ChangeDependencyGraph;
}

export interface ChangeRiskAssessment {
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  affected_components: string[];
  affected_workflows: string[];
  affected_entities: string[];
  validation_risk: number;
  repair_risk: number;
  simulation_risk: number;
  overall_risk_score: number;
}

export interface ChangeEffectivenessReport {
  components_modified: string[];
  components_preserved: string[];
  validation_passed: boolean;
  repair_required: boolean;
  simulation_passed: boolean;
  rollback_required: boolean;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  impact_level: "LOW" | "MEDIUM" | "HIGH";
  complexity_level: "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
}

export interface ChangeConflict {
  conflict_id: string;
  conflict_type: "ENTITY_REMOVAL" | "WORKFLOW_DEPENDENCY" | "PERMISSION" | "BUSINESS_RULE";
  message: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface ConflictDetectionReport {
  is_valid: boolean;
  conflicts: ChangeConflict[];
}

export interface RequirementChangeReport {
  change_id: string;
  version_info: RequirementVersion;
  diffs: ChangeDiff[];
  impact_report: ImpactAnalysisReport;
  risk_assessment: ChangeRiskAssessment;
  effectiveness: ChangeEffectivenessReport;
  conflicts_report: ConflictDetectionReport;
  updated_blueprint: any;
  updated_spec: any;
  updated_bundle: any;
}

export interface EvolutionTimelineEntry {
  version_id: string;
  change_summary: string;
  impact_level: "LOW" | "MEDIUM" | "HIGH";
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  timestamp: string;
  parent_version?: string | null;
  change_id?: string;
  change_type?: string;
  description?: string;
}

// Architecture Screen Canvas Types
export interface ArchitectureNode {
  id: string;
  label: string;
  type: "Actor" | "API" | "DB" | "UI" | "Workflow" | string;
  properties?: Record<string, any>;
}

export interface ArchitectureEdge {
  id: string;
  source: string;
  target: string;
  type: string;
}

// Screen Backend Responses
export interface DashboardScreen {
  success_rate: number;
  validation_rate: number;
  repair_rate: number;
  simulation_rate: number;
  recent_projects: Record<string, any>[];
  pipeline_statistics: DashboardMetrics;
}

export interface CompilerScreen {
  prompt: string;
  intent: any;
  blueprint: any;
  system_design: any;
  schema_bundle: any;
  compiler_logs: string[];
}

export interface ValidationRepairScreen {
  validation_report: ValidationReport;
  validation_score: number;
  errors: ValidationError[];
  warnings: string[];
  repairs: Record<string, any>[];
  repair_history: Record<string, any>[];
}

export interface ArchitectureMapScreen {
  nodes: Record<string, any>[];
  edges: Record<string, any>[];
  entity_relationships: Record<string, any>[];
  workflow_relationships: Record<string, any>[];
  dependency_graph: Record<string, any>;
}

export interface ExecutionVerificationScreen {
  simulation_report: ExecutionSimulationReport;
  workflow_results: Record<string, any>[];
  permission_results: Record<string, any>[];
  execution_metrics: Record<string, any>;
}

export interface VersionHistoryEvolutionScreen {
  versions: RequirementVersion[];
  change_reports: RequirementChangeReport[];
  risk_assessments: ChangeRiskAssessment[];
  impact_analysis: ImpactAnalysisReport[];
  evolution_timeline: EvolutionTimelineEntry[];
}

// Screen Component States (with loading/error status)
export interface DashboardScreenState {
  data: DashboardScreen | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  errorMessage?: string;
}

export interface CompilerScreenState {
  data: CompilerScreen | null;
  pipelineTraces: PipelineTrace[];
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  errorMessage?: string;
}

export interface ValidationScreenState {
  data: ValidationRepairScreen | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  errorMessage?: string;
}

export interface RepairScreenState {
  data: RepairReport | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  errorMessage?: string;
}

export interface SimulationScreenState {
  data: ExecutionVerificationScreen | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  errorMessage?: string;
}

export interface TimelineScreenState {
  data: VersionHistoryEvolutionScreen | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  errorMessage?: string;
}
