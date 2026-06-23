import logging
import json
import os
import time
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any, Tuple

from core.naming import CanonicalNamingEngine
from stages.stage4_system import (
    MasterSpecification, EntityDefinition, WorkflowDefinition,
    PermissionDefinition, RelationshipDefinition, Actor, MasterSpecificationBuilder,
    BusinessRuleDefinition
)
from stages.stage5_schema import (
    CompiledSchemaBundle, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, TraceabilityMetadata,
    CompilationArtifact, ColumnDefinition, CompiledSchemaBundleBuilder,
    get_entity_plural_path
)
from stages.stage6_validate import ValidationEngine, ValidationError, ValidationReport
from stages.stage7_repair import RepairEngine, RepairEffectivenessMetrics
from stages.stage3_recommend import ApprovedBlueprint, RecommendedActor, RecommendedFeature, FeatureExplanation, RecommendationSource, RecommendedWorkflow, RecommendedPermission

logger = logging.getLogger(__name__)

# --- PHASE 8 DATA MODELS ---

class SimulationState(BaseModel):
    state_id: str
    current_actor: str
    current_entity: Optional[str] = None
    current_workflow_step: Optional[str] = None
    available_actions: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class SimulationAction(BaseModel):
    action_id: str
    actor: str
    action: str
    target: str
    preconditions: List[str] = Field(default_factory=list)
    expected_result: str


