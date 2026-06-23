import logging
import json
import os
import time
import copy
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any, Tuple, Union

from core.naming import CanonicalNamingEngine
from stages.stage3_recommend import ApprovedBlueprint, RecommendedActor, RecommendedFeature, RecommendedWorkflow, RecommendedPermission
from stages.stage4_system import (
    MasterSpecification, EntityDefinition, RelationshipDefinition, WorkflowDefinition,
    PermissionDefinition, BusinessRuleDefinition, Actor, MasterSpecificationBuilder
)
from stages.stage5_schema import (
    CompiledSchemaBundle, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, TraceabilityMetadata,
    CompilationArtifact, ColumnDefinition, CompiledSchemaBundleBuilder, get_entity_plural_path
)
from stages.stage6_validate import ValidationEngine, ValidationError, ValidationReport
from stages.stage7_repair import RepairEngine, RepairReport
from stages.stage8_execution import ExecutionSimulator, ExecutionSimulationReport, DatabaseSimulator, StateTransitionRule

logger = logging.getLogger(__name__)

# --- PHASE 9 DATA MODELS ---

class RequirementChangeRequest(BaseModel):
    change_id: str
    change_type: Literal[
        "ADD_FEATURE", "REMOVE_FEATURE", "MODIFY_FEATURE",
        "ADD_ACTOR", "REMOVE_ACTOR", "MODIFY_WORKFLOW",
        "MODIFY_PERMISSION", "MODIFY_BUSINESS_RULE",
        "ADD_ENTITY", "REMOVE_ENTITY"
    ]
    description: str
    priority: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)


class ChangeSet(BaseModel):
    added: List[Dict[str, Any]] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    modified: List[Dict[str, Any]] = Field(default_factory=list)
    unchanged: List[str] = Field(default_factory=list)


class ChangeDependencyGraph(BaseModel):
    changed_component: str = ""
    directly_affected: List[str] = Field(default_factory=list)
    indirectly_affected: List[str] = Field(default_factory=list)
    dependency_depth: int = 0
    # For backwards compatibility:
    direct_dependencies: List[str] = Field(default_factory=list)
    indirect_dependencies: List[str] = Field(default_factory=list)


class ChangeImpactScore(BaseModel):
    entities_changed: int = 0
    workflows_changed: int = 0
    apis_changed: int = 0
    permissions_changed: int = 0
    business_rules_changed: int = 0
    score: float = 0.0
    impact_level: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"


class ChangeComplexityScore(BaseModel):
    score: float
    complexity_level: Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]


class ImpactAnalysisReport(BaseModel):
    affected_components: List[str] = Field(default_factory=list)
    unaffected_components: List[str] = Field(default_factory=list)
    estimated_effort: str
    impact_score: ChangeImpactScore
    dependency_graph: ChangeDependencyGraph = Field(default_factory=ChangeDependencyGraph)


class ChangeConflict(BaseModel):
    conflict_id: str
    conflict_type: Literal["ENTITY_REMOVAL", "WORKFLOW_DEPENDENCY", "PERMISSION", "BUSINESS_RULE"]
    message: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]


class ConflictDetectionReport(BaseModel):
    is_valid: bool
    conflicts: List[ChangeConflict] = Field(default_factory=list)


class ChangeRiskAssessment(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    affected_components: List[str] = Field(default_factory=list)
    affected_workflows: List[str] = Field(default_factory=list)
    affected_entities: List[str] = Field(default_factory=list)
    validation_risk: float = 0.0
    repair_risk: float = 0.0
    simulation_risk: float = 0.0
    overall_risk_score: float = 0.0


class RequirementVersion(BaseModel):
    version_id: str
    parent_version: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    change_summary: str


class RollbackPoint(BaseModel):
    version_id: str
    blueprint_snapshot: Dict[str, Any]
    specification_snapshot: Dict[str, Any]
    schema_snapshot: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ChangeDiff(BaseModel):
    component: str
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    change_reason: str


class ChangeEffectivenessReport(BaseModel):
    components_modified: List[str] = Field(default_factory=list)
    components_preserved: List[str] = Field(default_factory=list)
    validation_passed: bool
    repair_required: bool
    simulation_passed: bool
    rollback_required: bool
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    impact_level: Literal["LOW", "MEDIUM", "HIGH"]
    complexity_level: Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]


