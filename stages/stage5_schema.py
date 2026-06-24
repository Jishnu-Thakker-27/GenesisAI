import json
import logging
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any, Union
from datetime import datetime

from core.naming import CanonicalNamingEngine
from core.ast import Actor, EntityField, Entity, BusinessRule
from stages.stage4_system import (
    MasterSpecification, EntityDefinition, RelationshipDefinition, WorkflowDefinition,
    PermissionDefinition, DesignDecision
)

logger = logging.getLogger(__name__)

PLURAL_MAP = {
    "member": "members",
    "trainer": "trainers",
    "classschedule": "class-schedules",
    "classbooking": "class-bookings",
    "customer": "customers",
    "lead": "leads",
    "interactionlog": "interaction-logs",
    "patient": "patients",
    "doctor": "doctors",
    "appointment": "appointments",
    "medicalrecord": "medical-records",
    "student": "students",
    "teacher": "teachers",
    "course": "courses",
    "enrollment": "enrollments",
    "product": "products",
    "supplier": "suppliers",
    "stockorder": "stock-orders",
    "user": "users"
}

def get_entity_plural_path(entity_name: str) -> str:
    name_lower = entity_name.lower().replace("_", "").replace("-", "")
    return PLURAL_MAP.get(name_lower, name_lower + "s")


# --- TRACEABILITY METADATA MODEL ---

class TraceabilityMetadata(BaseModel):
    source_entity: Optional[str] = None
    source_workflow: Optional[str] = None
    source_design_decisions: List[str] = Field(default_factory=list)
    source_business_rules: List[str] = Field(default_factory=list)
    source_ast_version: str
    compiler_phase: str = "Schema Generation Engine"


class CompilationArtifact(BaseModel):
    artifact_id: str = Field(..., description="Unique artifact tracking ID")
    artifact_type: Literal["database_table", "api_endpoint", "ui_view", "auth_rule"]
    source_component: str = Field(..., description="e.g. Entity:Member")
    generated_component: str = Field(..., description="e.g. Table:member")
    ast_version: str
    traceability: TraceabilityMetadata


# --- SCHEMA AST MODELS ---

class ColumnDefinition(BaseModel):
    name: str = Field(..., description="snake_case column name")
    type: str = Field(..., description="string, integer, float, boolean, datetime, relationship")
    is_nullable: bool = False
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = Field(None, description="Format: TableName.column_name")


class DatabaseTableDefinition(BaseModel):
    table_name: str = Field(..., description="snake_case table name")
    columns: List[ColumnDefinition] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    indexes: List[str] = Field(default_factory=list)
    source_entity: str
    traceability: TraceabilityMetadata


class APIEndpointDefinition(BaseModel):
    endpoint_id: str = Field(..., description="Unique REST operation slug")
    path: str = Field(..., description="REST Path")
    method: Literal["GET", "POST", "PUT", "DELETE"]
    request_schema: Dict[str, Any] = Field(default_factory=dict)
    response_schema: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    source_entity: str
    traceability: TraceabilityMetadata


class UIComponent(BaseModel):
    type: Literal["input_field", "submit_button", "table_grid", "detail_card", "chart_dashboard"]
    label: str
    bindings: Dict[str, Any] = Field(default_factory=dict)


class UIViewDefinition(BaseModel):
    view_id: str = Field(..., description="Unique view slug")
    view_name: str
    components: List[UIComponent] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    source_workflow: str
    linked_endpoints: List[str] = Field(default_factory=list)
    traceability: TraceabilityMetadata


class AuthRuleDefinition(BaseModel):
    role: str = Field(..., description="Role profile name")
    permissions: List[str] = Field(default_factory=list)
    restricted_actions: List[str] = Field(default_factory=list)
    authentication_requirements: List[str] = Field(default_factory=list)
    traceability: TraceabilityMetadata


class SchemaContract(BaseModel):
    contract_id: str
    source_ast_component: str
    generated_components: List[str] = Field(default_factory=list)
    validation_rules: List[str] = Field(default_factory=list)
    traceability: TraceabilityMetadata


