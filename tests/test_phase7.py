import pytest
from datetime import datetime

from stages.stage2_intent import IntentExtractionResult, IntentActor, IntentFeature
from stages.stage3_recommend import (
    BlueprintRecommendation, RecommendedActor, RecommendedFeature, FeatureExplanation,
    RecommendationSource, RecommendedWorkflow, RecommendedPermission, RecommendedInnovation, ApprovedBlueprint
)
from stages.stage4_system import (
    MasterSpecificationBuilder, RelationshipDefinition, WorkflowDefinition,
    PermissionDefinition, DesignDecision, SystemDesignGraph, MasterSpecification,
    EntityDefinition, BusinessRuleDefinition, Actor
)
from stages.stage5_schema import (
    CompiledSchemaBundleBuilder, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, TraceabilityMetadata,
    CompilationArtifact, ColumnDefinition
)
from stages.stage6_validate import ValidationEngine, ValidationError, ValidationReport
from stages.stage7_repair import (
    RepairEngine, RepairStrategyLibrary, RepairCandidate, RepairAction, RepairReport,
    RepairEffectivenessMetrics, RepairHistory, RepairType
)


@pytest.fixture
def gym_approved_blueprint() -> ApprovedBlueprint:
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
    
    return ApprovedBlueprint(
        project_id="test_gym_project",
        app_type="Gym",
        actors=[rec_member, rec_admin],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[rec_perm],
        innovations=[]
    )


# --- 13+ UNIQUE ERROR CLASSES REPAIR TESTS ---