class SimulationTrace(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    actor: str
    action: str
    outcome: Literal["SUCCESS", "FAILED"]
    reason: str
    affected_components: List[str] = Field(default_factory=list)


class StateTransitionRule(BaseModel):
    entity: str
    from_state: str
    to_state: str
    allowed: bool


class BusinessRuleViolation(BaseModel):
    rule_id: str
    entity: str
    message: str
    severity: Literal["CRITICAL", "WARNING"]


class FailureClassification(BaseModel):
    validation_failures: int = 0
    repair_failures: int = 0
    workflow_failures: int = 0
    permission_failures: int = 0
    contract_failures: int = 0
    business_rule_failures: int = 0
    simulation_failures: int = 0


class ExecutionSimulationReport(BaseModel):
    simulation_id: str
    workflows_executed: List[str] = Field(default_factory=list)
    successful_steps: int = 0
    failed_steps: int = 0
    permission_failures: int = 0
    contract_failures: int = 0
    validation_failures: int = 0
    repair_failures: int = 0
    business_rule_failures: int = 0
    success_rate: float = 0.0
    simulation_traces: List[SimulationTrace] = Field(default_factory=list)


class DeterminismReport(BaseModel):
    prompt: str
    runs: List[Dict[str, Any]] = Field(default_factory=list)
    matching_runs: int = 0
    determinism_score: float = 0.0


class EvaluationLeaderboardEntry(BaseModel):
    run_id: str
    mode: Literal["FAST", "BALANCED", "HIGH_QUALITY"]
    success_rate: float
    repair_rate: float
    simulation_pass_rate: float
    latency: float
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class EvaluationReport(BaseModel):
    run_id: str
    prompt_count: int
    success_rate: float
    failure_rate: float
    repair_rate: float
    average_latency: float
    average_repairs: float
    simulation_pass_rate: float
    determinism_score: float
    repair_success_rate: float
    business_rule_pass_rate: float
    validation_pass_rate: float
    failure_classification: FailureClassification
    determinism_reports: List[DeterminismReport] = Field(default_factory=list)


# --- 1. DATABASE SIMULATOR ---

class DatabaseSimulator:
    def __init__(self, db_schema: List[DatabaseTableDefinition]):
        self.tables: Dict[str, List[Dict[str, Any]]] = {t.table_name: [] for t in db_schema}
        self.schema_map: Dict[str, DatabaseTableDefinition] = {t.table_name: t for t in db_schema}

    def insert(self, table_name: str, row: Dict[str, Any]) -> Tuple[bool, str]:
        if table_name not in self.tables:
            return False, f"Table '{table_name}' does not exist in database schema."

        tbl_def = self.schema_map[table_name]

        # 1. Check Primary Key
        pk_col = tbl_def.primary_keys[0] if tbl_def.primary_keys else "id"
        pk_val = row.get(pk_col)
        if pk_val is None:
            return False, f"Missing primary key value for '{pk_col}' in table '{table_name}'."
        
        # PK Uniqueness
        for existing in self.tables[table_name]:
            if existing.get(pk_col) == pk_val:
                return False, f"Primary key violation: row with {pk_col}={pk_val} already exists in table '{table_name}'."

        # 2. Check required fields (nullability)
        for col in tbl_def.columns:
            if not col.is_nullable and col.name != pk_col:
                if col.name not in row or row[col.name] is None:
                    return False, f"Nullability constraint violation: column '{col.name}' in table '{table_name}' is not nullable."

        # 3. Check Foreign Keys reference validity
        for fk in tbl_def.foreign_keys:
            col_name = fk.get("column")
            ref_tbl = fk.get("references_table")
            ref_col = fk.get("references_column")
            val = row.get(col_name)
            
            if val is not None:
                if ref_tbl not in self.tables:
                    return False, f"Foreign key error: target table '{ref_tbl}' does not exist."
                
                # Check if referenced row exists
                exists = False
                for target_row in self.tables[ref_tbl]:
                    if target_row.get(ref_col) == val:
                        exists = True
                        break
                if not exists:
                    return False, f"Foreign key violation: value '{val}' in column '{col_name}' of table '{table_name}' does not reference any valid key in '{ref_tbl}.{ref_col}'."

        self.tables[table_name].append(row)
        return True, "Insert successful."

    def select(self, table_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        if table_name not in self.tables:
            return []
        
        results = []
        for row in self.tables[table_name]:
            match = True
            for k, v in query.items():
                if row.get(k) != v:
                    match = False
                    break
            if match:
                results.append(row)
        return results

    def update(self, table_name: str, row_id: Any, new_data: Dict[str, Any]) -> Tuple[bool, str]:
        if table_name not in self.tables:
            return False, f"Table '{table_name}' does not exist."
        
        tbl_def = self.schema_map[table_name]
        pk_col = tbl_def.primary_keys[0] if tbl_def.primary_keys else "id"
        
        # Find row
        row_idx = -1
        for idx, row in enumerate(self.tables[table_name]):
            if row.get(pk_col) == row_id:
                row_idx = idx
                break
                
        if row_idx == -1:
            return False, f"Row with {pk_col}={row_id} not found in table '{table_name}'."
            
        target_row = dict(self.tables[table_name][row_idx])
        target_row.update(new_data)
        
        # Verify FK constraints on updated fields
        for fk in tbl_def.foreign_keys:
            col_name = fk.get("column")
            if col_name in new_data:
                ref_tbl = fk.get("references_table")
                ref_col = fk.get("references_column")
                val = new_data.get(col_name)
                if val is not None:
                    exists = False
                    for target_row_fk in self.tables[ref_tbl]:
                        if target_row_fk.get(ref_col) == val:
                            exists = True
                            break
                    if not exists:
                        return False, f"Foreign key violation on update: value '{val}' not found in '{ref_tbl}.{ref_col}'."
                        
        self.tables[table_name][row_idx] = target_row
        return True, "Update successful."

    def delete(self, table_name: str, row_id: Any) -> Tuple[bool, str]:
        if table_name not in self.tables:
            return False, f"Table '{table_name}' does not exist."
        
        tbl_def = self.schema_map[table_name]
        pk_col = tbl_def.primary_keys[0] if tbl_def.primary_keys else "id"
        
        # Check if other tables have foreign keys pointing to this row
        for other_tbl_name, other_tbl_rows in self.tables.items():
            other_tbl_def = self.schema_map[other_tbl_name]
            for fk in other_tbl_def.foreign_keys:
                if fk.get("references_table") == table_name and fk.get("references_column") == pk_col:
                    col_name = fk.get("column")
                    for r in other_tbl_rows:
                        if r.get(col_name) == row_id:
                            return False, f"Foreign key restrict: row in table '{table_name}' is referenced by table '{other_tbl_name}' column '{col_name}'."

        self.tables[table_name] = [r for r in self.tables[table_name] if r.get(pk_col) != row_id]
        return True, "Delete successful."


# --- 2. AUTH SIMULATOR ---

class AuthSimulator:
    @staticmethod
    def check_permission(actor: str, action_slug: str, auth_schema: List[AuthRuleDefinition]) -> Tuple[bool, str]:
        if actor == "Admin":
            return True, "Admin authorized by default."
            
        rule = next((au for au in auth_schema if au.role == actor), None)
        if not rule:
            return False, f"Role '{actor}' is unauthorized: no Auth rule definition exists."
            
        # Check permissions list
        allowed = False
        for perm in rule.permissions:
            if perm == action_slug or perm == "ManageAllRecords" or action_slug in perm:
                allowed = True
                break
                
        # Check restricted actions
        if allowed:
            for rest in rule.restricted_actions:
                if rest == action_slug or action_slug in rest:
                    return False, f"Action '{action_slug}' is explicitly restricted for role '{actor}'."
            return True, f"Role '{actor}' authorized for action '{action_slug}'."
            
        return False, f"Role '{actor}' lacks permission '{action_slug}'."


# --- 3. API SIMULATOR ---

class APISimulator:
    @staticmethod
    def simulate_call(
        method: Literal["GET", "POST", "PUT", "DELETE"],
        path: str,
        body: Dict[str, Any],
        actor: str,
        bundle: CompiledSchemaBundle,
        db_sim: DatabaseSimulator
    ) -> Tuple[bool, str, Optional[Any]]:
        # Find endpoint
        endpoint = None
        for ap in bundle.api_schema:
            if ap.method == method:
                # Handle path matching (e.g. /api/v1/members/{id} matching /api/v1/members/m1)
                clean_p1 = ap.path.replace("{id}", "").rstrip("/")
                clean_p2 = path.split("/")[0:-1]
                clean_p2 = "/".join(clean_p2) if len(path.split("/")) > 1 else path
                
                if clean_p1 in path or path == ap.path:
                    endpoint = ap
                    break
                    
        if not endpoint:
            return False, f"Route '{method} {path}' not found in API schema compilation.", None

        # Verify endpoint permission
        authorized, reason = AuthSimulator.check_permission(actor, endpoint.endpoint_id, bundle.auth_schema)
        if not authorized and actor in endpoint.permissions:
            authorized = True
        if not authorized:
            return False, f"Permission Denied: {reason}", None

        # Determine target table
        table_name = CanonicalNamingEngine.to_snake_case(endpoint.source_entity)
        if table_name == "system" and endpoint.endpoint_id.startswith("execute_"):
            return True, "Custom workflow execution endpoint authorized.", {"status": "authorized"}

        # Validate Request Schema
        if method in ("POST", "PUT") and endpoint.request_schema:
            if "properties" in endpoint.request_schema:
                props = endpoint.request_schema["properties"]
                for p_name, p_def in props.items():
                    # For POST, check required properties if table requires them
                    tbl_def = db_sim.schema_map.get(table_name)
                    if tbl_def:
                        col = next((c for c in tbl_def.columns if c.name == p_name), None)
                        if col and not col.is_nullable and not col.is_primary_key:
                            if p_name not in body:
                                return False, f"API Request Validation Failed: missing required field '{p_name}' in request body.", None

        # Perform DB Simulation
        if method == "POST":
            # Auto-generate PK if missing
            tbl_def = db_sim.schema_map.get(table_name)
            pk_col = tbl_def.primary_keys[0] if tbl_def and tbl_def.primary_keys else "id"
            if pk_col not in body:
                body[pk_col] = f"{table_name}_val_{len(db_sim.tables.get(table_name, [])) + 1}"
            success, msg = db_sim.insert(table_name, body)
            return success, msg, body if success else None
            
        elif method == "GET":
            # Check if get single or get list
            if path.endswith("}") or path.split("/")[-1].startswith(f"{table_name}_val_") or path.split("/")[-1].isalnum() and len(path.split("/")) > 4:
                row_id = path.split("/")[-1]
                tbl_def = db_sim.schema_map.get(table_name)
                pk_col = tbl_def.primary_keys[0] if tbl_def and tbl_def.primary_keys else "id"
                rows = db_sim.select(table_name, {pk_col: row_id})
                if not rows:
                    return False, f"Resource with {pk_col}={row_id} not found in table '{table_name}'.", None
                return True, "Fetch successful.", rows[0]
            else:
                rows = db_sim.select(table_name, {})
                return True, "Fetch successful.", rows
                
        elif method == "PUT":
            row_id = path.split("/")[-1]
            success, msg = db_sim.update(table_name, row_id, body)
            return success, msg, body if success else None
            
        elif method == "DELETE":
            row_id = path.split("/")[-1]
            success, msg = db_sim.delete(table_name, row_id)
            return success, msg, {"status": "deleted"} if success else None

        return False, "Unsupported method.", None


# --- 4. BUSINESS RULE SIMULATOR ---

class BusinessRuleSimulator:
    @staticmethod
    def verify_rule(
        rule: BusinessRuleDefinition,
        table_name: str,
        row: Dict[str, Any],
        db_sim: DatabaseSimulator
    ) -> Optional[BusinessRuleViolation]:
        # Implement deterministic checks for Gym, CRM, Hospital, School, Inventory
        rule_id = rule.rule_id
        
        # Gym Rule: Count bookings capped at max 3 per day
        if rule_id == "BR_001" and table_name == "class_booking":
            m_id = row.get("member_id")
            if m_id:
                existing = db_sim.select("class_booking", {"member_id": m_id})
                if len(existing) >= 3:
                    return BusinessRuleViolation(
                        rule_id=rule_id,
                        entity="ClassBooking",
                        message=f"Business Rule Violation: Member '{m_id}' exceeds daily booking cap of 3 classes.",
                        severity="CRITICAL"
                    )
                    
        # School Rule: Course Capacity (mock rule logic)
        if "capacity" in rule.rule.lower() or "limit" in rule.rule.lower():
            if table_name == "enrollment":
                c_id = row.get("course_id")
                if c_id:
                    existing = db_sim.select("enrollment", {"course_id": c_id})
                    # simulate capacity limit of 2
                    if len(existing) >= 2:
                        return BusinessRuleViolation(
                            rule_id=rule_id,
                            entity="Enrollment",
                            message=f"Business Rule Violation: Course '{c_id}' enrollment exceeds maximum class capacity.",
                            severity="CRITICAL"
                        )
                        
        return None


# --- 5. WORKFLOW SIMULATOR ---

class WorkflowSimulator:
    @staticmethod
    def simulate_workflow(
        wf: WorkflowDefinition,
        actor: str,
        bundle: CompiledSchemaBundle,
        spec: MasterSpecification,
        db_sim: DatabaseSimulator,
        state_rules: List[StateTransitionRule]
    ) -> Tuple[int, int, List[SimulationTrace], List[BusinessRuleViolation]]:
        traces = []
        rule_violations = []
        success_steps = 0
        failed_steps = 0
        
        # Initialize context state
        state = SimulationState(
            state_id=f"state_{wf.workflow_id}",
            current_actor=actor,
            current_workflow_step=None
        )

        for step in wf.workflow_steps:
            state.current_workflow_step = step
            trace_entry = SimulationTrace(
                actor=actor,
                action=step,
                outcome="SUCCESS",
                reason="",
                affected_components=[f"WorkflowStep:{step}"]
            )

            # Map steps to API simulator actions
            # e.g., 'Select Class' -> mock context mapping, no db operation needed
            # 'Verify Capacity' -> query DB simulator
            # 'Log Booking Record' -> POST DB simulator
            step_lower = step.lower()
            success = True
            reason = "Step executed successfully."
            
            # State Transition Validation
            from_state = state.context.get("entity_state", "PENDING")
            to_state = None
            if "confirm" in step_lower:
                to_state = "CONFIRMED"
            elif "complete" in step_lower:
                to_state = "COMPLETED"
            elif "reopen" in step_lower or "reset" in step_lower:
                to_state = "PENDING"
                
            if to_state:
                rule = next((r for r in state_rules if r.from_state == from_state and r.to_state == to_state), None)
                if rule and not rule.allowed:
                    success = False
                    reason = f"State Transition Rejected: transition from {from_state} to {to_state} is not allowed."
                else:
                    state.context["entity_state"] = to_state

            if success:
                if "select" in step_lower or "choose" in step_lower:
                    state.context["selected_id"] = "class_schedule_val_1"
                    state.context["member_id"] = "member_val_1"
                    state.context["course_id"] = "course_val_1"
                    state.context["lead_id"] = "lead_val_1"
                    
                elif "capacity" in step_lower or "verify" in step_lower:
                    # Query db schedule or status
                    tbl_name = "class_schedule" if "class" in step_lower else "class_booking"
                    if tbl_name in db_sim.tables:
                        rows = db_sim.select(tbl_name, {})
                        state.context["schedule_rows"] = len(rows)
                    else:
                        state.context["schedule_rows"] = 0
                        
                elif "log" in step_lower or "book" in step_lower or "create" in step_lower or "enroll" in step_lower:
                    # Determine table
                    target_tbl = "class_booking"
                    if "enroll" in step_lower:
                        target_tbl = "enrollment"
                    elif "appointment" in step_lower:
                        target_tbl = "appointment"
                    elif "lead" in step_lower:
                        target_tbl = "lead"
                    elif "stock" in step_lower:
                        target_tbl = "stock_order"
                        
                    body = {
                        "id": f"{target_tbl}_val_{len(db_sim.tables.get(target_tbl, [])) + 1}",
                        "name": f"Mock {target_tbl} record",
                        "status": "PENDING"
                    }
                    
                    # Bind foreign keys based on context
                    if target_tbl == "class_booking":
                        body["member_id"] = state.context.get("member_id", "member_val_1")
                        body["class_schedule_id"] = state.context.get("selected_id", "class_schedule_val_1")
                    elif target_tbl == "enrollment":
                        body["student_id"] = "student_val_1"
                        body["course_id"] = state.context.get("course_id", "course_val_1")
                    elif target_tbl == "appointment":
                        body["patient_id"] = "patient_val_1"
                        body["doctor_id"] = "doctor_val_1"
                    elif target_tbl == "lead":
                        body["sales_agent_id"] = "sales_agent_val_1"
                    elif target_tbl == "stock_order":
                        body["warehouse_staff_id"] = "warehouse_staff_val_1"

                    # Dynamically fill other required non-nullable columns with mock values
                    tbl_def = db_sim.schema_map.get(target_tbl)
                    if tbl_def:
                        pk_col = tbl_def.primary_keys[0] if tbl_def.primary_keys else "id"
                        for col in tbl_def.columns:
                            if not col.is_nullable and col.name != pk_col and col.name not in body:
                                if col.type == "integer":
                                    body[col.name] = 1
                                elif col.type == "boolean":
                                    body[col.name] = True
                                elif col.type == "datetime":
                                    body[col.name] = "2026-06-23T12:00:00"
                                else:
                                    body[col.name] = f"mock_{col.name}_val"

                    # Check Business Rules
                    for br in spec.business_rules:
                        viol = BusinessRuleSimulator.verify_rule(br, target_tbl, body, db_sim)
                        if viol:
                            rule_violations.append(viol)
                            success = False
                            reason = viol.message
                            break

                    if success:
                        # Run API simulation POST call
                        plural_path = get_entity_plural_path(target_tbl)
                        ok, msg, res = APISimulator.simulate_call("POST", f"/api/v1/{plural_path}", body, actor, bundle, db_sim)
                        if not ok:
                            success = False
                            reason = msg

            # Update trace and metrics
            if success:
                success_steps += 1
                trace_entry.outcome = "SUCCESS"
                trace_entry.reason = reason
            else:
                failed_steps += 1
                trace_entry.outcome = "FAILED"
                trace_entry.reason = reason
                traces.append(trace_entry)
                # Break execution of the workflow
                break
                
            traces.append(trace_entry)

        return success_steps, failed_steps, traces, rule_violations


# --- 6. HIGH LEVEL EXECUTION SIMULATOR ---

class ExecutionSimulator:
    @staticmethod
    def simulate(
        bundle: CompiledSchemaBundle,
        spec: MasterSpecification,
        blueprint: Optional[ApprovedBlueprint] = None
    ) -> ExecutionSimulationReport:
        simulation_id = f"sim_{int(time.time())}"
        
        # 1. Instantiate database simulator with compiled schemas
        db_sim = DatabaseSimulator(bundle.database_schema)
        
        # Seed default actors/entities data in database to satisfy foreign keys
        for tbl_name in db_sim.tables.keys():
            # Seed 1 dummy record in each table to simplify reference lookups
            dummy_row = {"id": f"{tbl_name}_val_1", "name": f"Seed {tbl_name}"}
            # Add other required fields with seed values
            tbl_def = db_sim.schema_map[tbl_name]
            for col in tbl_def.columns:
                if not col.is_nullable and col.name not in dummy_row:
                    if col.type == "integer":
                        dummy_row[col.name] = 1
                    elif col.type == "boolean":
                        dummy_row[col.name] = True
                    else:
                        dummy_row[col.name] = "seeded_val"
            db_sim.tables[tbl_name].append(dummy_row)

        # 2. Setup state transition rules
        state_rules = [
            StateTransitionRule(entity="Booking", from_state="PENDING", to_state="CONFIRMED", allowed=True),
            StateTransitionRule(entity="Booking", from_state="CONFIRMED", to_state="COMPLETED", allowed=True),
            StateTransitionRule(entity="Booking", from_state="COMPLETED", to_state="PENDING", allowed=False),
        ]

        # 3. Simulate workflows
        workflows_run = []
        total_success = 0
        total_failed = 0
        perm_failures = 0
        br_failures = 0
        all_traces = []

        for wf in spec.workflows:
            workflows_run.append(wf.workflow_name)
            # Find primary actor
            primary_actor = wf.actors[0] if wf.actors else "Admin"
            
            s_ok, s_fail, traces, viols = WorkflowSimulator.simulate_workflow(
                wf, primary_actor, bundle, spec, db_sim, state_rules
            )
            total_success += s_ok
            total_failed += s_fail
            br_failures += len(viols)
            all_traces.extend(traces)
            
            # Check unauthorized access simulation
            # Attempt to invoke custom endpoint with an unauthorized actor role
            unauth_actor = "GymMember" if primary_actor != "GymMember" else "Doctor"
            wf_slug = wf.workflow_id.lower().replace(" ", "_")
            ok, msg, res = APISimulator.simulate_call("POST", f"/api/v1/workflows/{wf_slug}", {}, unauth_actor, bundle, db_sim)
            if not ok and "Permission Denied" in msg:
                perm_failures += 1
                all_traces.append(SimulationTrace(
                    actor=unauth_actor,
                    action=f"execute_{wf_slug}",
                    outcome="FAILED",
                    reason=f"Successfully blocked unauthorized access: {msg}"
                ))

        # Check API CRUD schemas and permissions
        for ap in bundle.api_schema:
            if not ap.endpoint_id.startswith("execute_"):
                # Run GET call
                plural_path = get_entity_plural_path(ap.source_entity)
                ok, msg, res = APISimulator.simulate_call("GET", f"/api/v1/{plural_path}", {}, "Admin", bundle, db_sim)
                if ok:
                    total_success += 1
                else:
                    total_failed += 1

        total_steps = total_success + total_failed
        rate = (total_success / total_steps) * 100.0 if total_steps > 0 else 100.0

        # Calculate failures classification
        # validation/repair/contract failures are checked at higher orchestrators
        return ExecutionSimulationReport(
            simulation_id=simulation_id,
            workflows_executed=workflows_run,
            successful_steps=total_success,
            failed_steps=total_failed,
            permission_failures=perm_failures,
            contract_failures=0,
            validation_failures=len(bundle.compilation_report.errors),
            repair_failures=0,
            business_rule_failures=br_failures,
            success_rate=rate,
            simulation_traces=all_traces
        )


# --- 7. EVALUATION FRAMEWORK & CONFIGURATOR ---

class EvaluationDataset:
    NORMAL_PROMPTS = [
        "Build a gym management system with class schedules and slot booking.",
        "Create a CRM to track sales leads and agents log interactions.",
        "Compile a hospital appointment scheduler linking patients and doctors.",
        "Build a school management database where students enroll in courses.",
        "Generate an inventory stock tracking system with warehouse logins.",
        "Compile a tasks project workflow linking assignees and managers.",
        "Build a restaurant food delivery application with user orders.",
        "Create a library catalog lookup app tracing books and authors.",
        "Generate a hotel reservation tracker mapping guests to rooms.",
        "Build a simple blog posts dashboard allowing admin to publish content."
    ]
    
    EDGE_CASE_PROMPTS = [
        # Vague
        "Build me a system database.",
        "Implement a web application dashboard portal.",
        # Conflicting
        "Gym class bookings are open to everyone but only GymMembers can check booking logs.",
        "Teachers grade student exams but students can override teacher grades.",
        # Incomplete
        "Create a clinic scheduler for booking schedules without patient info.",
        "Generate a school system where students can take courses.",
        # Contradictory
        "Course capacity must be capped at 0 seats but students can still enroll.",
        "Sales deals require a lead status of CONVERTED but deals cannot be converted.",
        "Admin has zero permissions but controls all database logs.",
        "Users can register and log in but auth rules restrict all active sessions."
    ]


class EvaluationFramework:
    LEADERBOARD_PATH = "evaluation_leaderboard.json"

    @staticmethod
    def run_pipeline(
        prompt: str,
        mode: Literal["FAST", "BALANCED", "HIGH_QUALITY"],
        app_type: str = "Gym"
    ) -> Tuple[CompiledSchemaBundle, MasterSpecification, float, int, int]:
        # Simulate intent, recommendation, spec compile, schema compile, validate, and repair
        start_time = time.time()
        
        # 1. Compile intent & recommendation (mock baseline)
        rec_member = RecommendedActor(name="GymMember", description="A gym member", relevance_score=1.0, why_needed="Book classes")
        rec_admin = RecommendedActor(name="Admin", description="Admin user", relevance_score=0.90, why_needed="Manage gym")
        
        source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
        explanation = FeatureExplanation(
            feature_name="BookClass", what_it_does="Book slot", why_recommended="needed", business_value="rev",
            source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
        )
        rec_feat = RecommendedFeature(name="BookClass", description="Book class slots", actor_involved="GymMember", explanation=explanation)
        rec_wf = RecommendedWorkflow(
            name="ClassBookingFlow", description="Book spot", steps=["Select Class", "Verify Capacity", "Log Booking Record"], actor_involved="GymMember", why_needed="Core flow"
        )
        rec_perm = RecommendedPermission(actor="GymMember", action="BookClass", description="Book slots", why_needed="Required")
        
        bp = ApprovedBlueprint(
            project_id=CanonicalNamingEngine.to_snake_case(prompt.split()[0].replace(".", "")),
            app_type=app_type,
            actors=[rec_member, rec_admin],
            features=[rec_feat],
            workflows=[rec_wf],
            permissions=[rec_perm],
            innovations=[]
        )

        # 2. Spec compile
        spec = MasterSpecificationBuilder.compile_specification(bp)
        
        # 3. Schema compile
        bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
        
        # 4. Mode-based validation & repair
        repairs_run = 0
        validation_fails = 0
        successful_repairs = 0
        failed_repairs = 0
        
        if mode in ("BALANCED", "HIGH_QUALITY"):
            report = ValidationEngine.validate(bundle, spec, bp)
            if not report.is_valid:
                validation_fails += len(report.errors)
                # Repair once or multi-pass
                rep_report, bundle, spec, metrics = RepairEngine.repair(bundle, spec, bp)
                repairs_run += metrics.successful_repairs + metrics.failed_repairs
                
                if mode == "HIGH_QUALITY" and not rep_report.revalidation_results.is_valid:
                    # Run second pass
                    rep_report2, bundle, spec, metrics2 = RepairEngine.repair(bundle, spec, bp)
                    repairs_run += metrics2.successful_repairs + metrics2.failed_repairs

        latency = (time.time() - start_time) * 1000.0  # ms
        return bundle, spec, latency, repairs_run, validation_fails, successful_repairs, failed_repairs

    @classmethod
    def evaluate(
        cls,
        mode: Literal["FAST", "BALANCED", "HIGH_QUALITY"] = "BALANCED"
    ) -> Tuple[EvaluationReport, List[EvaluationLeaderboardEntry]]:
        run_id = f"eval_{int(time.time())}"
        
        prompts = EvaluationDataset.NORMAL_PROMPTS + EvaluationDataset.EDGE_CASE_PROMPTS
        prompt_count = len(prompts)
        
        total_latency = 0.0
        total_repairs = 0
        total_validations_failed = 0
        successful_runs = 0
        total_simulation_passes = 0
        
        total_successful_repairs = 0
        total_failed_repairs = 0
        runs_passing_validation_initially = 0
        runs_with_zero_br_failures = 0
        
        val_fails = 0
        rep_fails = 0
        wf_fails = 0
        perm_fails = 0
        br_fails = 0
        
        determinism_reports = []

        for p in prompts:
            # Map prompt category to domain type
            app_type = "Gym"
            if "crm" in p.lower():
                app_type = "CRM"
            elif "hospital" in p.lower() or "clinic" in p.lower():
                app_type = "Hospital"
            elif "school" in p.lower() or "course" in p.lower():
                app_type = "School"
            elif "inventory" in p.lower() or "stock" in p.lower():
                app_type = "Inventory"

            bundle, spec, latency, repairs, v_fails, s_repairs, f_repairs = cls.run_pipeline(p, mode, app_type)
            
            total_latency += latency
            total_repairs += repairs
            total_validations_failed += v_fails
            total_successful_repairs += s_repairs
            total_failed_repairs += f_repairs
            
            if v_fails == 0:
                runs_passing_validation_initially += 1
            
            # Execute simulation
            sim_report = ExecutionSimulator.simulate(bundle, spec)
            
            total_simulation_passes += 1 if sim_report.failed_steps == 0 else 0
            perm_fails += sim_report.permission_failures
            br_fails += sim_report.business_rule_failures
            
            if sim_report.business_rule_failures == 0:
                runs_with_zero_br_failures += 1
            
            # If valid post-repair, count as successful run
            report = ValidationEngine.validate(bundle, spec)
            if report.is_valid:
                successful_runs += 1
            else:
                val_fails += len(report.errors)
                rep_fails += repairs

            # Determinism checks for HIGH_QUALITY
            if mode == "HIGH_QUALITY":
                runs_list = []
                for _ in range(5):
                    b, s, _, _, _, _, _ = cls.run_pipeline(p, mode, app_type)
                    runs_list.append({
                        "api_count": len(b.api_schema),
                        "db_count": len(b.database_schema),
                        "ui_count": len(b.ui_schema),
                    })
                
                # Check match rate
                matches = 1
                for r in runs_list[1:]:
                    if r == runs_list[0]:
                        matches += 1
                determinism_reports.append(DeterminismReport(
                    prompt=p,
                    runs=runs_list,
                    matching_runs=matches,
                    determinism_score=matches / 5.0
                ))

        success_rate = (successful_runs / prompt_count) * 100.0
        failure_rate = 100.0 - success_rate
        repair_rate = (total_repairs / prompt_count) * 100.0
        sim_pass_rate = (total_simulation_passes / prompt_count) * 100.0
        
        det_score = 1.0
        if determinism_reports:
            det_score = sum(r.determinism_score for r in determinism_reports) / len(determinism_reports)

        validation_pass_rate = (runs_passing_validation_initially / prompt_count) * 100.0
        
        rep_total = total_successful_repairs + total_failed_repairs
        repair_success_rate = (total_successful_repairs / rep_total) * 100.0 if rep_total > 0 else 100.0
        
        business_rule_pass_rate = (runs_with_zero_br_failures / prompt_count) * 100.0

        classification = FailureClassification(
            validation_failures=val_fails,
            repair_failures=rep_fails,
            workflow_failures=0,
            permission_failures=perm_fails,
            contract_failures=0,
            business_rule_failures=br_fails,
            simulation_failures=prompt_count - total_simulation_passes
        )

        eval_report = EvaluationReport(
            run_id=run_id,
            prompt_count=prompt_count,
            success_rate=success_rate,
            failure_rate=failure_rate,
            repair_rate=repair_rate,
            average_latency=total_latency / prompt_count,
            average_repairs=total_repairs / prompt_count,
            simulation_pass_rate=sim_pass_rate,
            determinism_score=det_score,
            repair_success_rate=repair_success_rate,
            business_rule_pass_rate=business_rule_pass_rate,
            validation_pass_rate=validation_pass_rate,
            failure_classification=classification,
            determinism_reports=determinism_reports
        )

        # Save to Leaderboard
        entry = EvaluationLeaderboardEntry(
            run_id=run_id,
            mode=mode,
            success_rate=success_rate,
            repair_rate=repair_rate,
            simulation_pass_rate=sim_pass_rate,
            latency=total_latency / prompt_count
        )
        
        leaderboard = cls.load_leaderboard()
        leaderboard.append(entry)
        cls.save_leaderboard(leaderboard)

        return eval_report, leaderboard

    @classmethod
    def load_leaderboard(cls) -> List[EvaluationLeaderboardEntry]:
        if not os.path.exists(cls.LEADERBOARD_PATH):
            return []
        try:
            with open(cls.LEADERBOARD_PATH, "r") as f:
                data = json.load(f)
                return [EvaluationLeaderboardEntry(**x) for x in data]
        except Exception:
            return []

    @classmethod
    def save_leaderboard(cls, leaderboard: List[EvaluationLeaderboardEntry]):
        try:
            with open(cls.LEADERBOARD_PATH, "w") as f:
                json.dump([x.model_dump() for x in leaderboard], f, indent=4)
        except Exception as e:
            logger.error(f"Error saving leaderboard: {e}")