class ConsistencyViolation(BaseModel):
    violation_id: str
    layer_a: str
    layer_b: str
    message: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    related_components: List[str] = Field(default_factory=list)


class ASTVersion(BaseModel):
    version: str
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    compiler_phase: str = "Schema Generation Engine"
    source_ast_version: str


class SchemaCompilationReport(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    compiled_entities: List[str] = Field(default_factory=list)
    compiled_workflows: List[str] = Field(default_factory=list)
    compiled_permissions: List[str] = Field(default_factory=list)
    compiled_relationships: List[str] = Field(default_factory=list)
    consistency_checks_passed: int = 0
    consistency_checks_failed: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CompiledSchemaBundle(BaseModel):
    database_schema: List[DatabaseTableDefinition] = Field(default_factory=list)
    api_schema: List[APIEndpointDefinition] = Field(default_factory=list)
    ui_schema: List[UIViewDefinition] = Field(default_factory=list)
    auth_schema: List[AuthRuleDefinition] = Field(default_factory=list)
    contracts: List[SchemaContract] = Field(default_factory=list)
    consistency_report: List[ConsistencyViolation] = Field(default_factory=list)
    ast_version: ASTVersion
    compilation_report: SchemaCompilationReport
    artifacts: List[CompilationArtifact] = Field(default_factory=list)



# --- COMPILER MODULES ---

class DatabaseSchemaCompiler:
    @staticmethod
    def compile(spec: MasterSpecification, ast_version: str) -> List[DatabaseTableDefinition]:
        tables = []
        for ent in spec.entities:
            # Map columns
            columns = []
            primary_keys = []
            foreign_keys = []
            constraints = []
            
            for field in ent.fields:
                is_pk = field.is_key
                is_fk = field.type == "relationship" and field.references is not None
                
                if is_pk:
                    primary_keys.append(field.name)
                if is_fk:
                    target_table = CanonicalNamingEngine.to_snake_case(field.references.split(".")[0])
                    target_col = field.references.split(".")[1]
                    foreign_keys.append({
                        "column": field.name,
                        "references_table": target_table,
                        "references_column": target_col
                    })
                
                columns.append(ColumnDefinition(
                    name=field.name,
                    type=field.type,
                    is_nullable=not field.required,
                    is_primary_key=is_pk,
                    is_foreign_key=is_fk,
                    references=field.references
                ))
            
            # Map constraints
            if hasattr(ent, "constraints") and ent.constraints:
                constraints = list(ent.constraints)
                
            # Compile traceability metadata
            # Find originating workflow dependencies
            workflows_involved = [w.workflow_name for w in spec.workflows if ent.name in w.dependencies]
            source_wf = workflows_involved[0] if workflows_involved else None
            
            # Find originating design decisions
            source_dd = [d.decision_id for d in spec.design_decisions if ent.name in d.affected_components]
            
            # Find originating business rules
            source_br = []
            for r in spec.business_rules:
                affected = [a.lower() for a in r.affected_entities]
                if ent.name.lower() in affected:
                    source_br.append(r.rule_id)
            
            traceability = TraceabilityMetadata(
                source_entity=ent.name,
                source_workflow=source_wf,
                source_design_decisions=source_dd,
                source_business_rules=source_br,
                source_ast_version=ast_version,
                compiler_phase="Database Schema Compiler"
            )
            
            tables.append(DatabaseTableDefinition(
                table_name=CanonicalNamingEngine.to_snake_case(ent.name),
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                constraints=constraints,
                indexes=[f"idx_{CanonicalNamingEngine.to_snake_case(ent.name)}_{pk}" for pk in primary_keys],
                source_entity=ent.name,
                traceability=traceability
            ))
        return tables


class APISchemaCompiler:
    @staticmethod
    def compile(spec: MasterSpecification, ast_version: str) -> List[APIEndpointDefinition]:
        endpoints = []
        
        # Build CRUD for every entity
        for ent in spec.entities:
            plural_path = get_entity_plural_path(ent.name)
            table_name = CanonicalNamingEngine.to_snake_case(ent.name)
            
            # Find trace metadata
            workflows_involved = [w.workflow_name for w in spec.workflows if ent.name in w.dependencies]
            source_wf = workflows_involved[0] if workflows_involved else None
            source_dd = [d.decision_id for d in spec.design_decisions if ent.name in d.affected_components]
            source_br = []
            for r in spec.business_rules:
                if ent.name.lower() in [a.lower() for a in r.affected_entities]:
                    source_br.append(r.rule_id)
            
            trace = TraceabilityMetadata(
                source_entity=ent.name,
                source_workflow=source_wf,
                source_design_decisions=source_dd,
                source_business_rules=source_br,
                source_ast_version=ast_version,
                compiler_phase="API Schema Compiler"
            )
            
            # 1. GET ALL
            endpoints.append(APIEndpointDefinition(
                endpoint_id=f"get_{table_name}_list",
                path=f"/api/v1/{plural_path}",
                method="GET",
                request_schema={},
                response_schema={"type": "array", "items": {"$ref": f"#/components/schemas/{ent.name}"}},
                permissions=["Admin"] + ([p.role for p in spec.permissions if f"ReadOwnProfile" in p.permissions or f"ManageLeads" in p.permissions or f"ReadInventory" in p.permissions]),
                source_entity=ent.name,
                traceability=trace
            ))
            
            # 2. GET SINGLE
            endpoints.append(APIEndpointDefinition(
                endpoint_id=f"get_{table_name}_detail",
                path=f"/api/v1/{plural_path}/{{id}}",
                method="GET",
                request_schema={},
                response_schema={"$ref": f"#/components/schemas/{ent.name}"},
                permissions=["Admin"] + ([p.role for p in spec.permissions if f"ReadOwnProfile" in p.permissions]),
                source_entity=ent.name,
                traceability=trace
            ))
            
            # 3. POST CREATE
            endpoints.append(APIEndpointDefinition(
                endpoint_id=f"create_{table_name}",
                path=f"/api/v1/{plural_path}",
                method="POST",
                request_schema={"$ref": f"#/components/schemas/{ent.name}Input"},
                response_schema={"$ref": f"#/components/schemas/{ent.name}"},
                permissions=["Admin"] + ([p.role for p in spec.permissions if f"BookClasses" in p.permissions or f"ScheduleAppointments" in p.permissions or f"EnrollCourses" in p.permissions or f"ManageLeads" in p.permissions or f"UpdateInventory" in p.permissions]),
                source_entity=ent.name,
                traceability=trace
            ))
            
            # 4. PUT UPDATE
            endpoints.append(APIEndpointDefinition(
                endpoint_id=f"update_{table_name}",
                path=f"/api/v1/{plural_path}/{{id}}",
                method="PUT",
                request_schema={"$ref": f"#/components/schemas/{ent.name}Input"},
                response_schema={"$ref": f"#/components/schemas/{ent.name}"},
                permissions=["Admin"] + ([p.role for p in spec.permissions if f"GradeStudents" in p.permissions or f"UpdateInventory" in p.permissions or f"CreateDiagnosis" in p.permissions]),
                source_entity=ent.name,
                traceability=trace
            ))
            
            # 5. DELETE
            endpoints.append(APIEndpointDefinition(
                endpoint_id=f"delete_{table_name}",
                path=f"/api/v1/{plural_path}/{{id}}",
                method="DELETE",
                request_schema={},
                response_schema={"status": "string"},
                permissions=["Admin"],
                source_entity=ent.name,
                traceability=trace
            ))
            
        # Compile workflow custom endpoints
        for wf in spec.workflows:
            wf_slug = wf.workflow_id.lower().replace(" ", "_")
            source_dd = [d.decision_id for d in spec.design_decisions if wf.workflow_name in d.affected_components]
            
            trace = TraceabilityMetadata(
                source_workflow=wf.workflow_name,
                source_design_decisions=source_dd,
                source_ast_version=ast_version,
                compiler_phase="API Schema Compiler"
            )
            
            endpoints.append(APIEndpointDefinition(
                endpoint_id=f"execute_{wf_slug}",
                path=f"/api/v1/workflows/{wf_slug}",
                method="POST",
                request_schema={"workflow_steps": wf.workflow_steps},
                response_schema={"status": "string", "execution_log": "array"},
                permissions=["Admin"] + wf.actors,
                source_entity=wf.dependencies[0] if wf.dependencies else "System",
                traceability=trace
            ))
            
        return endpoints


class UISchemaCompiler:
    @staticmethod
    def compile(spec: MasterSpecification, ast_version: str) -> List[UIViewDefinition]:
        views = []
        for wf in spec.workflows:
            # Generate component tree from steps
            components = []
            actions = []
            linked_endpoints = []
            
            # Map steps to UI components and endpoints
            for step in wf.workflow_steps:
                step_lower = step.lower()
                comp_type = "input_field"
                if "select" in step_lower or "choose" in step_lower or "fill" in step_lower or "request" in step_lower:
                    comp_type = "input_field"
                elif "verify" in step_lower or "validate" in step_lower or "log" in step_lower or "deduct" in step_lower:
                    comp_type = "detail_card"
                elif "confirm" in step_lower or "submit" in step_lower or "save" in step_lower or "convert" in step_lower or "book" in step_lower or "grade" in step_lower:
                    comp_type = "submit_button"
                elif "history" in step_lower or "list" in step_lower or "browse" in step_lower:
                    comp_type = "table_grid"
                elif "dashboard" in step_lower or "metrics" in step_lower:
                    comp_type = "chart_dashboard"
                
                components.append(UIComponent(
                    type=comp_type,
                    label=step,
                    bindings={"step_action": CanonicalNamingEngine.to_snake_case(step)}
                ))
                actions.append(CanonicalNamingEngine.to_pascal_case(step))
            
            # Find associated entity dependencies and link API paths
            for dep in wf.dependencies:
                plural = get_entity_plural_path(dep)
                linked_endpoints.append(f"GET /api/v1/{plural}")
                linked_endpoints.append(f"POST /api/v1/{plural}")
            
            # Add the workflow route execution endpoint
            wf_slug = wf.workflow_id.lower().replace(" ", "_")
            linked_endpoints.append(f"POST /api/v1/workflows/{wf_slug}")
            
            # Traceability
            source_dd = [d.decision_id for d in spec.design_decisions if wf.workflow_name in d.affected_components]
            
            trace = TraceabilityMetadata(
                source_workflow=wf.workflow_name,
                source_design_decisions=source_dd,
                source_ast_version=ast_version,
                compiler_phase="UI Schema Compiler"
            )
            
            views.append(UIViewDefinition(
                view_id=f"view_{wf.workflow_id.lower()}",
                view_name=f"{wf.workflow_name} View",
                components=components,
                actions=actions,
                required_permissions=wf.actors,
                source_workflow=wf.workflow_name,
                linked_endpoints=linked_endpoints,
                traceability=trace
            ))
        return views


class AuthSchemaCompiler:
    @staticmethod
    def compile(spec: MasterSpecification, ast_version: str) -> List[AuthRuleDefinition]:
        auth_rules = []
        
        # Build restricted action templates
        all_privileges = {"ManageAllRecords", "DeleteDatabase", "OverrideAll", "ViewAnalyticsDashboard"}
        
        for perm in spec.permissions:
            role_allowed_perms = set(perm.permissions)
            restricted = list(all_privileges.difference(role_allowed_perms))
            
            reqs = ["JWT_Token"]
            if perm.role == "Admin":
                reqs = ["JWT_Token", "MFA"]
            
            trace = TraceabilityMetadata(
                source_ast_version=ast_version,
                compiler_phase="Auth Schema Compiler"
            )
            
            auth_rules.append(AuthRuleDefinition(
                role=perm.role,
                permissions=perm.permissions,
                restricted_actions=restricted,
                authentication_requirements=reqs,
                traceability=trace
            ))
        return auth_rules


class SchemaContractEngine:
    @staticmethod
    def generate_contracts(spec: MasterSpecification, database_schema: List[DatabaseTableDefinition], api_schema: List[APIEndpointDefinition], ui_schema: List[UIViewDefinition], auth_schema: List[AuthRuleDefinition], ast_version: str) -> List[SchemaContract]:
        contracts = []
        
        # For every entity, issue a contract locking it across layers
        for ent in spec.entities:
            contract_id = f"con_entity_{ent.name.lower()}"
            generated = []
            
            # Find DB tables
            db_t = next((d.table_name for d in database_schema if d.source_entity == ent.name), None)
            if db_t:
                generated.append(f"DB_Table:{db_t}")
                
            # Find APIs
            apis = [a.endpoint_id for a in api_schema if a.source_entity == ent.name]
            for ap in apis:
                generated.append(f"API:{ap}")
                
            # Find UI Views (workflows depending on this entity)
            views = [u.view_id for u in ui_schema if ent.name in [d for d in spec.workflows if d.workflow_name == u.source_workflow][0].dependencies]
            for v in views:
                generated.append(f"UI_View:{v}")
                
            trace = TraceabilityMetadata(
                source_entity=ent.name,
                source_ast_version=ast_version,
                compiler_phase="Schema Contract Engine"
            )
            
            contracts.append(SchemaContract(
                contract_id=contract_id,
                source_ast_component=f"Entity:{ent.name}",
                generated_components=generated,
                validation_rules=[
                    f"Check DB table exists",
                    f"Check CRUD API completeness",
                    f"Check required fields match"
                ],
                traceability=trace
            ))
        return contracts


# --- CROSS-LAYER CONSISTENCY ENGINE ---

class CrossLayerConsistencyEngine:
    @classmethod
    def verify(cls, spec: MasterSpecification, bundle_db: List[DatabaseTableDefinition], bundle_api: List[APIEndpointDefinition], bundle_ui: List[UIViewDefinition], bundle_auth: List[AuthRuleDefinition], bundle_contracts: List[SchemaContract]) -> List[ConsistencyViolation]:
        violations = []
        
        entity_names = {e.name for e in spec.entities}
        db_tables = {d.table_name: d for d in bundle_db}
        api_endpoints = {a.endpoint_id: a for a in bundle_api}
        api_paths = {f"{a.method} {a.path}": a for a in bundle_api}
        ui_views = {u.view_id: u for u in bundle_ui}
        auth_rules = {au.role: au for au in bundle_auth}
        actor_names = {a.name for a in spec.actors}
        
        # 1. Entity Exists In Database
        for ent in spec.entities:
            tbl_name = CanonicalNamingEngine.to_snake_case(ent.name)
            if tbl_name not in db_tables:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_db_entity_{ent.name.lower()}",
                    layer_a="AST",
                    layer_b="Database",
                    message=f"Entity '{ent.name}' is missing in compiled database schema table definitions.",
                    severity="HIGH",
                    related_components=[f"Entity:{ent.name}"]
                ))

        # 2. Entity Exists In API
        for ent in spec.entities:
            tbl_name = CanonicalNamingEngine.to_snake_case(ent.name)
            crud_id = f"create_{tbl_name}"
            if crud_id not in api_endpoints:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_api_entity_{ent.name.lower()}",
                    layer_a="AST",
                    layer_b="API",
                    message=f"Entity '{ent.name}' is missing corresponding CRUD create endpoint '{crud_id}'.",
                    severity="HIGH",
                    related_components=[f"Entity:{ent.name}"]
                ))

        # 3. Entity Exists In UI
        for ent in spec.entities:
            # Check if any UI view source workflow lists this entity in its dependencies
            referenced = False
            for ui in bundle_ui:
                # find workflow
                wf = next((w for w in spec.workflows if w.workflow_name == ui.source_workflow), None)
                if wf and ent.name in wf.dependencies:
                    referenced = True
                    break
            if not referenced and len(spec.workflows) > 0:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_ui_entity_{ent.name.lower()}",
                    layer_a="AST",
                    layer_b="UI",
                    message=f"Entity '{ent.name}' is not bound to any compiled UI views dependencies.",
                    severity="MEDIUM",
                    related_components=[f"Entity:{ent.name}"]
                ))

        # 4. Permissions Match Auth
        for perm in spec.permissions:
            if perm.role not in auth_rules:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_auth_role_{perm.role.lower()}",
                    layer_a="AST",
                    layer_b="Auth",
                    message=f"Logical permissions role '{perm.role}' does not match any Auth rule definitions.",
                    severity="HIGH",
                    related_components=[f"Permission:{perm.role}"]
                ))
            else:
                auth = auth_rules[perm.role]
                if set(perm.permissions) != set(auth.permissions):
                    violations.append(ConsistencyViolation(
                        violation_id=f"viol_auth_perms_{perm.role.lower()}",
                        layer_a="AST",
                        layer_b="Auth",
                        message=f"Logical permissions in AST and Compiled Auth Rules mismatch for role '{perm.role}'.",
                        severity="HIGH",
                        related_components=[f"Permission:{perm.role}", f"AuthRule:{perm.role}"]
                    ))

        # 5. Workflow References Existing APIs
        for wf in spec.workflows:
            wf_slug = wf.workflow_id.lower().replace(" ", "_")
            exec_id = f"execute_{wf_slug}"
            if exec_id not in api_endpoints:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_api_workflow_{wf.workflow_id}",
                    layer_a="AST",
                    layer_b="API",
                    message=f"Workflow custom trigger API execution endpoint '{exec_id}' is missing.",
                    severity="HIGH",
                    related_components=[f"Workflow:{wf.workflow_name}"]
                ))

        # 6. Relationships Match Foreign Keys
        for rel in spec.relationships:
            # rel.source_entity, rel.target_entity
            src_tbl = CanonicalNamingEngine.to_snake_case(rel.source_entity)
            trg_tbl = CanonicalNamingEngine.to_snake_case(rel.target_entity)
            if src_tbl in db_tables:
                tbl = db_tables[src_tbl]
                # check if there is a foreign key references target_tbl
                has_fk = any(fk["references_table"] == trg_tbl for fk in tbl.foreign_keys)
                if not has_fk and trg_tbl in db_tables:
                    has_fk = any(fk["references_table"] == src_tbl for fk in db_tables[trg_tbl].foreign_keys)
                if not has_fk:
                    violations.append(ConsistencyViolation(
                        violation_id=f"viol_db_relationship_{rel.relationship_id}",
                        layer_a="AST",
                        layer_b="Database",
                        message=f"Logical relationship '{rel.relationship_id}' is missing corresponding foreign key in table '{src_tbl}'.",
                        severity="HIGH",
                        related_components=[f"Relationship:{rel.relationship_id}", f"Table:{src_tbl}"]
                    ))

        # 7. Required Fields Match Across Layers
        for ent in spec.entities:
            src_tbl = CanonicalNamingEngine.to_snake_case(ent.name)
            if src_tbl in db_tables:
                tbl = db_tables[src_tbl]
                # Compare columns with entity fields
                for col in tbl.columns:
                    field = next((f for f in ent.fields if f.name == col.name), None)
                    if field:
                        if field.required == col.is_nullable: # Mismatch if required but nullable=True
                            violations.append(ConsistencyViolation(
                                violation_id=f"viol_db_field_nullable_{ent.name.lower()}_{col.name}",
                                layer_a="AST",
                                layer_b="Database",
                                message=f"Required constraint mismatch for field '{col.name}' in entity '{ent.name}'.",
                                severity="MEDIUM",
                                related_components=[f"EntityField:{ent.name}.{col.name}", f"Column:{src_tbl}.{col.name}"]
                            ))

        # 8. UI Linked Endpoints Exist
        for ui in bundle_ui:
            for endpoint_route in ui.linked_endpoints:
                # E.g. "POST /api/v1/class-bookings"
                # Strip and verify if exists in api_paths or endpoints
                if " /" in endpoint_route:
                    method, path = endpoint_route.split(" ", 1)
                    # Handle path template substitution for checking
                    matched = False
                    for route_key, api_endpoint in api_paths.items():
                        if api_endpoint.method == method:
                            # basic placeholder check e.g., `/id` vs `{id}`
                            clean_p1 = path.replace("{id}", "").replace("{id_name}", "").rstrip("/")
                            clean_p2 = api_endpoint.path.replace("{id}", "").replace("{id_name}", "").rstrip("/")
                            if clean_p1 == clean_p2:
                                matched = True
                                break
                    if not matched:
                        violations.append(ConsistencyViolation(
                            violation_id=f"viol_ui_link_{ui.view_id}_{CanonicalNamingEngine.to_snake_case(endpoint_route)}",
                            layer_a="UI",
                            layer_b="API",
                            message=f"UI view '{ui.view_name}' links to non-existent endpoint path '{endpoint_route}'.",
                            severity="HIGH",
                            related_components=[f"UIView:{ui.view_id}", f"Route:{endpoint_route}"]
                        ))

        # 9. Auth Roles Match Permissions
        for auth_r in bundle_auth:
            if auth_r.role not in actor_names:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_auth_roles_actor_{auth_r.role.lower()}",
                    layer_a="Auth",
                    layer_b="AST",
                    message=f"Auth rule role '{auth_r.role}' does not match any defined AST actors.",
                    severity="HIGH",
                    related_components=[f"AuthRule:{auth_r.role}"]
                ))

        # 10. Traceability Exists
        for tbl in bundle_db:
            if not tbl.traceability or not tbl.traceability.source_entity:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_trace_db_{tbl.table_name}",
                    layer_a="Database",
                    layer_b="Traceability",
                    message=f"Database table '{tbl.table_name}' is missing source entity traceability metadata.",
                    severity="MEDIUM",
                    related_components=[f"Table:{tbl.table_name}"]
                ))
        for ap in bundle_api:
            if not ap.traceability or (not ap.traceability.source_entity and not ap.traceability.source_workflow):
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_trace_api_{ap.endpoint_id}",
                    layer_a="API",
                    layer_b="Traceability",
                    message=f"API endpoint '{ap.endpoint_id}' is missing source traceability metadata.",
                    severity="MEDIUM",
                    related_components=[f"APIEndpoint:{ap.endpoint_id}"]
                ))
        for ui in bundle_ui:
            if not ui.traceability or not ui.traceability.source_workflow:
                violations.append(ConsistencyViolation(
                    violation_id=f"viol_trace_ui_{ui.view_id}",
                    layer_a="UI",
                    layer_b="Traceability",
                    message=f"UI view '{ui.view_id}' is missing source workflow traceability metadata.",
                    severity="MEDIUM",
                    related_components=[f"UIView:{ui.view_id}"]
                ))

        return violations