class EvolutionTimelineEntry(BaseModel):
    version_id: str
    change_summary: str
    impact_level: Literal["LOW", "MEDIUM", "HIGH"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    # Backwards compatibility:
    parent_version: Optional[str] = None
    change_id: Optional[str] = None
    change_type: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None


class EvolutionTimeline(BaseModel):
    entries: List[EvolutionTimelineEntry] = Field(default_factory=list)


class RequirementChangeReport(BaseModel):
    change_id: str
    version_info: RequirementVersion
    diffs: List[ChangeDiff] = Field(default_factory=list)
    impact_report: ImpactAnalysisReport
    risk_assessment: ChangeRiskAssessment
    effectiveness: ChangeEffectivenessReport
    conflicts_report: ConflictDetectionReport
    updated_blueprint: Optional[ApprovedBlueprint] = None
    updated_spec: Optional[MasterSpecification] = None
    updated_bundle: Optional[CompiledSchemaBundle] = None


# --- 1. CHANGE DETECTOR ---

class ChangeDetector:
    @staticmethod
    def detect_changes(blueprint: ApprovedBlueprint, request: RequirementChangeRequest) -> ChangeSet:
        added = []
        removed = []
        modified = []
        unchanged = []

        change_type = request.change_type
        payload = request.payload

        if change_type == "ADD_FEATURE":
            feat_name = payload.get("name")
            added.append({"type": "feature", "name": feat_name, "details": payload})
            
        elif change_type == "REMOVE_FEATURE":
            feat_name = payload.get("name")
            removed.append(feat_name)
            
        elif change_type == "MODIFY_FEATURE":
            feat_name = payload.get("name")
            modified.append({"type": "feature", "name": feat_name, "details": payload})

        elif change_type == "ADD_ACTOR":
            actor_name = payload.get("name")
            added.append({"type": "actor", "name": actor_name, "details": payload})

        elif change_type == "REMOVE_ACTOR":
            actor_name = payload.get("name")
            removed.append(actor_name)

        elif change_type == "MODIFY_WORKFLOW":
            wf_name = payload.get("name")
            modified.append({"type": "workflow", "name": wf_name, "details": payload})

        elif change_type == "MODIFY_PERMISSION":
            role = payload.get("role")
            modified.append({"type": "permission", "role": role, "details": payload})

        elif change_type == "MODIFY_BUSINESS_RULE":
            rule_id = payload.get("rule_id")
            modified.append({"type": "business_rule", "rule_id": rule_id, "details": payload})

        elif change_type == "ADD_ENTITY":
            ent_name = payload.get("name")
            added.append({"type": "entity", "name": ent_name, "details": payload})

        elif change_type == "REMOVE_ENTITY":
            ent_name = payload.get("name")
            removed.append(ent_name)

        # Catalog unchanged elements in blueprint
        for act in blueprint.actors:
            if act.name not in removed and not any(m.get("name") == act.name for m in modified):
                unchanged.append(f"Actor:{act.name}")
        for feat in blueprint.features:
            if feat.name not in removed and not any(m.get("name") == feat.name for m in modified):
                unchanged.append(f"Feature:{feat.name}")
        for wf in blueprint.workflows:
            if wf.name not in removed and not any(m.get("name") == wf.name for m in modified):
                unchanged.append(f"Workflow:{wf.name}")
        for perm in blueprint.permissions:
            if perm.actor not in removed and not any(m.get("role") == perm.actor for m in modified):
                unchanged.append(f"Permission:{perm.actor}")

        return ChangeSet(added=added, removed=removed, modified=modified, unchanged=unchanged)


# --- 2. CHANGE DEPENDENCY GRAPH BUILDER ---

class ChangeDependencyGraphBuilder:
    @staticmethod
    def build_graph(
        spec: MasterSpecification,
        bundle: CompiledSchemaBundle,
        changes: ChangeSet
    ) -> ChangeDependencyGraph:
        direct = set()
        indirect = set()
        depth = 0

        # Traverse target items to build dependency maps
        target_names = []
        for a in changes.added:
            target_names.append(a.get("name") or a.get("role") or a.get("rule_id"))
        for r in changes.removed:
            target_names.append(r)
        for m in changes.modified:
            target_names.append(m.get("name") or m.get("role") or m.get("rule_id"))

        target_names = [t for t in target_names if t]

        # 1. Direct dependencies: scan tables with FKs pointing to target or endpoints calling target
        for name in target_names:
            snake = CanonicalNamingEngine.to_snake_case(name)
            pascal = CanonicalNamingEngine.to_pascal_case(name)
            
            # Entities referencing the target entity (direct FK references)
            for tbl in bundle.database_schema:
                for fk in tbl.foreign_keys:
                    if fk.get("references_table") == snake:
                        direct.add(f"Table:{tbl.table_name}")
                        depth = max(depth, 1)

            # Workflows referencing the target entity
            for wf in spec.workflows:
                if pascal in wf.dependencies or name in wf.actors:
                    direct.add(f"Workflow:{wf.workflow_name}")
                    depth = max(depth, 1)

            # API Endpoints linked to this entity
            for ap in bundle.api_schema:
                if ap.source_entity == pascal:
                    direct.add(f"API:{ap.endpoint_id}")
                    depth = max(depth, 1)

            # UI view components referencing target endpoint
            for ui in bundle.ui_schema:
                for comp in ui.components:
                    bind = comp.bindings.get("endpoint_id")
                    if bind and snake in bind:
                        direct.add(f"UI:{ui.view_id}")
                        depth = max(depth, 1)

        # 2. Indirect dependencies: scan items depending on direct dependencies (transitive closures)
        for d in list(direct):
            d_name = d.split(":")[-1]
            # If d is a table, check tables depending on it
            if d.startswith("Table:"):
                for tbl in bundle.database_schema:
                    for fk in tbl.foreign_keys:
                        if fk.get("references_table") == d_name:
                            indirect.add(f"Table:{tbl.table_name}")
                            depth = max(depth, 2)
            # If d is a workflow, check UI views linked to it
            elif d.startswith("Workflow:"):
                for ui in bundle.ui_schema:
                    for comp in ui.components:
                        actions = comp.bindings.get("actions", [])
                        if any(d_name.lower() in str(act).lower() for act in actions):
                            indirect.add(f"UI:{ui.view_id}")
                            depth = max(depth, 2)

        changed_comp = target_names[0] if target_names else "none"
        return ChangeDependencyGraph(
            changed_component=changed_comp,
            directly_affected=list(direct),
            indirectly_affected=list(indirect),
            dependency_depth=depth,
            direct_dependencies=list(direct),
            indirect_dependencies=list(indirect)
        )


# --- 3. CONFLICT DETECTION ENGINE ---

class ConflictDetectionEngine:
    @staticmethod
    def detect_conflicts(
        spec: MasterSpecification,
        bundle: CompiledSchemaBundle,
        changes: ChangeSet
    ) -> ConflictDetectionReport:
        conflicts = []
        c_counter = 1

        for r in changes.removed:
            snake = CanonicalNamingEngine.to_snake_case(r)
            pascal = CanonicalNamingEngine.to_pascal_case(r)

            # 1. Entity Removal Conflict: check foreign keys referencing this table
            for tbl in bundle.database_schema:
                if tbl.table_name != snake:
                    for fk in tbl.foreign_keys:
                        if fk.get("references_table") == snake:
                            conflicts.append(ChangeConflict(
                                conflict_id=f"conf_{c_counter:03d}",
                                conflict_type="ENTITY_REMOVAL",
                                message=f"Entity Removal Conflict: removing '{r}' violates FK constraints in table '{tbl.table_name}'.",
                                severity="HIGH"
                            ))
                            c_counter += 1

            # 2. Workflow Dependency Conflict: check workflows referencing this entity
            for wf in spec.workflows:
                if pascal in wf.dependencies:
                    conflicts.append(ChangeConflict(
                        conflict_id=f"conf_{c_counter:03d}",
                        conflict_type="WORKFLOW_DEPENDENCY",
                        message=f"Workflow Dependency Conflict: removing entity '{r}' breaks active workflow '{wf.workflow_name}'.",
                        severity="HIGH"
                    ))
                    c_counter += 1

                # Actor removal conflict
                if r in wf.actors and len(wf.actors) == 1:
                    conflicts.append(ChangeConflict(
                        conflict_id=f"conf_{c_counter:03d}",
                        conflict_type="WORKFLOW_DEPENDENCY",
                        message=f"Workflow Dependency Conflict: removing actor '{r}' leaves workflow '{wf.workflow_name}' orphaned.",
                        severity="HIGH"
                    ))
                    c_counter += 1

            # 3. Business Rule Conflict: check rules referencing removed entity
            for br in spec.business_rules:
                if hasattr(br, "affected_entities") and pascal in br.affected_entities:
                    conflicts.append(ChangeConflict(
                        conflict_id=f"conf_{c_counter:03d}",
                        conflict_type="BUSINESS_RULE",
                        message=f"Business Rule Conflict: business rule '{br.rule_id}' depends on removed entity '{r}'.",
                        severity="HIGH"
                    ))
                    c_counter += 1

        # 4. Permission Conflict
        for m in changes.modified:
            if m.get("type") == "permission":
                role = m.get("role")
                payload = m.get("details", {})
                new_perms = payload.get("permissions", [])
                
                # Check privilege escalation (e.g. basic user granted DeleteDatabase)
                if role != "Admin" and any(p in ("DeleteDatabase", "OverrideAll") for p in new_perms):
                    conflicts.append(ChangeConflict(
                        conflict_id=f"conf_{c_counter:03d}",
                        conflict_type="PERMISSION",
                        message=f"Permission Conflict: Privilege escalation check failed. Non-admin role '{role}' granted admin permission.",
                        severity="HIGH"
                    ))
                    c_counter += 1

        is_valid = len([c for c in conflicts if c.severity == "HIGH"]) == 0
        return ConflictDetectionReport(is_valid=is_valid, conflicts=conflicts)


# --- 4. COMPLEXITY SCORE CALCULATOR ---

class ChangeComplexityScoreCalculator:
    @staticmethod
    def calculate(dep_graph: ChangeDependencyGraph, changes: ChangeSet) -> Tuple[ChangeImpactScore, ChangeComplexityScore]:
        ent_count = 0
        wf_count = 0
        api_count = 0
        perm_count = 0
        br_count = 0

        # Sum direct/indirect dependencies by component category
        all_deps = dep_graph.direct_dependencies + dep_graph.indirect_dependencies
        for d in all_deps:
            if d.startswith("Table:"):
                ent_count += 1
            elif d.startswith("Workflow:"):
                wf_count += 1
            elif d.startswith("API:"):
                api_count += 1
            elif d.startswith("UI:"):
                pass  # UI changes
            elif d.startswith("Auth:"):
                perm_count += 1

        # Sum actual changes list sizes
        total_changes = len(changes.added) + len(changes.removed) + len(changes.modified)
        
        # Calculate impact score (0 to 100)
        score = (len(all_deps) * 8.0) + (total_changes * 15.0)
        score = min(max(score, 0.0), 100.0)

        # Map to impact level
        if score < 30.0:
            imp_lvl = "LOW"
        elif score < 60.0:
            imp_lvl = "MEDIUM"
        else:
            imp_lvl = "HIGH"

        # Determine complexity rating
        affected_total = len(all_deps) + total_changes
        if affected_total <= 2:
            complexity = "LOW"
        elif affected_total <= 5:
            complexity = "MEDIUM"
        elif affected_total <= 10:
            complexity = "HIGH"
        else:
            complexity = "VERY_HIGH"

        impact_score = ChangeImpactScore(
            entities_changed=ent_count,
            workflows_changed=wf_count,
            apis_changed=api_count,
            permissions_changed=perm_count,
            business_rules_changed=br_count,
            score=score,
            impact_level=imp_lvl
        )
        complexity_score = ChangeComplexityScore(
            score=float(affected_total * 10.0),
            complexity_level=complexity
        )
        return impact_score, complexity_score


# --- 5. CHANGE RISK ASSESSMENT ENGINE ---

class ChangeRiskAssessmentEngine:
    @staticmethod
    def assess(
        dep_graph: ChangeDependencyGraph,
        changes: ChangeSet,
        conflicts: ConflictDetectionReport
    ) -> ChangeRiskAssessment:
        affected_entities = []
        affected_workflows = []
        affected_components = []

        all_deps = dep_graph.direct_dependencies + dep_graph.indirect_dependencies
        for d in all_deps:
            affected_components.append(d)
            if d.startswith("Table:"):
                affected_entities.append(d.split(":")[-1])
            elif d.startswith("Workflow:"):
                affected_workflows.append(d.split(":")[-1])

        # Risk metrics based on depth and conflicts
        validation_risk = 0.1
        repair_risk = 0.1
        simulation_risk = 0.1

        if not conflicts.is_valid:
            validation_risk = 0.90
            repair_risk = 0.85
            simulation_risk = 0.95

        # Check depth impact
        if dep_graph.dependency_depth >= 2:
            validation_risk = max(validation_risk, 0.50)
            simulation_risk = max(simulation_risk, 0.60)

        # Overall risk calculation
        overall = (validation_risk + repair_risk + simulation_risk) / 3.0 * 100.0
        overall = min(max(overall, 0.0), 100.0)

        if overall < 35.0:
            risk_lvl = "LOW"
        elif overall < 70.0:
            risk_lvl = "MEDIUM"
        else:
            risk_lvl = "HIGH"

        return ChangeRiskAssessment(
            risk_level=risk_lvl,
            affected_components=affected_components,
            affected_workflows=affected_workflows,
            affected_entities=affected_entities,
            validation_risk=validation_risk,
            repair_risk=repair_risk,
            simulation_risk=simulation_risk,
            overall_risk_score=overall
        )


# --- 6. CHANGE PROPAGATION ENGINE ---

class ChangePropagationEngine:
    @staticmethod
    def propagate(
        blueprint: ApprovedBlueprint,
        spec: MasterSpecification,
        bundle: CompiledSchemaBundle,
        changes: ChangeSet
    ) -> Tuple[ApprovedBlueprint, MasterSpecification, CompiledSchemaBundle]:
        bp_new = copy.deepcopy(blueprint)
        spec_new = copy.deepcopy(spec)
        bundle_new = copy.deepcopy(bundle)

        # 1. Process REMOVED elements first
        for rem_name in changes.removed:
            snake = CanonicalNamingEngine.to_snake_case(rem_name)
            pascal = CanonicalNamingEngine.to_pascal_case(rem_name)

            # Blueprint
            bp_new.features = [f for f in bp_new.features if f.name != rem_name]
            bp_new.actors = [a for a in bp_new.actors if a.name != rem_name]
            bp_new.workflows = [w for w in bp_new.workflows if w.name != rem_name]
            bp_new.permissions = [p for p in bp_new.permissions if p.actor != rem_name]

            # MasterSpecification
            spec_new.entities = [e for e in spec_new.entities if e.name != pascal]
            spec_new.workflows = [w for w in spec_new.workflows if w.workflow_name != rem_name]
            spec_new.actors = [a for a in spec_new.actors if a.name != pascal]
            spec_new.permissions = [p for p in spec_new.permissions if p.role != pascal]
            spec_new.relationships = [
                r for r in spec_new.relationships
                if r.source_entity != pascal and r.target_entity != pascal
            ]

            # CompiledSchemaBundle
            bundle_new.database_schema = [t for t in bundle_new.database_schema if t.table_name != snake]
            bundle_new.api_schema = [ap for ap in bundle_new.api_schema if ap.source_entity != pascal]
            bundle_new.auth_schema = [au for au in bundle_new.auth_schema if au.role != pascal]
            bundle_new.ui_schema = [ui for ui in bundle_new.ui_schema if ui.view_id != f"view_{snake}"]

        # 2. Process ADDED elements
        for add_item in changes.added:
            itype = add_item.get("type")
            name = add_item.get("name")
            payload = add_item.get("details", {})

            if itype == "feature":
                from stages.stage3_recommend import FeatureExplanation, RecommendationSource
                explanation_payload = payload.get("explanation")
                if not explanation_payload:
                    explanation_payload = FeatureExplanation(
                        feature_name=name,
                        what_it_does=payload.get("description", "Incremental feature"),
                        why_recommended="User change request",
                        business_value="User value",
                        source=RecommendationSource(
                            source_type="user_requirement",
                            source_description="Incremental compiler",
                            relevance_score=1.0
                        ),
                        source_reliability=1.0,
                        recommendation_confidence=1.0,
                        innovation_origin="user_created",
                        relevance_score=1.0
                    )
                rec_feat = RecommendedFeature(
                    name=name,
                    description=payload.get("description", ""),
                    actor_involved=payload.get("actor_involved", "Admin"),
                    explanation=explanation_payload
                )
                bp_new.features.append(rec_feat)
                
                # Incrementally discover and compile entity
                from core.ast import EntityField
                ent_id = f"ent_{CanonicalNamingEngine.to_snake_case(name)}"
                new_ent = EntityDefinition(
                    entity_id=ent_id,
                    entity_name=CanonicalNamingEngine.to_pascal_case(name),
                    name=CanonicalNamingEngine.to_pascal_case(name),
                    description=payload.get("description", "Incremental feature entity"),
                    source="user_requirement",
                    confidence=1.0,
                    fields=[
                        EntityField(name="id", type="string", is_key=True, required=True),
                        EntityField(name="name", type="string", is_key=False, required=True)
                    ]
                )
                spec_new.entities.append(new_ent)
                
                # Append table and endpoints incrementally
                ast_v = spec_new.metadata.get("blueprint_project_id", "v1.0")
                trace = TraceabilityMetadata(source_entity=name, source_ast_version=ast_v, compiler_phase="Incremental Compiler")
                
                new_tbl = DatabaseTableDefinition(
                    table_name=CanonicalNamingEngine.to_snake_case(name),
                    columns=[
                        ColumnDefinition(name="id", type="string", is_primary_key=True, is_nullable=False),
                        ColumnDefinition(name="name", type="string", is_primary_key=False, is_nullable=False)
                    ],
                    primary_keys=["id"],
                    source_entity=CanonicalNamingEngine.to_pascal_case(name),
                    traceability=trace
                )
                bundle_new.database_schema.append(new_tbl)

                # Add REST endpoints
                plural = get_entity_plural_path(name)
                bundle_new.api_schema.append(APIEndpointDefinition(
                    endpoint_id=f"get_{new_tbl.table_name}_list",
                    path=f"/api/v1/{plural}",
                    method="GET",
                    source_entity=new_ent.name,
                    traceability=trace
                ))
                bundle_new.api_schema.append(APIEndpointDefinition(
                    endpoint_id=f"create_{new_tbl.table_name}",
                    path=f"/api/v1/{plural}",
                    method="POST",
                    source_entity=new_ent.name,
                    traceability=trace
                ))

            elif itype == "actor":
                rec_act = RecommendedActor(
                    name=name,
                    description=payload.get("description", ""),
                    relevance_score=1.0,
                    why_needed="User requested"
                )
                bp_new.actors.append(rec_act)
                
                # Add actor to spec
                spec_new.actors.append(Actor(name=name, description=payload.get("description", "")))
                
                # Add AuthRule definition
                ast_v = spec_new.metadata.get("blueprint_project_id", "v1.0")
                trace = TraceabilityMetadata(source_entity=name, source_ast_version=ast_v, compiler_phase="Incremental Compiler")
                bundle_new.auth_schema.append(AuthRuleDefinition(
                    rule_id=f"r_{name.lower()}",
                    role=name,
                    permissions=["ReadOwnProfile"],
                    traceability=trace
                ))

        # 3. Process MODIFIED elements
        for mod_item in changes.modified:
            itype = mod_item.get("type")
            name = mod_item.get("name") or mod_item.get("role") or mod_item.get("rule_id")
            payload = mod_item.get("details", {})

            if itype == "workflow":
                wf_name = name
                new_steps = payload.get("workflow_steps", [])
                
                # Update Spec
                for wf in spec_new.workflows:
                    if wf.workflow_name == wf_name:
                        wf.workflow_steps = new_steps

            elif itype == "permission":
                role = name
                new_perms = payload.get("permissions", [])
                
                # Update Spec
                for perm in spec_new.permissions:
                    if perm.role == role:
                        perm.permissions = new_perms
                        
                # Update Schema auth rules
                for au in bundle_new.auth_schema:
                    if au.role == role:
                        au.permissions = new_perms

            elif itype == "business_rule":
                rule_id = name
                new_rule = payload.get("rule", "")
                
                # Update Spec
                for br in spec_new.business_rules:
                    if br.rule_id == rule_id:
                        br.rule = new_rule

        return bp_new, spec_new, bundle_new


# --- 7. CHANGE SAFETY ENGINE ---

class ChangeSafetyEngine:
    @staticmethod
    def verify_safety(
        bundle_old: CompiledSchemaBundle,
        bundle_new: CompiledSchemaBundle,
        report: ImpactAnalysisReport
    ) -> bool:
        # Check that all components flagged as unaffected are structurally identical
        unaffected = report.unaffected_components
        
        old_tables = {t.table_name: t for t in bundle_old.database_schema}
        new_tables = {t.table_name: t for t in bundle_new.database_schema}
        
        old_apis = {ap.endpoint_id: ap for ap in bundle_old.api_schema}
        new_apis = {ap.endpoint_id: ap for ap in bundle_new.api_schema}

        for u in unaffected:
            comp_type, comp_name = u.split(":")
            if comp_type == "Table":
                if comp_name in old_tables and comp_name in new_tables:
                    # Compare columns structural definition
                    if old_tables[comp_name].columns != new_tables[comp_name].columns:
                        print(f"DEBUG: verify_safety Table mismatch on {comp_name}. Old cols: {old_tables[comp_name].columns}, New cols: {new_tables[comp_name].columns}")
                        return False
            elif comp_type == "API":
                if comp_name in old_apis and comp_name in new_apis:
                    if old_apis[comp_name].path != new_apis[comp_name].path or old_apis[comp_name].method != new_apis[comp_name].method:
                        print(f"DEBUG: verify_safety API mismatch on {comp_name}")
                        return False
        return True


# --- 8. ROLLBACK & TIMELINE PERSISTENCE ---

class EvolutionTimelineManager:
    TIMELINE_PATH = "evolution_timeline.json"

    @classmethod
    def load_timeline(cls) -> EvolutionTimeline:
        if not os.path.exists(cls.TIMELINE_PATH):
            return EvolutionTimeline()
        try:
            with open(cls.TIMELINE_PATH, "r") as f:
                data = json.load(f)
                return EvolutionTimeline(**data)
        except Exception:
            return EvolutionTimeline()

    @classmethod
    def commit_version(cls, entry: EvolutionTimelineEntry):
        timeline = cls.load_timeline()
        timeline.entries.append(entry)
        try:
            with open(cls.TIMELINE_PATH, "w") as f:
                json.dump(timeline.model_dump(), f, indent=4)
        except Exception as e:
            logger.error(f"Timeline save failure: {e}")


# --- 9. REQUIREMENT CHANGE ENGINE ORCHESTRATOR ---

class RequirementChangeEngine:
    @staticmethod
    def apply_change(
        blueprint: ApprovedBlueprint,
        spec: MasterSpecification,
        bundle: CompiledSchemaBundle,
        request: RequirementChangeRequest
    ) -> RequirementChangeReport:
        # 1. Change Detection
        changes = ChangeDetector.detect_changes(blueprint, request)

        # 2. Dependency Analysis
        dep_graph = ChangeDependencyGraphBuilder.build_graph(spec, bundle, changes)

        # 3. Conflict Detection
        conflicts = ConflictDetectionEngine.detect_conflicts(spec, bundle, changes)

        # 4. Complexity & Risk Assessment
        imp_score, complexity = ChangeComplexityScoreCalculator.calculate(dep_graph, changes)
        risk = ChangeRiskAssessmentEngine.assess(dep_graph, changes, conflicts)

        # Prepare Impact Analysis Report
        unaffected = []
        all_deps = dep_graph.direct_dependencies + dep_graph.indirect_dependencies
        for t in bundle.database_schema:
            if f"Table:{t.table_name}" not in all_deps:
                unaffected.append(f"Table:{t.table_name}")
        for ap in bundle.api_schema:
            if f"API:{ap.endpoint_id}" not in all_deps:
                unaffected.append(f"API:{ap.endpoint_id}")

        impact_report = ImpactAnalysisReport(
            affected_components=all_deps,
            unaffected_components=unaffected,
            estimated_effort="Low (Surgical)" if complexity.complexity_level == "LOW" else "Medium (Cascade)",
            impact_score=imp_score,
            dependency_graph=dep_graph
        )

        # 5. Create Transactional Rollback Point
        rollback_pt = RollbackPoint(
            version_id=request.change_id,
            blueprint_snapshot=blueprint.model_dump(),
            specification_snapshot=spec.model_dump(),
            schema_snapshot=bundle.model_dump()
        )

        # Initial default statuses
        rollback_required = False
        val_passed = True
        rep_required = False
        sim_passed = True
        diffs = []

        bp_new, spec_new, bundle_new = blueprint, spec, bundle

        # Revert immediately if CRITICAL conflicts found before propagation
        if not conflicts.is_valid:
            rollback_required = True
            val_passed = False
            sim_passed = False
        else:
            try:
                # 6. Propagation
                bp_new, spec_new, bundle_new = ChangePropagationEngine.propagate(
                    blueprint, spec, bundle, changes
                )

                # Safety check
                safe = ChangeSafetyEngine.verify_safety(bundle, bundle_new, impact_report)
                if not safe:
                    raise Exception("ChangeSafetyCheckFailed: Unintended changes detected in preserved components.")

                # Calculate diffs
                for a in changes.added:
                    diffs.append(ChangeDiff(
                        component=a.get("name") or "unknown",
                        before_state=None,
                        after_state=str(a),
                        change_reason="Add requested"
                    ))
                for r in changes.removed:
                    diffs.append(ChangeDiff(
                        component=r,
                        before_state="Present",
                        after_state=None,
                        change_reason="Remove requested"
                    ))

                # 7. Post-change validation
                val_report = ValidationEngine.validate(bundle_new, spec_new, bp_new)
                if not val_report.is_valid:
                    rep_required = True
                    # Attempt Repair
                    rep_report, bundle_new, spec_new, metrics = RepairEngine.repair(bundle_new, spec_new, bp_new)
                    if not rep_report.revalidation_results.is_valid:
                        raise Exception("PostChangeRepairFailed: Validation remains broken after repair pass.")

                # 8. Post-change simulation
                sim_report = ExecutionSimulator.simulate(bundle_new, spec_new, bp_new)
                if sim_report.failed_steps > 0:
                    failures = [t.reason for t in sim_report.simulation_traces if t.outcome == "FAILED"]
                    raise Exception(f"PostChangeSimulationFailed: Simulation encountered runtime failures. Failures: {failures}")

            except Exception as e:
                logger.error(f"Propagation rollback triggered: {e}")
                rollback_required = True
                val_passed = False
                sim_passed = False
                # Revert to snapshot
                bp_new = blueprint
                spec_new = spec
                bundle_new = bundle

        # 9. Version & Timeline Commit on Success
        parent_v = spec.metadata.get("ast_version_id", "v1.0")
        version_info = RequirementVersion(
            version_id=request.change_id,
            parent_version=parent_v,
            change_summary=request.description
        )

        if not rollback_required:
            spec_new.metadata["ast_version_id"] = request.change_id
            timeline_entry = EvolutionTimelineEntry(
                version_id=request.change_id,
                change_summary=request.description,
                impact_level=imp_score.impact_level,
                risk_level=risk.risk_level,
                timestamp=datetime.now().isoformat(),
                parent_version=parent_v,
                change_id=request.change_id,
                change_type=request.change_type,
                description=request.description
            )
            EvolutionTimelineManager.commit_version(timeline_entry)

        effectiveness = ChangeEffectivenessReport(
            components_modified=[a.get("name") or "unknown" for a in changes.added + changes.modified],
            components_preserved=unaffected,
            validation_passed=val_passed,
            repair_required=rep_required,
            simulation_passed=sim_passed,
            rollback_required=rollback_required,
            risk_level=risk.risk_level,
            impact_level=imp_score.impact_level,
            complexity_level=complexity.complexity_level
        )

        return RequirementChangeReport(
            change_id=request.change_id,
            version_info=version_info,
            diffs=diffs,
            impact_report=impact_report,
            risk_assessment=risk,
            effectiveness=effectiveness,
            conflicts_report=conflicts,
            updated_blueprint=bp_new if not rollback_required else None,
            updated_spec=spec_new if not rollback_required else None,
            updated_bundle=bundle_new if not rollback_required else None
        )
