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
    EntityDefinition, BusinessRuleDefinition
)
from stages.stage5_schema import (
    CompiledSchemaBundleBuilder, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, TraceabilityMetadata,
    CompilationArtifact
)
from stages.stage6_validate import ValidationEngine, ValidationError, ValidationReport
from core.ast import Actor, Entity, EntityField, BusinessRule


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


# --- 5 DOMAINS VALIDATION TESTS ---

def test_gym_validation_clean(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.critical_count == 0
    assert report.high_count == 0


def test_crm_validation_clean():
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
    report = ValidationEngine.validate(bundle, spec, bp)
    assert report.is_valid is True


def test_hospital_validation_clean():
    rec_doc = RecommendedActor(name="Doctor", description="Practitioner", relevance_score=1.0, why_needed="Treat patients")
    rec_patient = RecommendedActor(name="Patient", description="Patient profile", relevance_score=1.0, why_needed="Schedule appointments")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="AppointmentScheduling", what_it_does="Schedule", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="AppointmentScheduling", description="Manage appointments", actor_involved="Doctor", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="AppointmentSchedulingFlow", description="Schedule appt", steps=["Request", "Book"], actor_involved="Patient", why_needed="Access flow"
    )
    bp = ApprovedBlueprint(
        project_id="test_hospital_project",
        app_type="Hospital",
        actors=[rec_doc, rec_patient],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    report = ValidationEngine.validate(bundle, spec, bp)
    assert report.is_valid is True


def test_school_validation_clean():
    rec_student = RecommendedActor(name="Student", description="Student profile", relevance_score=1.0, why_needed="Learn")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="CourseEnrollment", what_it_does="Enroll", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="CourseEnrollment", description="Enroll in courses", actor_involved="Student", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="CourseEnrollmentFlow", description="Enroll workflow", steps=["Choose", "Add"], actor_involved="Student", why_needed="Course flow"
    )
    bp = ApprovedBlueprint(
        project_id="test_school_project",
        app_type="School",
        actors=[rec_student],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    report = ValidationEngine.validate(bundle, spec, bp)
    assert report.is_valid is True


def test_inventory_validation_clean():
    rec_staff = RecommendedActor(name="WarehouseStaff", description="Staff profile", relevance_score=1.0, why_needed="Manage goods")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="ReceiveStock", what_it_does="Stock", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="ReceiveStock", description="Stock levels management", actor_involved="WarehouseStaff", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="ReceiveStockFlow", description="Receive stock run", steps=["Arrive", "Unload"], actor_involved="WarehouseStaff", why_needed="Inventory flow"
    )
    bp = ApprovedBlueprint(
        project_id="test_inventory_project",
        app_type="Inventory",
        actors=[rec_staff],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    report = ValidationEngine.validate(bundle, spec, bp)
    assert report.is_valid is True


# --- VALIDATION DIAGNOSTIC EDGE CASES ---

def test_validation_missing_primary_key(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Strip primary keys from the Member table
    for tbl in bundle.database_schema:
        if tbl.table_name == "member":
            tbl.primary_keys = []
            
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "DB_MISSING_PK" for e in report.errors)


def test_validation_api_unknown_entity(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Point one endpoint to an unknown entity
    bundle.api_schema[0].source_entity = "GhostEntity"
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "API_UNKNOWN_ENTITY" for e in report.errors)


def test_validation_ui_broken_endpoint(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Force UI view to link to a broken route path
    bundle.ui_schema[0].linked_endpoints = ["POST /api/v1/ghost_route_path"]
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "UI_BROKEN_ENDPOINT" for e in report.errors)


def test_validation_workflow_circular_dep(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Inject circular dependency between workflows in MasterSpecification spec
    spec.workflows = [
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
    ]
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "WORKFLOW_CIRCULAR_DEP" for e in report.errors)


def test_validation_missing_traceability_artifact(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Strip artifacts registry to trigger traceability validation failures
    bundle.artifacts = []
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "TRACEABILITY_MISSING_ARTIFACT" for e in report.errors)


def test_validation_contract_broken_reference(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Map a contract to point to a non-existent database table 'ghost_table'
    bundle.contracts[0].generated_components.append("DB_Table:ghost_table")
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "CONTRACT_INVALID_REF" for e in report.errors)


def test_validation_db_duplicate_table(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Duplicate table definition entry in schema database
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
    
    report = ValidationEngine.validate(bundle, spec, gym_approved_blueprint)
    assert report.is_valid is False
    assert any(e.error_code == "DB_DUPLICATE_TABLE" for e in report.errors)