# --- COMPILED SCHEMA BUNDLE BUILDER & REPORT ENGINE ---

class CompiledSchemaBundleBuilder:
    @staticmethod
    def compile_bundle(spec: MasterSpecification) -> CompiledSchemaBundle:
        ast_version_str = spec.metadata.get("blueprint_project_id", "v1.0")
        
        # 1. Compile layers
        db_schema = DatabaseSchemaCompiler.compile(spec, ast_version_str)
        api_schema = APISchemaCompiler.compile(spec, ast_version_str)
        ui_schema = UISchemaCompiler.compile(spec, ast_version_str)
        auth_schema = AuthSchemaCompiler.compile(spec, ast_version_str)
        
        # 2. Compile contracts
        contracts = SchemaContractEngine.generate_contracts(
            spec, db_schema, api_schema, ui_schema, auth_schema, ast_version_str
        )
        
        # 3. Perform consistency checks
        violations = CrossLayerConsistencyEngine.verify(
            spec, db_schema, api_schema, ui_schema, auth_schema, contracts
        )
        
        # 4. Generate report errors and warnings
        errors = []
        warnings = []
        
        for v in violations:
            if v.severity == "HIGH":
                errors.append(v.message)
            else:
                warnings.append(v.message)

        # 5. Compiler Validation Rules
        # Rule 9: No Duplicate Components
        seen_tables = set()
        for t in db_schema:
            if t.table_name in seen_tables:
                errors.append(f"Duplicate entity / database table '{t.table_name}' compiled.")
            seen_tables.add(t.table_name)
            
        seen_paths = set()
        for a in api_schema:
            path_key = f"{a.method} {a.path}"
            if path_key in seen_paths:
                errors.append(f"Duplicate API endpoint path '{path_key}' compiled.")
            seen_paths.add(path_key)
            
        seen_views = set()
        for u in ui_schema:
            if u.view_id in seen_views:
                errors.append(f"Duplicate UI view ID '{u.view_id}' compiled.")
            seen_views.add(u.view_id)
            
        seen_auth = set()
        for au in auth_schema:
            if au.role in seen_auth:
                errors.append(f"Duplicate Auth rule role '{au.role}' compiled.")
            seen_auth.add(au.role)

        is_valid = len(errors) == 0
        passed_count = 10 - len(violations)
        
        comp_report = SchemaCompilationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            compiled_entities=[e.name for e in spec.entities],
            compiled_workflows=[w.workflow_name for w in spec.workflows],
            compiled_permissions=[p.role for p in spec.permissions],
            compiled_relationships=[r.relationship_id for r in spec.relationships],
            consistency_checks_passed=max(0, passed_count),
            consistency_checks_failed=len(violations),
            timestamp=datetime.now().isoformat()
        )
        
        ast_ver = ASTVersion(
            version=ast_version_str,
            generated_at=spec.metadata.get("compiled_at", datetime.now().isoformat()),
            compiler_phase="Phase 5 Schema Generation Engine",
            source_ast_version=ast_version_str
        )
        
        # 6. Generate CompilationArtifacts
        artifacts = []
        for t in db_schema:
            artifacts.append(CompilationArtifact(
                artifact_id=f"art_db_{t.table_name}",
                artifact_type="database_table",
                source_component=f"Entity:{t.source_entity}",
                generated_component=f"Table:{t.table_name}",
                ast_version=ast_version_str,
                traceability=t.traceability
            ))
        for a in api_schema:
            source = f"Entity:{a.source_entity}" if a.traceability.source_entity else f"Workflow:{a.traceability.source_workflow}"
            artifacts.append(CompilationArtifact(
                artifact_id=f"art_api_{a.endpoint_id}",
                artifact_type="api_endpoint",
                source_component=source,
                generated_component=f"Endpoint:{a.endpoint_id}",
                ast_version=ast_version_str,
                traceability=a.traceability
            ))
        for u in ui_schema:
            artifacts.append(CompilationArtifact(
                artifact_id=f"art_ui_{u.view_id}",
                artifact_type="ui_view",
                source_component=f"Workflow:{u.source_workflow}",
                generated_component=f"View:{u.view_id}",
                ast_version=ast_version_str,
                traceability=u.traceability
            ))
        for au in auth_schema:
            artifacts.append(CompilationArtifact(
                artifact_id=f"art_auth_{au.role.lower()}",
                artifact_type="auth_rule",
                source_component=f"Actor:{au.role}",
                generated_component=f"AuthRule:{au.role}",
                ast_version=ast_version_str,
                traceability=au.traceability
            ))
        
        return CompiledSchemaBundle(
            database_schema=db_schema,
            api_schema=api_schema,
            ui_schema=ui_schema,
            auth_schema=auth_schema,
            contracts=contracts,
            consistency_report=violations,
            ast_version=ast_ver,
            compilation_report=comp_report,
            artifacts=artifacts
        )

