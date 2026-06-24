import logging
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime

from core.naming import CanonicalNamingEngine
from stages.stage4_system import MasterSpecification, EntityDefinition, WorkflowDefinition, PermissionDefinition, RelationshipDefinition
from stages.stage5_schema import (
    CompiledSchemaBundle, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, TraceabilityMetadata,
    CompilationArtifact, CrossLayerConsistencyEngine
)
from stages.stage3_recommend import ApprovedBlueprint

logger = logging.getLogger(__name__)

# --- VALIDATION ENGINE DATA MODELS ---

class ValidationError(BaseModel):
    error_id: str = Field(..., description="Unique error identifier e.g., val_err_001")
    error_code: str = Field(..., description="Machine-readable error type e.g., DB_MISSING_PK")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    layer: Literal["Database", "API", "UI", "Auth", "Workflow", "Coverage", "Graph", "Traceability", "Contract", "Cross-Layer"]
    component: str = Field(..., description="Name of the component under audit")
    message: str = Field(..., description="Detailed diagnostic error message")
    source_component: str = Field(..., description="Source AST component trace e.g., Entity:Member")
    repair_hint: str = Field(..., description="Surgical prescription to fix this issue")


class ValidationReport(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    validated_components: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- VALIDATION ENGINE ---

class ValidationEngine:
    @staticmethod
    def validate(bundle: CompiledSchemaBundle, spec: MasterSpecification, blueprint: Optional[ApprovedBlueprint] = None) -> ValidationReport:
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        validated_components: List[str] = []
        
        # Helper to register validation errors
        err_counter = 1
        def log_issue(code: str, severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"], layer: str, component: str, message: str, source_component: str, hint: str):
            nonlocal err_counter
            issue = ValidationError(
                error_id=f"val_err_{err_counter:03d}",
                error_code=code,
                severity=severity,
                layer=layer,
                component=component,
                message=message,
                source_component=source_component,
                repair_hint=hint
            )
            if severity in ("CRITICAL", "HIGH"):
                errors.append(issue)
            else:
                warnings.append(issue)
            err_counter += 1

        # Mappings
        actor_names = {a.name for a in spec.actors}
        entity_names = {e.name for e in spec.entities}
        workflow_names = {w.workflow_name for w in spec.workflows}
        
        db_tables = {t.table_name: t for t in bundle.database_schema}
        api_endpoints = {a.endpoint_id: a for a in bundle.api_schema}
        api_paths = {f"{a.method} {a.path}": a for a in bundle.api_schema}
        ui_views = {v.view_id: v for v in bundle.ui_schema}
        auth_rules = {au.role: au for au in bundle.auth_schema}
        contracts = {c.contract_id: c for c in bundle.contracts}
        artifacts = {art.artifact_id: art for art in bundle.artifacts}

        # --- 1. JSON & REQUIRED FIELDS VALIDATION ---
        for tbl in bundle.database_schema:
            validated_components.append(f"Table:{tbl.table_name}")
            if not tbl.table_name:
                log_issue("DB_MISSING_NAME", "CRITICAL", "Database", "Table:unknown", "Database table is missing a name.", "AST:Entity", "Ensure CanonicalNamingEngine sanitizes entity name correctly.")
            if not tbl.columns:
                log_issue("DB_EMPTY_TABLE", "HIGH", "Database", f"Table:{tbl.table_name}", f"Database table '{tbl.table_name}' contains no columns.", f"Entity:{tbl.source_entity}", "Add default 'id' primary key column.")

        for ap in bundle.api_schema:
            validated_components.append(f"APIEndpoint:{ap.endpoint_id}")
            if not ap.path or not ap.method:
                log_issue("API_INVALID_ROUTE", "CRITICAL", "API", f"APIEndpoint:{ap.endpoint_id}", "API endpoint has missing path or method parameters.", f"Entity:{ap.source_entity}", "Enforce REST compliance path definitions.")

        # --- 2. DATABASE VALIDATOR ---
        for tbl in bundle.database_schema:
            # Check Primary Key Exists
            if not tbl.primary_keys:
                log_issue("DB_MISSING_PK", "CRITICAL", "Database", f"Table:{tbl.table_name}", f"Table '{tbl.table_name}' is missing a primary key.", f"Entity:{tbl.source_entity}", f"Add a column named 'id' with type 'string' and is_key=True on Entity '{tbl.source_entity}'.")
            
            # Check Foreign Keys point to valid tables/columns
            for fk in tbl.foreign_keys:
                ref_tbl = fk.get("references_table")
                ref_col = fk.get("references_column")
                col_name = fk.get("column")
                
                if ref_tbl not in db_tables:
                    log_issue("DB_INVALID_FK", "CRITICAL", "Database", f"Table:{tbl.table_name}", f"Table '{tbl.table_name}' foreign key '{col_name}' points to non-existent table '{ref_tbl}'.", f"Entity:{tbl.source_entity}", f"Verify relationship targets. Target entity for relationship must exist in AST.")
                else:
                    target_tbl = db_tables[ref_tbl]
                    if ref_col not in target_tbl.primary_keys and not any(c.name == ref_col for c in target_tbl.columns):
                        log_issue("DB_INVALID_FK_COLUMN", "CRITICAL", "Database", f"Table:{tbl.table_name}", f"Table '{tbl.table_name}' foreign key '{col_name}' points to invalid column '{ref_col}' on table '{ref_tbl}'.", f"Entity:{tbl.source_entity}", f"Change references configuration to point to primary key, e.g. '{ref_tbl}.id'.")

            # Check relationships are preserved
            for rel in spec.relationships:
                if CanonicalNamingEngine.to_snake_case(rel.source_entity) == tbl.table_name:
                    trg_tbl = CanonicalNamingEngine.to_snake_case(rel.target_entity)
                    has_fk = any(fk.get("references_table") == trg_tbl for fk in tbl.foreign_keys)
                    if not has_fk and trg_tbl in db_tables:
                        has_fk = any(fk.get("references_table") == tbl.table_name for fk in db_tables[trg_tbl].foreign_keys)
                    if not has_fk:
                        log_issue("DB_BROKEN_RELATIONSHIP", "HIGH", "Database", f"Table:{tbl.table_name}", f"Logical relationship '{rel.relationship_id}' is missing a compiled foreign key column in table '{tbl.table_name}'.", f"Relationship:{rel.relationship_id}", f"Add a relationship field on entity '{rel.source_entity}' referencing '{rel.target_entity}.id'.")

        # Check duplicate tables
        seen_tables = set()
        for t in bundle.database_schema:
            if t.table_name in seen_tables:
                log_issue("DB_DUPLICATE_TABLE", "CRITICAL", "Database", f"Table:{t.table_name}", f"Duplicate database table name '{t.table_name}' compiled.", f"Entity:{t.source_entity}", "Ensure all entity names are unique in AST.")
            seen_tables.add(t.table_name)

        # --- 3. API VALIDATOR ---
        seen_endpoints = set()
        for ap in bundle.api_schema:
            route_key = f"{ap.method} {ap.path}"
            if route_key in seen_endpoints:
                log_issue("API_DUPLICATE_ENDPOINT", "CRITICAL", "API", f"APIEndpoint:{ap.endpoint_id}", f"Duplicate API endpoint path '{route_key}' compiled.", f"Entity:{ap.source_entity}", "Ensure custom route paths are unique.")
            seen_endpoints.add(route_key)
            
            # Referenced entity exists
            if ap.source_entity != "System" and ap.source_entity not in entity_names:
                log_issue("API_UNKNOWN_ENTITY", "HIGH", "API", f"APIEndpoint:{ap.endpoint_id}", f"API endpoint '{ap.endpoint_id}' references non-existent AST entity '{ap.source_entity}'.", f"Entity:{ap.source_entity}", "Expose endpoints only for valid AST entities.")

            # Validate allowed permissions
            for role in ap.permissions:
                if role != "Admin" and role not in actor_names:
                    log_issue("API_INVALID_ROLE", "HIGH", "API", f"APIEndpoint:{ap.endpoint_id}", f"Endpoint permissions allow role '{role}' which is not in AST actors directory.", f"Entity:{ap.source_entity}", "Only assign endpoint route permissions to defined AST actors.")

        # --- 4. UI VALIDATOR ---
        seen_views = set()
        for ui in bundle.ui_schema:
            validated_components.append(f"UIView:{ui.view_id}")
            if ui.view_id in seen_views:
                log_issue("UI_DUPLICATE_VIEW", "CRITICAL", "UI", f"UIView:{ui.view_id}", f"Duplicate UI view ID '{ui.view_id}' compiled.", f"Workflow:{ui.source_workflow}", "Configure unique workflow names.")
            seen_views.add(ui.view_id)
            
            # Check linked_endpoints exist in API schema
            for endpoint_route in ui.linked_endpoints:
                if " /" in endpoint_route:
                    method, path = endpoint_route.split(" ", 1)
                    matched = False
                    for route_key, api_endpoint in api_paths.items():
                        if api_endpoint.method == method:
                            clean_p1 = path.replace("{id}", "").rstrip("/")
                            clean_p2 = api_endpoint.path.replace("{id}", "").rstrip("/")
                            if clean_p1 == clean_p2:
                                matched = True
                                break
                    if not matched:
                        log_issue("UI_BROKEN_ENDPOINT", "HIGH", "UI", f"UIView:{ui.view_id}", f"UI view '{ui.view_name}' links to non-existent endpoint path '{endpoint_route}'.", f"Workflow:{ui.source_workflow}", f"Compile custom REST endpoint for path '{path}' with method '{method}'.")

            # Check view permissions match actor permissions
            for role in ui.required_permissions:
                if role not in actor_names:
                    log_issue("UI_INVALID_ROLE", "HIGH", "UI", f"UIView:{ui.view_id}", f"UI view '{ui.view_name}' required permissions lists undefined role '{role}'.", f"Workflow:{ui.source_workflow}", "Map view access rights strictly to defined AST actors.")

            # Check view components are valid
            if not ui.components:
                log_issue("UI_INVALID_BINDING", "MEDIUM", "UI", f"UIView:{ui.view_id}", f"UI view '{ui.view_name}' is compiled empty with no input components.", f"Workflow:{ui.source_workflow}", "Ensure workflow steps exist to compile views.")

        # --- 5. AUTH VALIDATOR ---
        seen_roles = set()
        for au in bundle.auth_schema:
            validated_components.append(f"AuthRule:{au.role}")
            if au.role in seen_roles:
                log_issue("AUTH_DUPLICATE_ROLE", "CRITICAL", "Auth", f"AuthRule:{au.role}", f"Duplicate Auth rule role '{au.role}' compiled.", f"Actor:{au.role}", "Actors list must contain unique roles.")
            seen_roles.add(au.role)
            
            if au.role not in actor_names:
                log_issue("AUTH_INVALID_ROLE", "CRITICAL", "Auth", f"AuthRule:{au.role}", f"Auth rule role '{au.role}' is not a defined AST actor.", f"Actor:{au.role}", "Auth rule role must match defined AST actor.")

            # Validate restricted actions consistency
            for action in au.permissions:
                if "ManageAll" in action and "ManageAll" in au.restricted_actions:
                    log_issue("AUTH_INCONSISTENT_RESTRICTION", "HIGH", "Auth", f"AuthRule:{au.role}", f"Role '{au.role}' has conflicting permissions: action is both allowed and restricted.", f"Actor:{au.role}", "Remove permission conflict from permission mapping.")

        # --- 6. WORKFLOW VALIDATOR ---
        for wf in spec.workflows:
            validated_components.append(f"Workflow:{wf.workflow_name}")
            
            # Actors exist
            for actor in wf.actors:
                if actor not in actor_names:
                    log_issue("WORKFLOW_MISSING_ACTOR", "CRITICAL", "Workflow", f"Workflow:{wf.workflow_name}", f"Workflow '{wf.workflow_name}' references non-existent actor '{actor}'.", f"Workflow:{wf.workflow_name}", "Map workflow actors directly to defined AST actors.")
                    
            # Entities exist
            for dep in wf.dependencies:
                if dep not in entity_names:
                    log_issue("WORKFLOW_MISSING_ENTITY", "CRITICAL", "Workflow", f"Workflow:{wf.workflow_name}", f"Workflow '{wf.workflow_name}' depends on non-existent entity '{dep}'.", f"Workflow:{wf.workflow_name}", "Expose workflow entities in entity definitions list.")

            # Check for circular workflow dependencies
            visited = {}
            adj = {}
            for w in spec.workflows:
                normalized_name = w.workflow_name.lower().replace(" ", "")
                deps = [d.lower().replace(" ", "") for d in getattr(w, "workflow_dependencies", [])]
                adj[normalized_name] = deps

            def detect_cycle(node):
                visited[node] = 0
                for neighbor in adj.get(node, []):
                    if neighbor in adj:
                        if neighbor not in visited:
                            if detect_cycle(neighbor):
                                return True
                        elif visited[neighbor] == 0:
                            return True
                visited[node] = 1
                return False

            norm_name = wf.workflow_name.lower().replace(" ", "")
            if detect_cycle(norm_name):
                log_issue("WORKFLOW_CIRCULAR_DEP", "CRITICAL", "Workflow", f"Workflow:{wf.workflow_name}", f"Circular workflow dependency detected starting at '{wf.workflow_name}'.", f"Workflow:{wf.workflow_name}", "Decouple workflow steps to form a strict DAG flow.")

            # Check Workflow Missing Steps (WORKFLOW_MISSING_STEP)
            wf_name_lower = wf.workflow_name.lower()
            steps_lower = [s.lower() for s in wf.workflow_steps]
            if "registration" in wf_name_lower:
                if not any("verify" in s or "verification" in s for s in steps_lower):
                    log_issue(
                        code="WORKFLOW_MISSING_STEP",
                        severity="HIGH",
                        layer="Workflow",
                        component=f"Workflow:{wf.workflow_name}",
                        message=f"Workflow '{wf.workflow_name}' is missing a verification step.",
                        source_component=f"Workflow:{wf.workflow_name}",
                        hint="Add 'Verification Step' to workflow steps."
                    )

        # --- 7. REQUIREMENT COVERAGE VALIDATOR ---
        if blueprint:
            for feat in blueprint.features:
                # Feature must exist somewhere: as a compiled table, endpoint, view, or workflow
                represented = False
                feat_snake = CanonicalNamingEngine.to_snake_case(feat.name)
                
                # Check DB table
                if feat_snake in db_tables:
                    represented = True
                # Check API CRUD or trigger
                if any(feat_snake in ap.endpoint_id for ap in bundle.api_schema):
                    represented = True
                # Check UI view
                if any(feat_snake in ui.view_id for ui in bundle.ui_schema):
                    represented = True
                # Check Workflow name
                if any(feat_snake in wf.workflow_id for wf in spec.workflows):
                    represented = True
                    
                if not represented:
                    log_issue("COVERAGE_LOSS", "HIGH", "Coverage", f"Feature:{feat.name}", f"Feature '{feat.name}' was approved in blueprint but lost during schema compilation.", f"Feature:{feat.name}", "Ensure EntityDiscoveryEngine or WorkflowDesigner exposes structural components matching this feature.")

        # --- 8. TRACEABILITY VALIDATOR ---
        for tbl in bundle.database_schema:
            if not tbl.traceability or not tbl.traceability.source_entity:
                log_issue("TRACEABILITY_LOST", "MEDIUM", "Traceability", f"Table:{tbl.table_name}", f"Database table '{tbl.table_name}' has missing source traceability metadata.", f"Table:{tbl.table_name}", "Add TraceabilityMetadata with source_entity target.")
                
            # Verify CompilationArtifact exists and matches source
            has_artifact = False
            for art in bundle.artifacts:
                if art.artifact_type == "database_table" and art.generated_component == f"Table:{tbl.table_name}":
                    has_artifact = True
                    if art.source_component != f"Entity:{tbl.source_entity}":
                        log_issue("TRACEABILITY_MISMATCH", "HIGH", "Traceability", f"Table:{tbl.table_name}", f"CompilationArtifact source mapping mismatch for table '{tbl.table_name}': got '{art.source_component}', expected 'Entity:{tbl.source_entity}'", f"Table:{tbl.table_name}", "Map compilation artifact source component back to AST Entity name.")
                    break
            if not has_artifact:
                log_issue("TRACEABILITY_MISSING_ARTIFACT", "HIGH", "Traceability", f"Table:{tbl.table_name}", f"Database table '{tbl.table_name}' has no registered CompilationArtifact in schema bundle.", f"Table:{tbl.table_name}", "Instruct bundle compiler to register a CompilationArtifact for this table.")

        for ap in bundle.api_schema:
            if not ap.traceability or (not ap.traceability.source_entity and not ap.traceability.source_workflow):
                log_issue("TRACEABILITY_LOST", "MEDIUM", "Traceability", f"APIEndpoint:{ap.endpoint_id}", f"API endpoint '{ap.endpoint_id}' has missing source traceability metadata.", f"APIEndpoint:{ap.endpoint_id}", "Add TraceabilityMetadata details.")
                
            has_artifact = False
            for art in bundle.artifacts:
                if art.artifact_type == "api_endpoint" and art.generated_component == f"Endpoint:{ap.endpoint_id}":
                    has_artifact = True
                    break
            if not has_artifact:
                log_issue("TRACEABILITY_MISSING_ARTIFACT", "HIGH", "Traceability", f"APIEndpoint:{ap.endpoint_id}", f"API endpoint '{ap.endpoint_id}' has no registered CompilationArtifact.", f"APIEndpoint:{ap.endpoint_id}", "Register a CompilationArtifact for this endpoint.")

        for ui in bundle.ui_schema:
            if not ui.traceability or not ui.traceability.source_workflow:
                log_issue("TRACEABILITY_LOST", "MEDIUM", "Traceability", f"UIView:{ui.view_id}", f"UI view '{ui.view_id}' has missing source traceability metadata.", f"UIView:{ui.view_id}", "Add TraceabilityMetadata source_workflow.")
                
            has_artifact = False
            for art in bundle.artifacts:
                if art.artifact_type == "ui_view" and art.generated_component == f"View:{ui.view_id}":
                    has_artifact = True
                    break
            if not has_artifact:
                log_issue("TRACEABILITY_MISSING_ARTIFACT", "HIGH", "Traceability", f"UIView:{ui.view_id}", f"UI view '{ui.view_id}' has no registered CompilationArtifact.", f"UIView:{ui.view_id}", "Register a CompilationArtifact for this view.")

        for au in bundle.auth_schema:
            has_artifact = False
            for art in bundle.artifacts:
                if art.artifact_type == "auth_rule" and art.generated_component == f"AuthRule:{au.role}":
                    has_artifact = True
                    break
            if not has_artifact:
                log_issue("TRACEABILITY_MISSING_ARTIFACT", "HIGH", "Traceability", f"AuthRule:{au.role}", f"Auth rule '{au.role}' has no registered CompilationArtifact.", f"AuthRule:{au.role}", "Register a CompilationArtifact for this auth rule.")

        # --- 9. CONTRACT VALIDATOR ---
        for contract in bundle.contracts:
            validated_components.append(f"Contract:{contract.contract_id}")
            if not contract.generated_components:
                log_issue("CONTRACT_BROKEN", "HIGH", "Contract", f"Contract:{contract.contract_id}", f"Contract '{contract.contract_id}' lists zero generated schema components.", f"Contract:{contract.contract_id}", "Sustain mappings between logical components and physical outputs in the bundle.")
            
            # Check target references exist
            for gen in contract.generated_components:
                comp_type, name = gen.split(":", 1)
                if comp_type == "DB_Table" and name not in db_tables:
                    log_issue("CONTRACT_INVALID_REF", "HIGH", "Contract", f"Contract:{contract.contract_id}", f"Contract '{contract.contract_id}' references non-existent database table '{name}'.", f"Contract:{contract.contract_id}", "Map contract target components strictly to compiled schemas.")
                elif comp_type == "API" and name not in api_endpoints:
                    log_issue("CONTRACT_INVALID_REF", "HIGH", "Contract", f"Contract:{contract.contract_id}", f"Contract '{contract.contract_id}' references non-existent API endpoint '{name}'.", f"Contract:{contract.contract_id}", "Map contract target components strictly to compiled schemas.")
                elif comp_type == "UI_View" and name not in ui_views:
                    log_issue("CONTRACT_INVALID_REF", "HIGH", "Contract", f"Contract:{contract.contract_id}", f"Contract '{contract.contract_id}' references non-existent UI view '{name}'.", f"Contract:{contract.contract_id}", "Map contract target components strictly to compiled schemas.")

        # --- 10. GRAPH VALIDATOR ---
        # Read MasterSpecification graph to verify system design dependencies
        if spec.graph:
            nodes_map = {n["id"]: n for n in spec.graph.nodes}
            # Check for broken references in edges
            for edge in spec.graph.edges:
                src = edge["source"]
                trg = edge["target"]
                edge_type = edge["type"]
                if src not in nodes_map:
                    log_issue("GRAPH_BROKEN_EDGE", "HIGH", "Graph", f"GraphEdge:{src}->{trg}", f"Graph edge of type '{edge_type}' references non-existent source node '{src}'.", f"GraphNode:{src}", "Verify SystemDesignGraph nodes registry includes all actors, entities, and workflows.")
                if trg not in nodes_map:
                    log_issue("GRAPH_BROKEN_EDGE", "HIGH", "Graph", f"GraphEdge:{src}->{trg}", f"Graph edge of type '{edge_type}' references non-existent target node '{trg}'.", f"GraphNode:{trg}", "Verify SystemDesignGraph nodes registry includes all actors, entities, and workflows.")

            # Check for orphan entities (entities with no relations or execution triggers)
            entity_nodes = {n["id"] for n in spec.graph.nodes if n["type"] == "entity"}
            connected_nodes = set()
            for edge in spec.graph.edges:
                connected_nodes.add(edge["source"])
                connected_nodes.add(edge["target"])
                
            for ent in entity_nodes:
                if ent not in connected_nodes:
                    log_issue("GRAPH_ORPHAN_ENTITY", "MEDIUM", "Graph", f"GraphNode:{ent}", f"Orphan Entity node '{ent}' has no relations or workflow triggers connected in system design graph.", f"Entity:{ent}", "Map relationships or bind this entity as a workflow dependency.")

        # --- 11. CROSS-LAYER CONSISTENCY VALIDATOR ---
        consistency_violations = CrossLayerConsistencyEngine.verify(
            spec, bundle.database_schema, bundle.api_schema, bundle.ui_schema, bundle.auth_schema, bundle.contracts
        )
        for viol in consistency_violations:
            log_issue(
                code=f"CONSISTENCY_{viol.layer_a.upper()}_{viol.layer_b.upper()}",
                severity=viol.severity,
                layer="Cross-Layer",
                component=viol.violation_id,
                message=viol.message,
                source_component=viol.related_components[0] if viol.related_components else "Cross-Layer Engine",
                hint="Audit field schema names and types across DB, API, UI, and Auth compiler definitions."
            )

        # Check Required Field Mismatch (REQUIRED_FIELD_MISMATCH)
        for tbl in bundle.database_schema:
            entity_name = tbl.source_entity
            table_name = tbl.table_name
            create_ep = api_endpoints.get(f"create_{table_name}")
            if create_ep and create_ep.request_schema and "properties" in create_ep.request_schema:
                props = create_ep.request_schema["properties"]
                for col in tbl.columns:
                    if col.is_primary_key:
                        continue
                    if not col.is_nullable and col.name not in props:
                        log_issue(
                            code="REQUIRED_FIELD_MISMATCH",
                            severity="HIGH",
                            layer="Cross-Layer",
                            component=f"APIEndpoint:{create_ep.endpoint_id}",
                            message=f"Required database column '{col.name}' is missing in API request schema properties.",
                            source_component=f"EntityField:{entity_name}.{col.name}",
                            hint=f"Add field '{col.name}' to API request schema properties."
                        )

        # Build validation report metrics
        critical_c = len([e for e in errors if e.severity == "CRITICAL"])
        high_c = len([e for e in errors if e.severity == "HIGH"])
        medium_c = len([w for w in warnings if w.severity == "MEDIUM"])
        low_c = len([w for w in warnings if w.severity == "LOW"])
        is_valid = len(errors) == 0

        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            critical_count=critical_c,
            high_count=high_c,
            medium_count=medium_c,
            low_count=low_c,
            validated_components=list(set(validated_components)),
            timestamp=datetime.now().isoformat()
        )
