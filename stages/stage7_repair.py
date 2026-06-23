import logging
import re
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any, Tuple
from enum import Enum

from core.naming import CanonicalNamingEngine
from stages.stage4_system import MasterSpecification, EntityDefinition, WorkflowDefinition, PermissionDefinition, RelationshipDefinition, Actor
from stages.stage5_schema import (
    CompiledSchemaBundle, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, TraceabilityMetadata,
    CompilationArtifact, ColumnDefinition, UIComponent
)
from stages.stage6_validate import ValidationEngine, ValidationError, ValidationReport
from stages.stage3_recommend import ApprovedBlueprint

logger = logging.getLogger(__name__)

# --- PHASE 7 DATA MODELS ---

class RepairType(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LINK = "LINK"
    RENAME = "RENAME"
    REGENERATE_PARTIAL = "REGENERATE_PARTIAL"


class RepairStrategy(BaseModel):
    strategy_id: str
    error_type: str
    repair_steps: List[str]
    expected_result: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class RepairCandidate(BaseModel):
    candidate_id: str
    error_id: str
    repair_strategy: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    target_components: List[str] = Field(default_factory=list)
    estimated_impact: str
    repair_type: RepairType


class RepairAction(BaseModel):
    action_id: str
    candidate_id: str
    action_description: str
    affected_components: List[str] = Field(default_factory=list)
    before_state: str
    after_state: str
    success: bool


class ImpactAnalysis(BaseModel):
    source_error: ValidationError
    affected_components: List[str] = Field(default_factory=list)
    unaffected_components: List[str] = Field(default_factory=list)
    repair_scope: str


class RepairEffectivenessMetrics(BaseModel):
    before_error_count: int
    after_error_count: int
    reduction_percentage: float
    successful_repairs: int
    failed_repairs: int


class RepairHistoryEntry(BaseModel):
    error_id: str
    repair_strategy: str
    success: bool
    before_validation: ValidationError
    after_validation: Optional[ValidationError] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class RepairReport(BaseModel):
    repair_id: str
    validation_errors_received: List[ValidationError] = Field(default_factory=list)
    repair_candidates_generated: List[RepairCandidate] = Field(default_factory=list)
    repair_actions_executed: List[RepairAction] = Field(default_factory=list)
    successful_repairs: List[RepairAction] = Field(default_factory=list)
    failed_repairs: List[RepairAction] = Field(default_factory=list)
    revalidation_results: ValidationReport
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- STRATEGY LIBRARY ---

class RepairStrategyLibrary:
    STRATEGIES = {
        "DB_MISSING_PK": RepairStrategy(
            strategy_id="strat_db_pk",
            error_type="DB_MISSING_PK",
            repair_steps=["Identify target database table", "Create new primary key column 'id' of type 'string'", "Append column and list as primary key"],
            expected_result="Table contains valid primary key",
            confidence=0.98
        ),
        "DB_BROKEN_RELATIONSHIP": RepairStrategy(
            strategy_id="strat_db_fk_rel",
            error_type="DB_BROKEN_RELATIONSHIP",
            repair_steps=["Identify missing relationship target table", "Add new foreign key column", "Register foreign key constraint"],
            expected_result="Database schema preserves logical relationship",
            confidence=0.95
        ),
        "DB_DUPLICATE_TABLE": RepairStrategy(
            strategy_id="strat_db_dup",
            error_type="DB_DUPLICATE_TABLE",
            repair_steps=["Identify duplicate table name in database schema", "Retain the first compiled table definition", "Filter out subsequent duplicates"],
            expected_result="No duplicate tables in database schema",
            confidence=1.0
        ),
        "API_DUPLICATE_ENDPOINT": RepairStrategy(
            strategy_id="strat_api_dup",
            error_type="API_DUPLICATE_ENDPOINT",
            repair_steps=["Identify duplicate API endpoint path/method", "Filter out duplicates, keeping first definition"],
            expected_result="API routes are unique",
            confidence=1.0
        ),
        "API_UNKNOWN_ENTITY": RepairStrategy(
            strategy_id="strat_api_unk_ent",
            error_type="API_UNKNOWN_ENTITY",
            repair_steps=["Identify API endpoint with unknown source entity", "Map the endpoint's source_entity to a valid default entity from spec"],
            expected_result="API endpoint references a valid entity",
            confidence=0.9
        ),
        "API_INVALID_ROLE": RepairStrategy(
            strategy_id="strat_api_inv_role",
            error_type="API_INVALID_ROLE",
            repair_steps=["Identify endpoint permissions containing undefined roles", "Filter the permissions list to keep only defined AST actors or Admin"],
            expected_result="API endpoint permissions match defined actors",
            confidence=0.95
        ),
        "UI_DUPLICATE_VIEW": RepairStrategy(
            strategy_id="strat_ui_dup",
            error_type="UI_DUPLICATE_VIEW",
            repair_steps=["Identify duplicate UI view slug", "Filter out duplicates, keeping first definition"],
            expected_result="UI view slugs are unique",
            confidence=1.0
        ),
        "UI_BROKEN_ENDPOINT": RepairStrategy(
            strategy_id="strat_ui_broken_ep",
            error_type="UI_BROKEN_ENDPOINT",
            repair_steps=["Identify broken endpoint route linked in UI view", "Parse method and path, generate a new APIEndpointDefinition", "Add the compiled endpoint to API schema"],
            expected_result="UI views link to valid REST endpoints",
            confidence=0.92
        ),
        "UI_INVALID_ROLE": RepairStrategy(
            strategy_id="strat_ui_inv_role",
            error_type="UI_INVALID_ROLE",
            repair_steps=["Identify view required permissions containing undefined roles", "Filter required permissions list to defined AST actors"],
            expected_result="UI view access rights match defined actors",
            confidence=0.95
        ),
        "AUTH_DUPLICATE_ROLE": RepairStrategy(
            strategy_id="strat_auth_dup",
            error_type="AUTH_DUPLICATE_ROLE",
            repair_steps=["Identify duplicate Auth rule role", "Filter out duplicates, keeping first rule definition"],
            expected_result="Auth rules list contains unique roles",
            confidence=1.0
        ),
        "AUTH_INVALID_ROLE": RepairStrategy(
            strategy_id="strat_auth_inv_role",
            error_type="AUTH_INVALID_ROLE",
            repair_steps=["Identify Auth rule defined for undefined role", "Discard the invalid Auth rule"],
            expected_result="Auth rule role matches defined actor",
            confidence=1.0
        ),
        "WORKFLOW_MISSING_ACTOR": RepairStrategy(
            strategy_id="strat_wf_miss_actor",
            error_type="WORKFLOW_MISSING_ACTOR",
            repair_steps=["Identify missing actor referenced in workflow", "Generate a new default Actor definition in spec actors list"],
            expected_result="Workflow references exist in spec actors",
            confidence=0.95
        ),
        "WORKFLOW_CIRCULAR_DEP": RepairStrategy(
            strategy_id="strat_wf_circ",
            error_type="WORKFLOW_CIRCULAR_DEP",
            repair_steps=["Identify circular dependency starting at workflow", "Clear the workflow_dependencies list for the affected workflows"],
            expected_result="Workflow dependency graph forms a DAG",
            confidence=0.98
        ),
        "TRACEABILITY_MISSING_ARTIFACT": RepairStrategy(
            strategy_id="strat_trace_miss_art",
            error_type="TRACEABILITY_MISSING_ARTIFACT",
            repair_steps=["Identify schema component missing a compilation artifact", "Construct and append a new CompilationArtifact referencing the component and AST source"],
            expected_result="Traceability artifacts are complete",
            confidence=0.99
        ),
        "CONTRACT_INVALID_REF": RepairStrategy(
            strategy_id="strat_contract_inv_ref",
            error_type="CONTRACT_INVALID_REF",
            repair_steps=["Identify broken component references inside contract generated_components", "Filter out non-existent target paths"],
            expected_result="Contracts map to valid physical schema components",
            confidence=0.98
        ),
        "REQUIRED_FIELD_MISMATCH": RepairStrategy(
            strategy_id="strat_req_field_mismatch",
            error_type="REQUIRED_FIELD_MISMATCH",
            repair_steps=["Identify database columns vs API schema parameters mismatch", "Regenerate/patch API request/response schema for affected component to align fields"],
            expected_result="API parameters match database columns requirements",
            confidence=0.93
        ),
        "WORKFLOW_MISSING_STEP": RepairStrategy(
            strategy_id="strat_wf_miss_step",
            error_type="WORKFLOW_MISSING_STEP",
            repair_steps=["Identify missing step in workflow definition flow", "Append the missing step (e.g. 'Verification Step' or default step) to workflow steps list"],
            expected_result="Workflow definition flow is complete with all required steps",
            confidence=0.9
        ),
        "COVERAGE_LOSS": RepairStrategy(
            strategy_id="strat_coverage_loss",
            error_type="COVERAGE_LOSS",
            repair_steps=["Identify approved blueprint feature missing in compiled schemas", "Surgically compile a placeholder schema table or endpoint representation for the missing feature"],
            expected_result="Blueprint features coverage is complete",
            confidence=0.88
        )
    }


# --- IMPACT ANALYZER ---

class ImpactAnalyzer:
    @staticmethod
    def analyze(error: ValidationError, bundle: CompiledSchemaBundle, spec: MasterSpecification) -> ImpactAnalysis:
        affected = []
        
        source = error.source_component
        comp = error.component
        
        affected.append(comp)
        if source:
            affected.append(source)
            
        for art in bundle.artifacts:
            if art.source_component == source:
                affected.append(art.generated_component)
                
        if spec.graph and source:
            source_id = source.split(":", 1)[1].lower() if ":" in source else source.lower()
            for edge in spec.graph.edges:
                src = edge["source"].lower()
                trg = edge["target"].lower()
                if src == source_id:
                    affected.append(f"Node:{edge['target']}")
                elif trg == source_id:
                    affected.append(f"Node:{edge['source']}")
                    
        affected = list(set(affected))
        
        all_comps = []
        for t in bundle.database_schema:
            all_comps.append(f"Table:{t.table_name}")
        for a in bundle.api_schema:
            all_comps.append(f"APIEndpoint:{a.endpoint_id}")
        for u in bundle.ui_schema:
            all_comps.append(f"UIView:{u.view_id}")
        for au in bundle.auth_schema:
            all_comps.append(f"AuthRule:{au.role}")
            
        unaffected = [c for c in all_comps if c not in affected]
        
        return ImpactAnalysis(
            source_error=error,
            affected_components=affected,
            unaffected_components=unaffected,
            repair_scope=f"Targeted repair on component '{comp}'"
        )


# --- REPAIR PLANNER ---

class RepairPlanner:
    @staticmethod
    def plan(error: ValidationError, err_index: int) -> Optional[RepairCandidate]:
        code = error.error_code
        strategy = RepairStrategyLibrary.STRATEGIES.get(code)
        if not strategy:
            strategy = RepairStrategy(
                strategy_id=f"strat_fallback_{code.lower()}",
                error_type=code,
                repair_steps=["Diagnose manual patch configuration"],
                expected_result="Errors resolved",
                confidence=0.5
            )
            
        rep_type = RepairType.REGENERATE_PARTIAL
        if "DUPLICATE" in code:
            rep_type = RepairType.DELETE
        elif "MISSING" in code or "BROKEN" in code or "COVERAGE" in code:
            rep_type = RepairType.CREATE
        elif "INVALID" in code or "MISMATCH" in code:
            rep_type = RepairType.UPDATE
            
        complexity_factor = 0.9 if "CIRCULAR" in code or "COVERAGE" in code or "MISMATCH" in code else 0.98
        confidence = strategy.confidence * complexity_factor

        return RepairCandidate(
            candidate_id=f"rep_cand_{err_index:03d}",
            error_id=error.error_id,
            repair_strategy=strategy.repair_steps[0],
            confidence=confidence,
            target_components=[error.component],
            estimated_impact=strategy.expected_result,
            repair_type=rep_type
        )


# --- REPAIR SAFETY ENGINE ---

class RepairSafetyEngine:
    @staticmethod
    def verify_safety(before_bundle: CompiledSchemaBundle, after_bundle: CompiledSchemaBundle, candidate: RepairCandidate) -> bool:
        target_set = set(candidate.target_components)
        
        # If DB is not in target_set, DB table names and column structures must remain unchanged
        db_in_target = any("Table:" in t or "Feature:" in t for t in target_set)
        if not db_in_target:
            tbls_before = {t.table_name: len(t.columns) for t in before_bundle.database_schema}
            tbls_after = {t.table_name: len(t.columns) for t in after_bundle.database_schema}
            if tbls_before != tbls_after:
                return False
                
        # If UI is not in target_set, UI view count and components must remain unchanged
        ui_in_target = any("UIView:" in t or "View:" in t for t in target_set)
        if not ui_in_target:
            views_before = {v.view_id for v in before_bundle.ui_schema}
            views_after = {v.view_id for v in after_bundle.ui_schema}
            if views_before != views_after:
                return False
                
        # If Auth is not in target_set, Auth rule roles must remain unchanged
        auth_in_target = any("AuthRule:" in t or "Role:" in t for t in target_set)
        if not auth_in_target:
            roles_before = {a.role for a in before_bundle.auth_schema}
            roles_after = {a.role for a in after_bundle.auth_schema}
            if roles_before != roles_after:
                return False
                
        return True


# --- TARGETED REPAIR ENGINE ---

class TargetedRepairEngine:
    @staticmethod
    def repair_component(
        bundle: CompiledSchemaBundle,
        spec: MasterSpecification,
        candidate: RepairCandidate,
        error: ValidationError
    ) -> Tuple[CompiledSchemaBundle, MasterSpecification, List[str]]:
        affected = []
        err_code = error.error_code

        if err_code == "DB_MISSING_PK":
            tbl_name = error.component.split(":", 1)[1]
            for tbl in bundle.database_schema:
                if tbl.table_name == tbl_name:
                    has_id = any(c.name == "id" for c in tbl.columns)
                    if not has_id:
                        tbl.columns.insert(0, ColumnDefinition(
                            name="id",
                            type="string",
                            is_nullable=False,
                            is_primary_key=True,
                            is_foreign_key=False
                        ))
                    if "id" not in tbl.primary_keys:
                        tbl.primary_keys.append("id")
                    affected.append(f"Table:{tbl_name}")
                    break

        elif err_code == "DB_BROKEN_RELATIONSHIP":
            tbl_name = error.component.split(":", 1)[1]
            rel_id = error.source_component.split(":", 1)[1]
            rel = next((r for r in spec.relationships if r.relationship_id == rel_id), None)
            if rel:
                trg_tbl = CanonicalNamingEngine.to_snake_case(rel.target_entity)
                fk_col = f"{trg_tbl}_id"
                for tbl in bundle.database_schema:
                    if tbl.table_name == tbl_name:
                        if not any(c.name == fk_col for c in tbl.columns):
                            tbl.columns.append(ColumnDefinition(
                                name=fk_col,
                                type="relationship",
                                is_nullable=True,
                                is_primary_key=False,
                                is_foreign_key=True,
                                references=f"{rel.target_entity}.id"
                            ))
                        if not any(fk.get("column") == fk_col for fk in tbl.foreign_keys):
                            tbl.foreign_keys.append({
                                "column": fk_col,
                                "references_table": trg_tbl,
                                "references_column": "id"
                            })
                        affected.append(f"Table:{tbl_name}")
                        break

        elif err_code == "DB_DUPLICATE_TABLE":
            tbl_name = error.component.split(":", 1)[1]
            seen = set()
            new_db_schema = []
            for t in bundle.database_schema:
                if t.table_name == tbl_name:
                    if tbl_name not in seen:
                        new_db_schema.append(t)
                        seen.add(tbl_name)
                else:
                    new_db_schema.append(t)
            bundle.database_schema = new_db_schema
            affected.append(f"Table:{tbl_name}")

        elif err_code == "API_DUPLICATE_ENDPOINT":
            ep_id = error.component.split(":", 1)[1]
            ep = next((a for a in bundle.api_schema if a.endpoint_id == ep_id), None)
            if ep:
                route_key = f"{ep.method} {ep.path}"
                seen = set()
                new_api = []
                for a in bundle.api_schema:
                    r_key = f"{a.method} {a.path}"
                    if r_key == route_key:
                        if route_key not in seen:
                            new_api.append(a)
                            seen.add(route_key)
                    else:
                        new_api.append(a)
                bundle.api_schema = new_api
                affected.append(f"APIEndpoint:{ep_id}")

        elif err_code == "API_UNKNOWN_ENTITY":
            ep_id = error.component.split(":", 1)[1]
            for ap in bundle.api_schema:
                if ap.endpoint_id == ep_id:
                    if spec.entities:
                        ap.source_entity = spec.entities[0].name
                    else:
                        ap.source_entity = "System"
                    affected.append(f"APIEndpoint:{ep_id}")
                    break

        elif err_code == "API_INVALID_ROLE":
            ep_id = error.component.split(":", 1)[1]
            actor_names = {a.name for a in spec.actors}
            for ap in bundle.api_schema:
                if ap.endpoint_id == ep_id:
                    ap.permissions = [p for p in ap.permissions if p == "Admin" or p in actor_names]
                    affected.append(f"APIEndpoint:{ep_id}")
                    break

        elif err_code == "UI_DUPLICATE_VIEW":
            view_id = error.component.split(":", 1)[1]
            seen = set()
            new_ui = []
            for u in bundle.ui_schema:
                if u.view_id == view_id:
                    if view_id not in seen:
                        new_ui.append(u)
                        seen.add(view_id)
                else:
                    new_ui.append(u)
            bundle.ui_schema = new_ui
            affected.append(f"UIView:{view_id}")

        elif err_code == "UI_BROKEN_ENDPOINT":
            view_id = error.component.split(":", 1)[1]
            route_str = ""
            for ui in bundle.ui_schema:
                if ui.view_id == view_id:
                    api_paths = {f"{a.method} {a.path}" for a in bundle.api_schema}
                    for link in ui.linked_endpoints:
                        if link not in api_paths:
                            matched = False
                            if " /" in link:
                                method, path = link.split(" ", 1)
                                for a in bundle.api_schema:
                                    if a.method == method:
                                        p1 = path.replace("{id}", "").rstrip("/")
                                        p2 = a.path.replace("{id}", "").rstrip("/")
                                        if p1 == p2:
                                            matched = True
                                            break
                            if not matched:
                                route_str = link
                                break
                    break
            
            if route_str and " /" in route_str:
                method, path = route_str.split(" ", 1)
                ep_id = f"execute_{CanonicalNamingEngine.to_snake_case(path.replace('/', '_').replace('{', '').replace('}', ''))}"
                new_ep = APIEndpointDefinition(
                    endpoint_id=ep_id,
                    path=path,
                    method=method,
                    request_schema={},
                    response_schema={"status": "string"},
                    permissions=["Admin"],
                    source_entity="System",
                    traceability=TraceabilityMetadata(
                        source_ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                        compiler_phase="Partial Regeneration Engine (UI Broken Route Repair)"
                    )
                )
                bundle.api_schema.append(new_ep)
                bundle.artifacts.append(CompilationArtifact(
                    artifact_id=f"art_api_{ep_id}",
                    artifact_type="api_endpoint",
                    source_component="Workflow:System",
                    generated_component=f"Endpoint:{ep_id}",
                    ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                    traceability=new_ep.traceability
                ))
                affected.append(f"APIEndpoint:{ep_id}")
                affected.append(f"UIView:{view_id}")

        elif err_code == "UI_INVALID_ROLE":
            view_id = error.component.split(":", 1)[1]
            actor_names = {a.name for a in spec.actors}
            for ui in bundle.ui_schema:
                if ui.view_id == view_id:
                    ui.required_permissions = [p for p in ui.required_permissions if p in actor_names]
                    affected.append(f"UIView:{view_id}")
                    break

        elif err_code == "AUTH_DUPLICATE_ROLE":
            role_name = error.component.split(":", 1)[1]
            seen = set()
            new_auth = []
            for au in bundle.auth_schema:
                if au.role == role_name:
                    if role_name not in seen:
                        new_auth.append(au)
                        seen.add(role_name)
                else:
                    new_auth.append(au)
            bundle.auth_schema = new_auth
            affected.append(f"AuthRule:{role_name}")

        elif err_code == "AUTH_INVALID_ROLE":
            role_name = error.component.split(":", 1)[1]
            bundle.auth_schema = [au for au in bundle.auth_schema if au.role != role_name]
            bundle.artifacts = [art for art in bundle.artifacts if art.generated_component != f"AuthRule:{role_name}"]
            affected.append(f"AuthRule:{role_name}")

        elif err_code == "WORKFLOW_MISSING_ACTOR":
            m = re.search(r"references non-existent actor '([^']+)'", error.message)
            actor_name = m.group(1) if m else "DefaultActor"
            if not any(a.name == actor_name for a in spec.actors):
                spec.actors.append(Actor(
                    name=actor_name,
                    description=f"Auto-generated repair for missing actor {actor_name}",
                    permissions=[]
                ))
            affected.append(f"Actor:{actor_name}")

        elif err_code == "WORKFLOW_CIRCULAR_DEP":
            wf_name = error.component.split(":", 1)[1]
            for wf in spec.workflows:
                if wf.workflow_name == wf_name:
                    wf.workflow_dependencies = []
                    affected.append(f"Workflow:{wf_name}")
                    break

        elif err_code == "TRACEABILITY_MISSING_ARTIFACT":
            comp_type, comp_name = error.component.split(":", 1)
            if comp_type == "Table":
                tbl = next((t for t in bundle.database_schema if t.table_name == comp_name), None)
                if tbl:
                    bundle.artifacts.append(CompilationArtifact(
                        artifact_id=f"art_db_{comp_name}",
                        artifact_type="database_table",
                        source_component=f"Entity:{tbl.source_entity}",
                        generated_component=f"Table:{comp_name}",
                        ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                        traceability=tbl.traceability
                    ))
                    affected.append(f"Table:{comp_name}")
            elif comp_type == "APIEndpoint":
                ap = next((a for a in bundle.api_schema if a.endpoint_id == comp_name), None)
                if ap:
                    source = f"Entity:{ap.source_entity}" if ap.traceability.source_entity else f"Workflow:{ap.traceability.source_workflow}"
                    bundle.artifacts.append(CompilationArtifact(
                        artifact_id=f"art_api_{comp_name}",
                        artifact_type="api_endpoint",
                        source_component=source,
                        generated_component=f"Endpoint:{comp_name}",
                        ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                        traceability=ap.traceability
                    ))
                    affected.append(f"APIEndpoint:{comp_name}")
            elif comp_type == "UIView":
                ui = next((u for u in bundle.ui_schema if u.view_id == comp_name), None)
                if ui:
                    bundle.artifacts.append(CompilationArtifact(
                        artifact_id=f"art_ui_{comp_name}",
                        artifact_type="ui_view",
                        source_component=f"Workflow:{ui.source_workflow}",
                        generated_component=f"View:{comp_name}",
                        ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                        traceability=ui.traceability
                    ))
                    affected.append(f"UIView:{comp_name}")
            elif comp_type == "AuthRule":
                au = next((a for a in bundle.auth_schema if a.role == comp_name), None)
                if au:
                    bundle.artifacts.append(CompilationArtifact(
                        artifact_id=f"art_auth_{comp_name.lower()}",
                        artifact_type="auth_rule",
                        source_component=f"Actor:{comp_name}",
                        generated_component=f"AuthRule:{comp_name}",
                        ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                        traceability=au.traceability
                    ))
                    affected.append(f"AuthRule:{comp_name}")

        elif err_code == "CONTRACT_INVALID_REF":
            contract_id = error.component.split(":", 1)[1]
            db_tables = {t.table_name for t in bundle.database_schema}
            api_endpoints = {a.endpoint_id for a in bundle.api_schema}
            ui_views = {v.view_id for v in bundle.ui_schema}
            for con in bundle.contracts:
                if con.contract_id == contract_id:
                    valid_refs = []
                    for gen in con.generated_components:
                        c_type, c_name = gen.split(":", 1)
                        if c_type == "DB_Table" and c_name in db_tables:
                            valid_refs.append(gen)
                        elif c_type == "API" and c_name in api_endpoints:
                            valid_refs.append(gen)
                        elif c_type == "UI_View" and c_name in ui_views:
                            valid_refs.append(gen)
                    con.generated_components = valid_refs
                    affected.append(f"Contract:{contract_id}")
                    break

        elif err_code == "REQUIRED_FIELD_MISMATCH":
            ep_id = error.component.split(":", 1)[1]
            m = re.search(r"Required database column '([^']+)' is missing", error.message)
            field_name = m.group(1) if m else None
            
            for ap in bundle.api_schema:
                if ap.endpoint_id == ep_id:
                    tbl_name = CanonicalNamingEngine.to_snake_case(ap.source_entity)
                    tbl = next((t for t in bundle.database_schema if t.table_name == tbl_name), None)
                    if tbl:
                        if not ap.request_schema:
                            ap.request_schema = {"type": "object", "properties": {}}
                        elif "properties" not in ap.request_schema:
                            ap.request_schema["properties"] = {}
                        
                        if field_name:
                            col = next((c for c in tbl.columns if c.name == field_name), None)
                            if col:
                                ap.request_schema["properties"][field_name] = {"type": col.type}
                        else:
                            for col in tbl.columns:
                                if col.is_primary_key:
                                    continue
                                if not col.is_nullable and col.name not in ap.request_schema["properties"]:
                                    ap.request_schema["properties"][col.name] = {"type": col.type}
                    
                    affected.append(f"APIEndpoint:{ep_id}")
                    break

        elif err_code == "WORKFLOW_MISSING_STEP":
            wf_name = error.component.split(":", 1)[1]
            for wf in spec.workflows:
                if wf.workflow_name == wf_name:
                    if "Verification Step" not in wf.workflow_steps:
                        wf.workflow_steps.append("Verification Step")
                    affected.append(f"Workflow:{wf_name}")
                    break

        elif err_code == "COVERAGE_LOSS":
            feat_name = error.component.split(":", 1)[1]
            feat_snake = CanonicalNamingEngine.to_snake_case(feat_name)
            trace = TraceabilityMetadata(
                source_entity=feat_name,
                source_ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                compiler_phase="Partial Regeneration Engine (Coverage Repair)"
            )
            new_table = DatabaseTableDefinition(
                table_name=feat_snake,
                columns=[
                    ColumnDefinition(name="id", type="string", is_nullable=False, is_primary_key=True),
                    ColumnDefinition(name="name", type="string", is_nullable=True)
                ],
                primary_keys=["id"],
                foreign_keys=[],
                constraints=[],
                indexes=[],
                source_entity=feat_name,
                traceability=trace
            )
            bundle.database_schema.append(new_table)
            bundle.artifacts.append(CompilationArtifact(
                artifact_id=f"art_db_{feat_snake}",
                artifact_type="database_table",
                source_component=f"Entity:{feat_name}",
                generated_component=f"Table:{feat_snake}",
                ast_version=spec.metadata.get("blueprint_project_id", "v1.0"),
                traceability=trace
            ))
            affected.append(f"Feature:{feat_name}")
            affected.append(f"Table:{feat_snake}")

        return bundle, spec, affected


# --- HIGH LEVEL REPAIR ENGINE ---

class RepairHistory:
    _history: List[RepairHistoryEntry] = []

    @classmethod
    def add_entry(cls, entry: RepairHistoryEntry):
        cls._history.append(entry)

    @classmethod
    def get_history(cls) -> List[RepairHistoryEntry]:
        return cls._history


class RepairEngine:
    @staticmethod
    def repair(
        bundle: CompiledSchemaBundle,
        spec: MasterSpecification,
        blueprint: Optional[ApprovedBlueprint] = None
    ) -> Tuple[RepairReport, CompiledSchemaBundle, MasterSpecification, RepairEffectivenessMetrics]:
        # Step 1: Validate bundle
        initial_report = ValidationEngine.validate(bundle, spec, blueprint)
        all_initial_errors = initial_report.errors
        before_error_count = len(all_initial_errors)
        
        if before_error_count == 0:
            # Bundle has no errors, return a clean report
            clean_metrics = RepairEffectivenessMetrics(
                before_error_count=0,
                after_error_count=0,
                reduction_percentage=100.0,
                successful_repairs=0,
                failed_repairs=0
            )
            clean_report = RepairReport(
                repair_id=f"rep_clean_{int(datetime.now().timestamp())}",
                validation_errors_received=[],
                repair_candidates_generated=[],
                repair_actions_executed=[],
                successful_repairs=[],
                failed_repairs=[],
                revalidation_results=initial_report
            )
            return clean_report, bundle, spec, clean_metrics

        repair_id = f"rep_{int(datetime.now().timestamp())}"
        candidates = []
        actions = []
        successful_repairs = []
        failed_repairs = []

        import copy
        bundle_copy = copy.deepcopy(bundle)
        spec_copy = copy.deepcopy(spec)

        for i, error in enumerate(all_initial_errors):
            # Step 2: Impact Analysis
            impact = ImpactAnalyzer.analyze(error, bundle_copy, spec_copy)
            
            # Step 3: Plan Repair
            candidate = RepairPlanner.plan(error, i + 1)
            if not candidate:
                continue
            candidates.append(candidate)

            # Step 4: targeted Repair
            before_state_summary = f"Components: {error.component}; Error: {error.message}"
            bundle_pre_repair = copy.deepcopy(bundle_copy)
            
            repaired_bundle, repaired_spec, affected_components = TargetedRepairEngine.repair_component(
                bundle_copy, spec_copy, candidate, error
            )

            is_safe = RepairSafetyEngine.verify_safety(bundle_pre_repair, repaired_bundle, candidate)
            
            success = False
            after_state_summary = ""
            if is_safe:
                bundle_copy = repaired_bundle
                spec_copy = repaired_spec
                success = True
                after_state_summary = f"Applied strategy {candidate.repair_strategy} successfully."
            else:
                after_state_summary = "Repair rejected by safety engine boundaries check."
                logger.warning(f"Safety violation during repair of {error.error_id}")

            action = RepairAction(
                action_id=f"act_{repair_id}_{i+1:03d}",
                candidate_id=candidate.candidate_id,
                action_description=candidate.repair_strategy,
                affected_components=affected_components,
                before_state=before_state_summary,
                after_state=after_state_summary,
                success=success
            )
            actions.append(action)

        # Step 5: Revalidation
        post_report = ValidationEngine.validate(bundle_copy, spec_copy, blueprint)
        all_post_errors = post_report.errors
        after_error_count = len(all_post_errors)

        # Classify success and failed repairs
        post_err_codes = {e.error_code for e in all_post_errors}
        for act, err in zip(actions, all_initial_errors):
            resolved = err.error_code not in post_err_codes
            act.success = act.success and resolved
            
            if act.success:
                successful_repairs.append(act)
            else:
                failed_repairs.append(act)

            # Log History Entry
            history_entry = RepairHistoryEntry(
                error_id=err.error_id,
                repair_strategy=act.action_description,
                success=act.success,
                before_validation=err,
                after_validation=next((pe for pe in all_post_errors if pe.error_code == err.error_code), None)
            )
            RepairHistory.add_entry(history_entry)

        # Metrics calculation
        reduction = 0.0
        if before_error_count > 0:
            reduction = ((before_error_count - after_error_count) / before_error_count) * 100.0

        metrics = RepairEffectivenessMetrics(
            before_error_count=before_error_count,
            after_error_count=after_error_count,
            reduction_percentage=reduction,
            successful_repairs=len(successful_repairs),
            failed_repairs=len(failed_repairs)
        )

        report = RepairReport(
            repair_id=repair_id,
            validation_errors_received=all_initial_errors,
            repair_candidates_generated=candidates,
            repair_actions_executed=actions,
            successful_repairs=successful_repairs,
            failed_repairs=failed_repairs,
            revalidation_results=post_report
        )

        return report, bundle_copy, spec_copy, metrics