# 1. DB_MISSING_PK
def test_repair_db_missing_pk(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Strip primary key from table
    for tbl in bundle.database_schema:
        if tbl.table_name == "member":
            tbl.primary_keys = []
            
    # Verify validation fails
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert any(e.error_code == "DB_MISSING_PK" for e in report.errors)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    
    # Verify repaired and passes revalidation
    assert metrics.reduction_percentage == 100.0
    assert metrics.successful_repairs >= 1
    assert RepairedSchemaBundle.compilation_report.is_valid is True
    assert ValidationEngine.validate(RepairedSchemaBundle, RepairedSpec, gym_approved_blueprint).is_valid is True


# 2. DB_BROKEN_RELATIONSHIP
def test_repair_db_broken_relationship(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    
    # Ensure a relationship exists targeting Trainer entity (which exists by default in Gym Spec)
    spec.relationships = [
        RelationshipDefinition(
            relationship_id="rel_member_trainer",
            source_entity="Member",
            target_entity="Trainer",
            relationship_type="many-to-one",
            description="Member has assigned trainer"
        )
    ]
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Remove the relationship foreign key from member table
    for tbl in bundle.database_schema:
        if tbl.table_name == "member":
            tbl.columns = [c for c in tbl.columns if c.name != "trainer_id"]
            tbl.foreign_keys = [fk for fk in tbl.foreign_keys if fk.get("column") != "trainer_id"]
            
    # Validate & Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    
    # Verify success
    assert metrics.successful_repairs >= 1
    assert ValidationEngine.validate(RepairedSchemaBundle, RepairedSpec, gym_approved_blueprint).is_valid is True


# 3. DB_DUPLICATE_TABLE
def test_repair_db_duplicate_table(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Duplicate member table
    dup_table = DatabaseTableDefinition(
        table_name="member",
        columns=bundle.database_schema[0].columns,
        primary_keys=bundle.database_schema[0].primary_keys,
        foreign_keys=bundle.database_schema[0].foreign_keys,
        constraints=bundle.database_schema[0].constraints,
        indexes=bundle.database_schema[0].indexes,
        source_entity="Member",
        traceability=bundle.database_schema[0].traceability
    )
    bundle.database_schema.append(dup_table)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    
    # Verify deduplicated
    assert metrics.successful_repairs == 1
    table_names = [t.table_name for t in RepairedSchemaBundle.database_schema]
    assert table_names.count("member") == 1
    assert ValidationEngine.validate(RepairedSchemaBundle, RepairedSpec, gym_approved_blueprint).is_valid is True


# 4. API_DUPLICATE_ENDPOINT
def test_repair_api_duplicate_endpoint(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Duplicate API endpoint
    dup_ep = bundle.api_schema[0].model_copy()
    bundle.api_schema.append(dup_ep)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert len(RepairedSchemaBundle.api_schema) == len(bundle.api_schema) - 1


# 5. API_UNKNOWN_ENTITY
def test_repair_api_unknown_entity(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Unknown entity name
    bundle.api_schema[0].source_entity = "GhostEntity"
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert RepairedSchemaBundle.api_schema[0].source_entity != "GhostEntity"


# 6. API_INVALID_ROLE
def test_repair_api_invalid_role(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Invalid role in endpoint permission
    bundle.api_schema[0].permissions.append("GhostRole")
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert "GhostRole" not in RepairedSchemaBundle.api_schema[0].permissions


# 7. UI_DUPLICATE_VIEW
def test_repair_ui_duplicate_view(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Duplicate view definition
    dup_view = bundle.ui_schema[0].model_copy()
    bundle.ui_schema.append(dup_view)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert len(RepairedSchemaBundle.ui_schema) == len(bundle.ui_schema) - 1


# 8. UI_BROKEN_ENDPOINT
def test_repair_ui_broken_endpoint(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Broken UI link
    bundle.ui_schema[0].linked_endpoints.append("POST /api/v1/ghost_route_path")
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs >= 1
    # Check that a new endpoint was compiled for `/api/v1/ghost_route_path`
    api_paths = {a.path for a in RepairedSchemaBundle.api_schema}
    assert "/api/v1/ghost_route_path" in api_paths


# 9. UI_INVALID_ROLE
def test_repair_ui_invalid_role(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Invalid role requirement in UI view permissions
    bundle.ui_schema[0].required_permissions.append("GhostRole")
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert "GhostRole" not in RepairedSchemaBundle.ui_schema[0].required_permissions


# 10. AUTH_DUPLICATE_ROLE
def test_repair_auth_duplicate_role(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Duplicate Auth rule
    dup_auth = bundle.auth_schema[0].model_copy()
    bundle.auth_schema.append(dup_auth)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert len(RepairedSchemaBundle.auth_schema) == len(bundle.auth_schema) - 1


# 11. AUTH_INVALID_ROLE
def test_repair_auth_invalid_role(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Auth rule for non-existent role
    invalid_auth = AuthRuleDefinition(
        role="GhostRole",
        permissions=["ReadSecret"],
        restricted_actions=[],
        authentication_requirements=["JWT"],
        traceability=bundle.auth_schema[0].traceability
    )
    bundle.auth_schema.append(invalid_auth)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs >= 1
    assert not any(au.role == "GhostRole" for au in RepairedSchemaBundle.auth_schema)


# 12. WORKFLOW_MISSING_ACTOR
def test_repair_workflow_missing_actor(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Workflow references a non-existent actor 'Patient'
    spec.workflows[0].actors.append("Patient")
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    # Check that 'Patient' actor was appended to spec actors list
    actor_names = {a.name for a in RepairedSpec.actors}
    assert "Patient" in actor_names


# 13. WORKFLOW_CIRCULAR_DEP
def test_repair_workflow_circular_dep(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    
    # Inject: Circular dependencies between workflows
    spec.workflows.extend([
        WorkflowDefinition(
            workflow_id="wf_a",
            workflow_name="WorkflowA",
            workflow_dependencies=["workflowb"],
            criticality="HIGH"
        ),
        WorkflowDefinition(
            workflow_id="wf_b",
            workflow_name="WorkflowB",
            workflow_dependencies=["workflowa"],
            criticality="HIGH"
        )
    ])
    # Compile bundle AFTER updating spec workflows list
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs >= 1
    assert ValidationEngine.validate(RepairedSchemaBundle, RepairedSpec, gym_approved_blueprint).is_valid is True


# 14. TRACEABILITY_MISSING_ARTIFACT
def test_repair_traceability_missing_artifact(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Clear compilation artifacts
    bundle.artifacts = []
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs >= 1
    assert len(RepairedSchemaBundle.artifacts) > 0


# 15. CONTRACT_INVALID_REF
def test_repair_contract_invalid_ref(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Broken component reference inside schema contracts
    bundle.contracts[0].generated_components.append("DB_Table:ghost_table")
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    assert "DB_Table:ghost_table" not in RepairedSchemaBundle.contracts[0].generated_components


# 16. REQUIRED_FIELD_MISMATCH
def test_repair_required_field_mismatch(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: DB column is not-nullable, but is missing in API request properties dictionary
    # E.g. Member table has a non-nullable 'email' field, but create_member API endpoint lacks it
    for tbl in bundle.database_schema:
        if tbl.table_name == "member":
            tbl.columns.append(ColumnDefinition(
                name="email",
                type="string",
                is_nullable=False,
                is_primary_key=False
            ))
            
    for ap in bundle.api_schema:
        if ap.endpoint_id == "create_member":
            ap.request_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            
    # Verify validation fails
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert any(e.error_code == "REQUIRED_FIELD_MISMATCH" for e in report.errors)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs >= 1
    
    # Check that 'email' was appended to the API create_member request properties
    create_ep = next((a for a in RepairedSchemaBundle.api_schema if a.endpoint_id == "create_member"), None)
    assert create_ep is not None
    assert "email" in create_ep.request_schema["properties"]


# 17. WORKFLOW_MISSING_STEP
def test_repair_workflow_missing_step(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    
    # Inject: Workflow named 'Registration Flow' has steps but is missing 'Verification Step'
    spec.workflows.append(WorkflowDefinition(
        workflow_id="wf_reg",
        workflow_name="Registration Flow",
        workflow_steps=["Registration", "Account Created"],
        actors=["GymMember"],
        dependencies=["Member"],
        criticality="HIGH"
    ))
    # Compile bundle AFTER updating spec workflows list
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Verify validation fails
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert any(e.error_code == "WORKFLOW_MISSING_STEP" for e in report.errors)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs >= 1
    
    # Check that 'Verification Step' was appended to workflow steps
    wf_reg = next((w for w in RepairedSpec.workflows if w.workflow_name == "Registration Flow"), None)
    assert wf_reg is not None
    assert "Verification Step" in wf_reg.workflow_steps


# 18. COVERAGE_LOSS
def test_repair_coverage_loss(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject: Add a new approved feature in blueprint, but it is not compiled anywhere in schemas
    gym_approved_blueprint.features.append(RecommendedFeature(
        name="Notifications",
        description="Notify class changes",
        actor_involved="GymMember",
        explanation=gym_approved_blueprint.features[0].explanation
    ))
    
    # Verify validation fails
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert any(e.error_code == "COVERAGE_LOSS" for e in report.errors)
    
    # Repair
    rep_report, RepairedSchemaBundle, RepairedSpec, metrics = RepairEngine.repair(bundle, spec, gym_approved_blueprint)
    assert metrics.successful_repairs == 1
    
    # Check that a notifications table is constructed in db schema
    table_names = {t.table_name for t in RepairedSchemaBundle.database_schema}
    assert "notifications" in table_names


# --- INTEGRATION TEST MULTIPLE DOMAINS & SIMULTANEOUS ERRORS ---

def test_crm_simultaneous_repairs():
    rec_agent = RecommendedActor(name="SalesAgent", description="Sales agent", relevance_score=1.0, why_needed="Track leads")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="LeadTracking", what_it_does="Track lead", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="LeadTracking", description="Sales funnel lead tracking", actor_involved="SalesAgent", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="LeadConversionFlow", description="Convert lead", steps=["Qualify", "Convert"], actor_involved="SalesAgent", why_needed="Funnel flow"
    )
    bp = ApprovedBlueprint(
        project_id="test_crm_project",
        app_type="CRM",
        actors=[rec_agent],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject multiple errors simultaneously
    # 1. Strip PK from Lead table
    for tbl in bundle.database_schema:
        if tbl.table_name == "lead":
            tbl.primary_keys = []
            
    # 2. Add invalid Auth rule
    invalid_auth = AuthRuleDefinition(
        role="GhostAgent",
        permissions=["ReadSecret"],
        restricted_actions=[],
        authentication_requirements=["JWT"],
        traceability=bundle.auth_schema[0].traceability
    )
    bundle.auth_schema.append(invalid_auth)
    
    # 3. Add broken view permission
    bundle.ui_schema[0].required_permissions.append("GhostRole")
    
    # Run Repair Engine
    report, repaired_bundle, repaired_spec, metrics = RepairEngine.repair(bundle, spec, bp)
    
    # Assert metrics and success
    assert metrics.before_error_count == 5
    assert metrics.after_error_count == 0
    assert metrics.reduction_percentage == 100.0
    assert metrics.successful_repairs == 5
    assert ValidationEngine.validate(repaired_bundle, repaired_spec, bp).is_valid is True
